"""
Question preprocessing: spell-check and normalization before RAG.

Implements hybrid approach:
1. Detect question language from text (not browser locale!)
2. Fast library-based spell-check for 14 supported languages (50-100ms)
3. Skip spell-check if confidence is low or language mismatches

Supported languages: English, Norwegian, Spanish, French, German, Dutch,
Portuguese, Italian, Russian, Ukrainian, Polish, Turkish, Czech, Danish, Swedish
"""

import logging
import re
from typing import Optional

from langdetect import DetectorFactory, detect_langs, LangDetectException

logger = logging.getLogger(__name__)

# langdetect is randomized by default; seed it so the same question always
# detects as the same language.
DetectorFactory.seed = 0

# Once schema identifiers are stripped, a short question leaves only a few
# words, and langdetect's guess on those is little better than noise
# ("Does SIRI-PT exist?" -> "Does exist?" -> French at 1.0). Below these
# thresholds the language is treated as undetected, so callers do not force
# a non-English answer or spell-check with the wrong dictionary.
MIN_DETECTION_WORDS = 3
MIN_DETECTION_CONFIDENCE = 0.90

# Languages supported by pyspellchecker (with local dictionaries)
SPELLCHECKER_SUPPORTED_LANGS = {
    "English": "en",
    "Norwegian": "no",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Dutch": "nl",
    "Portuguese": "pt",
    "Italian": "it",
    "Russian": "ru",
    "Ukrainian": "uk",
    "Polish": "pl",
    "Turkish": "tr",
    "Czech": "cs",
    "Danish": "da",
    "Swedish": "sv",
}

# Map langdetect language codes to spellchecker language names
LANGDETECT_TO_SPELLCHECKER = {
    "en": "English",
    "no": "Norwegian",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "nl": "Dutch",
    "pt": "Portuguese",
    "it": "Italian",
    "ru": "Russian",
    "uk": "Ukrainian",
    "pl": "Polish",
    "tr": "Turkish",
    "cs": "Czech",
    "da": "Danish",
    "sv": "Swedish",
}

# Full name for every language code langdetect's model can output (55 langs).
# Broader than LANGDETECT_TO_SPELLCHECKER on purpose: an LLM can answer in any
# of these languages even though pyspellchecker only ships local dictionaries
# for the subset above. Used for answer-language detection, not spell-check.
LANGDETECT_LANGUAGE_NAMES = {
    "af": "Afrikaans", "ar": "Arabic", "bg": "Bulgarian", "bn": "Bengali",
    "ca": "Catalan", "cs": "Czech", "cy": "Welsh", "da": "Danish", "de": "German",
    "el": "Greek", "en": "English", "es": "Spanish", "et": "Estonian",
    "fa": "Persian", "fi": "Finnish", "fr": "French", "gu": "Gujarati",
    "he": "Hebrew", "hi": "Hindi", "hr": "Croatian", "hu": "Hungarian",
    "id": "Indonesian", "it": "Italian", "ja": "Japanese", "kn": "Kannada",
    "ko": "Korean", "lt": "Lithuanian", "lv": "Latvian", "mk": "Macedonian",
    "ml": "Malayalam", "mr": "Marathi", "ne": "Nepali", "nl": "Dutch",
    "no": "Norwegian", "pa": "Punjabi", "pl": "Polish", "pt": "Portuguese",
    "ro": "Romanian", "ru": "Russian", "sk": "Slovak", "sl": "Slovenian",
    "so": "Somali", "sq": "Albanian", "sv": "Swedish", "sw": "Swahili",
    "ta": "Tamil", "te": "Telugu", "th": "Thai", "tl": "Tagalog", "tr": "Turkish",
    "uk": "Ukrainian", "ur": "Urdu", "vi": "Vietnamese",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
}

# Technical terms to skip (XML tags, class names, standards)
TECHNICAL_PATTERNS = {
    # NeTEx/SIRI/OpRa class names
    "ServiceJourney", "DatedServiceJourney", "ScheduledStopPoint", "StopPlace",
    "JourneyPattern", "ServiceCalendar", "RouteLink", "TimingLink",
    "OperatingDay", "OperatingPeriod", "VehicleJourney", "DayType",
    "AccessibilityLimitation", "SiteConnection", "TariffZone",
    # Common acronyms
    "NeTEx", "SIRI", "OpRa", "XML", "JSON", "URI", "URL", "API",
    "UTC", "ISO", "GTFS", "OSM", "WGS84",
}


def _is_technical_term(word: str) -> bool:
    """Check if word is a technical term to skip spell-checking."""
    # Strip punctuation
    clean_word = word.strip(".,;:!?\"'")

    # Exact match or contains as part of camelCase
    if clean_word in TECHNICAL_PATTERNS:
        return True

    # CamelCase or UPPERCASE acronyms
    if clean_word and (clean_word[0].isupper() or clean_word.isupper()):
        return True

    # XML tags
    if clean_word.startswith("<") or clean_word.endswith(">"):
        return True

    # Underscore-separated identifiers
    if "_" in clean_word:
        return True

    return False


def _correct_with_library(question: str, language: str) -> Optional[str]:
    """
    Fast spell-check using local pyspellchecker library.
    Returns corrected question or None if language not supported.
    """
    try:
        from spellchecker import SpellChecker
    except ImportError:
        logger.warning("pyspellchecker not installed, skipping library-based correction")
        return None

    if language not in SPELLCHECKER_SUPPORTED_LANGS:
        return None

    lang_code = SPELLCHECKER_SUPPORTED_LANGS[language]
    try:
        spell = SpellChecker(language=lang_code)
    except Exception as e:
        logger.warning(f"Failed to load spell-checker for {language}: {e}")
        return None

    words = question.split()
    corrected = []
    has_changes = False

    for word in words:
        if _is_technical_term(word):
            # Keep technical terms unchanged
            corrected.append(word)
        else:
            # Check and correct misspelled words
            clean_word = word.strip(".,;:!?\"'")
            if clean_word.lower() not in spell:
                correction = spell.correction(clean_word)
                if correction and correction != clean_word:
                    # Preserve original casing for proper nouns
                    if clean_word[0].isupper():
                        correction = correction.capitalize()
                    corrected.append(word.replace(clean_word, correction))
                    has_changes = True
                else:
                    corrected.append(word)
            else:
                corrected.append(word)

    return " ".join(corrected) if has_changes else None


def _looks_like_schema_identifier(word: str) -> bool:
    """
    Check if a word looks like a schema/class-name identifier (for language
    detection input), as opposed to just an ordinary capitalized word (e.g.
    the first word of a sentence). Deliberately stricter than
    _is_technical_term: that function treats *any* capitalized word as
    skip-worthy, which is fine for spell-check (don't "fix" proper nouns) but
    would strip the sentence-initial word of every question here, leaving too
    little text for reliable language detection.
    """
    clean_word = word.strip(".,;:!?\"'<>")
    if not clean_word:
        return False
    if clean_word in TECHNICAL_PATTERNS:
        return True
    # CamelCase/PascalCase: a lowercase letter followed by an uppercase letter
    # somewhere in the word, e.g. "DatedServiceJourney", "StopPlace".
    if any(prev.islower() and curr.isupper() for prev, curr in zip(clean_word, clean_word[1:])):
        return True
    # Fully uppercase multi-letter acronyms, e.g. "XML", "SIRI".
    if clean_word.isupper() and len(clean_word) > 1:
        return True
    if "_" in clean_word:
        return True
    return False


def _strip_technical_terms(question: str) -> str:
    """Remove schema/class-name tokens that skew language detection toward English."""
    return " ".join(word for word in question.split() if not _looks_like_schema_identifier(word))


def _detect_question_language(question: str) -> Optional[str]:
    """
    Detect the actual language of the question text using langdetect.
    Returns language name (e.g., "Norwegian") or None if detection fails or
    there is too little natural-language text to detect reliably.
    """
    # CamelCase technical terms (e.g. "DatedServiceJourney") read as English
    # tokens to langdetect and can dominate the signal in short questions,
    # so strip them before detecting the natural-language portion.
    stripped = _strip_technical_terms(question)
    word_count = len(re.findall(r"[^\W\d_]+", stripped))
    if word_count < MIN_DETECTION_WORDS:
        logger.debug(f"Too few words ({word_count}) to detect question language: {stripped!r}")
        return None
    try:
        # langdetect returns list of LangDetect objects with probabilities
        detections = detect_langs(stripped)
        if detections:
            detected_code = detections[0].lang  # Best match
            detected_name = LANGDETECT_LANGUAGE_NAMES.get(detected_code)
            confidence = detections[0].prob
            if detected_name and confidence >= MIN_DETECTION_CONFIDENCE:
                logger.debug(f"Detected question language: {detected_name} (code={detected_code}, confidence={confidence:.2f})")
                return detected_name
            logger.debug(f"Low-confidence language detection ignored: code={detected_code}, confidence={confidence:.2f}")
    except LangDetectException as e:
        logger.debug(f"Language detection failed: {e}")

    return None


def detect_question_language(question: str) -> Optional[str]:
    """Public wrapper: detect a question's language from its text (not browser locale)."""
    return _detect_question_language(question)


def _correct_with_llm(question: str, language: str) -> Optional[str]:
    """
    LLM-based spell correction for unsupported languages (optional, not yet implemented).
    Returns None if LLM service not available.
    """
    # TODO: Implement LLM-based spell-check when a general LLM service layer is available
    # For now, library-based approach covers 14 languages and handles most cases
    return None


def preprocess_question(question: str, language: str) -> str:
    """
    Preprocess question: spell-check before RAG retrieval.

    Strategy:
    1. Detect actual question language from text (not browser locale!)
    2. Only apply spell-check if detected language matches spellchecker support
    3. Skip spell-check if detection fails or confidence is low

    Args:
        question: Raw user question
        language: Browser locale language (unreliable, used as fallback only)

    Returns:
        Corrected question (or original if correction fails/unnecessary)
    """
    # Detect the actual language of the question from its text
    detected_language = _detect_question_language(question)

    if detected_language and detected_language in SPELLCHECKER_SUPPORTED_LANGS:
        # Use detected language for spell-checking, not browser locale
        corrected = _correct_with_library(question, detected_language)
        if corrected:
            logger.info(f"Spell-check [{detected_language}]: '{question}' → '{corrected}'")
            return corrected
    elif detected_language:
        # Language detected but not supported by spellchecker
        logger.debug(f"Detected language {detected_language} not supported for spell-check")
    else:
        # Language detection failed; skip spell-check to avoid mangling
        logger.debug(f"Could not detect question language; skipping spell-check")

    return question
