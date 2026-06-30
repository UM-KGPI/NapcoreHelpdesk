"""
Question preprocessing: spell-check and normalization before RAG.

Implements hybrid approach:
1. Fast library-based spell-check for 14 supported languages (50-100ms)
2. LLM-based fallback for unsupported languages (500-800ms, optional)

Supported languages: English, Norwegian, Spanish, French, German, Dutch,
Portuguese, Italian, Russian, Ukrainian, Polish, Turkish, Czech, Danish, Swedish
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

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

    Hybrid approach:
    1. Fast library-based spell-check for 14 supported languages (50-100ms)
    2. LLM fallback for unsupported languages (optional, not yet implemented)

    Args:
        question: Raw user question
        language: Language name (e.g., "Norwegian", "English")

    Returns:
        Corrected question (or original if correction fails/unnecessary)
    """
    # Try fast library-based correction first (covers 14 languages)
    corrected = _correct_with_library(question, language)
    if corrected:
        logger.info(f"Spell-check: '{question}' → '{corrected}'")
        return corrected

    # TODO: LLM fallback for unsupported languages (Slovenian, etc.)
    # Would add ~500-800ms latency for those cases
    return question
