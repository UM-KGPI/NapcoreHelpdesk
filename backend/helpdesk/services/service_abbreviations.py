"""Service abbreviations such as SIRI-CA or SIRI-VM, read from the standards' own READMEs.

A question that names a service only by its abbreviation ("overlaps between
SIRI-CA and SIRI-VM") matched no concept and no file, so retrieval fell back to
generic files and the answer guessed what the letters stand for. The SIRI README
lists every service as "Control Actions (SIRI-CA)"; the indexed README chunks are
read for such pairs, and each service is linked to its indexed *_service.xsd by
the first letters of each word of its name ("Control Actions" ->
siri_controlAction_service.xsd), which also tolerates small spelling slips in the
README. Nothing is hand-written: a new service in a README is picked up the next
time the index is read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from helpdesk.models import SourceChunk

# "Control Actions (SIRI-CA)": a capitalised name of one to five words, then the
# abbreviation in parentheses: the standard's name, a hyphen, two to four capitals.
_NAME_ABBREVIATION = re.compile(r"\b([A-Z][A-Za-z]+(?: [A-Za-z]+){0,4}) \(([A-Z][A-Za-z]{1,9}-[A-Z]{2,4})\)")
_SERVICE_SCHEMA = re.compile(r"(?:^|/)[a-z]+_([A-Za-z]+)_service\.xsd$")
_WORD_PREFIX = 5


@dataclass(frozen=True)
class Service:
    abbreviation: str
    name: str
    schema_paths: tuple[str, ...]


def _word_stems(name: str) -> list[str]:
    stems = []
    for word in name.lower().split():
        if word.endswith("s") and len(word) > _WORD_PREFIX:
            word = word[:-1]
        stems.append(word[:_WORD_PREFIX])
    return stems


def _schema_matches(name: str, schema_stem: str) -> bool:
    """True when the schema stem starts each word of the name in order:
    "Vehicle Monitoring" and "vehiclemonitoring"."""
    position = 0
    for stem in _word_stems(name):
        found = schema_stem.find(stem, position)
        if found < 0:
            return False
        position = found + len(stem)
    return True


def build_services(readme_texts: list[str], indexed_paths: list[str]) -> dict[str, Service]:
    schemas = []
    for path in sorted(set(indexed_paths)):
        match = _SERVICE_SCHEMA.search(path)
        if match:
            schemas.append((path, match.group(1).lower()))
    services: dict[str, Service] = {}
    for text in readme_texts:
        for name, abbreviation in _NAME_ABBREVIATION.findall(text or ""):
            key = abbreviation.upper()
            if key in services:
                continue
            paths = tuple(sorted(path for path, stem in schemas if _schema_matches(name, stem)))
            services[key] = Service(abbreviation=key, name=name, schema_paths=paths)
    return services


_service_table_cache: dict[str, Service] | None = None


def service_table() -> dict[str, Service]:
    """Services read from the index, cached for the process. A failed read (no
    database, empty index) returns an empty table and is not cached."""
    global _service_table_cache
    if _service_table_cache is not None:
        return _service_table_cache
    try:
        readmes = list(
            SourceChunk.objects.filter(source_path__iendswith="README.md")
            .exclude(source_path__startswith=".mylocal")
            .values_list("text", flat=True)
        )
        paths = list(SourceChunk.objects.filter(source_path__endswith="_service.xsd").values_list("source_path", flat=True))
    except Exception:  # database unavailable or not allowed (e.g. SimpleTestCase)
        return {}
    table = build_services(readmes, paths)
    if table:
        _service_table_cache = table
    return table


def services_in_question(question: str, table: dict[str, Service] | None = None) -> list[Service]:
    """Services the question names by abbreviation, in the order they appear."""
    table = service_table() if table is None else table
    found: list[Service] = []
    for token in re.findall(r"\b[A-Za-z]{2,10}-[A-Za-z]{2,4}\b", question or ""):
        service = table.get(token.upper())
        if service and service not in found:
            found.append(service)
    return found


def expand_abbreviations(question: str, services: list[Service]) -> str:
    """The question with each abbreviation followed by its service name:
    "SIRI-CA (Control Actions)"."""
    expanded = question
    for service in services:
        expanded = re.sub(
            rf"\b{re.escape(service.abbreviation)}\b(?! \()",
            f"{service.abbreviation} ({service.name})",
            expanded,
            flags=re.IGNORECASE,
        )
    return expanded
