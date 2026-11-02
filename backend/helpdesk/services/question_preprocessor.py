"""
Question language detection from the question text (not the browser locale).

The detected language decides the answer language and whether a question is also
searched in English. Questions are not spell-corrected: a general dictionary does not
know the domain vocabulary and rewrote correct words ("métadonnées" -> "étalonnées",
"real-time" -> "mealtime"), and the rewritten text was what got searched and stored.
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
# a non-English answer.
MIN_DETECTION_WORDS = 3
MIN_DETECTION_CONFIDENCE = 0.90

# Full name for every language code langdetect's model can output (55 langs).
# An LLM can answer in any of these languages.
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


def _looks_like_schema_identifier(word: str) -> bool:
    """
    Check if a word looks like a schema/class-name identifier (for language
    detection input), as opposed to just an ordinary capitalized word (e.g.
    the first word of a sentence): stripping every capitalized word would drop
    the sentence-initial word of every question, leaving too little text for
    reliable language detection.
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
