"""
Text normalization utilities for FAQ matching and deduplication.

Canonical normalization (lowercasing, whitespace collapse, punctuation
stripping) makes matching robust to minor surface variations in how the
same question is phrased across repeated asks.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-05-18  |  Modified: 2026-06-28
"""

from __future__ import annotations

import re

# Each rule is a (suffix_to_strip, replacement) pair, ordered longest-first so
# the most specific suffix is matched before shorter overlapping ones.
# The replacement is appended after removing the suffix, allowing "-les" → "-le"
# style rules that preserve the stem's trailing "e".
_STEM_RULES: tuple[tuple[str, str], ...] = (
    ("ations", ""),   # validations → valid
    ("ation",  ""),   # validation  → valid
    ("ating",  ""),   # validating  → valid
    ("ated",   ""),   # validated   → valid
    ("ates",   ""),   # validates   → valid
    ("ators",  ""),   # validators  → valid
    ("ator",   ""),   # validator   → valid
    ("tions",  ""),   # transitions → transit
    ("tion",   ""),   # transition  → transit
    ("ings",   ""),   # publishings → publish (rare but consistent)
    ("ing",    ""),   # publishing  → publish
    ("ions",   ""),   # discussions → discuss
    ("ion",    ""),   # discussion  → discuss
    ("ities",  ""),   # capabilities → capabilit
    ("ity",    ""),   # capability  → capabilit
    ("ness",   ""),   # correctness → correct
    ("ment",   ""),   # requirement → requir
    ("edly",   ""),   # markedly    → mark
    ("bles",   "ble"),# variables   → variable (not "variabl")
    ("les",    "le"), # timetables  → timetable (not "timetabl")
    ("ples",   "ple"),# examples    → example
    ("ers",    ""),   # publishers  → publish
    ("er",     ""),   # publisher   → publish
    ("ied",    ""),   # specified   → specif
    ("ies",    ""),   # entries     → entr
    ("ate",    ""),   # validate    → valid, generate → generat
    ("ly",     ""),   # directly    → direct
    ("ed",     ""),   # published   → publish
    ("es",     ""),   # boxes       → box
    ("s",      ""),   # schemas     → schema
)

# Minimum characters that must remain in the stem after transformation.
# Prevents over-stemming short words.
_MIN_STEM_LENGTH = 4

# Word-boundary tokenizer: alphanumeric sequences starting with a letter.
# Using explicit character classes rather than \b so behaviour is identical
# across Python versions and does not depend on Unicode word boundaries.
_WORD_RE = re.compile(r"[a-z][a-z0-9]*")


def stem_token(word: str) -> str:
    """Strip the longest matching common English suffix.

    Keeps stems at least *_MIN_STEM_LENGTH* characters to avoid over-stemming.
    The input is lowercased before processing so callers need not normalise.

    Examples::

        stem_token("validation")  # → "valid"
        stem_token("validating")  # → "valid"
        stem_token("validate")    # → "valid"
        stem_token("timetables")  # → "timetable"
        stem_token("timetable")   # → "timetable"  (no rule fires)
        stem_token("netex")       # → "netex"       (no rule fires)
        stem_token("publishing")  # → "publish"
    """
    w = word.lower()
    for suffix, replacement in _STEM_RULES:
        candidate_len = len(w) - len(suffix) + len(replacement)
        if w.endswith(suffix) and candidate_len >= _MIN_STEM_LENGTH:
            return w[: len(w) - len(suffix)] + replacement
    return w


def question_word_stems(text: str) -> frozenset[str]:
    """Return a frozenset of stemmed words extracted from *text*.

    Uses word-boundary tokenization (``_WORD_RE``) rather than a substring
    search, so a short token such as ``"time"`` does NOT match inside the
    compound word ``"timetable"``.
    """
    return frozenset(stem_token(w) for w in _WORD_RE.findall(text.lower()))
