"""
Recover the NeTEx classes that object properties point to but the extractor did not produce.

extract_xsd_ontology emits a class only for elements that pass its domain-concept filters. The
property enrichment (scripts/build_netex_ttl_with_properties.py) then finds object properties whose
range is a NeTEx element that is not a class ("dangling" targets): DayType, VehicleType,
TimeDemandType and so on. Leaving them out cuts those properties off from the ontology.

The rule here is the same for every run, so the ontology can be regenerated from the NeTEx
repository without hand work. A dangling target becomes a class when

- it is declared as an xsd:element;
- its name is PascalCase (a lower-case element name is a container such as privateCodes);
- it is not a placeholder (X_Dummy) or a derived view (XView, XInverse).

Its definition is the documentation of the element, else the documentation of its type; a class
with neither is still recovered, without a definition.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-19  |  Modified: 2026-10-19
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

XSD_NS = "{http://www.w3.org/2001/XMLSchema}"
NON_CLASS_SUFFIXES = ("_Dummy", "View", "Inverse")
RECOVERY_MARKER = "(property-gap recovery)"


@dataclass(frozen=True)
class ElementDeclaration:
    name: str
    source: str  # path relative to the xsd root
    documentation: str  # the element's own documentation, else its type's, else empty
    substitution_group: str


def _documentation(node: ET.Element) -> str:
    doc_node = node.find(f"{XSD_NS}annotation/{XSD_NS}documentation")
    return " ".join((doc_node.text or "").split()) if doc_node is not None else ""


def _type_documentation(xsd_root: Path) -> dict[str, str]:
    """The first documentation found for each named complexType and simpleType."""

    documented: dict[str, str] = {}
    for path in sorted(xsd_root.rglob("*.xsd")):
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            continue
        for tag in ("complexType", "simpleType"):
            for node in tree.iter(f"{XSD_NS}{tag}"):
                name = node.get("name")
                doc = _documentation(node) if name else ""
                if name and doc and name not in documented:
                    documented[name] = doc
    return documented


def collect_element_declarations(xsd_root: Path) -> dict[str, ElementDeclaration]:
    """Every named xsd:element under the xsd root, keyed by name.

    A name declared more than once keeps the first declaration that has documentation (files are
    read in sorted order, so the result does not depend on the file system).
    """

    type_docs = _type_documentation(xsd_root)
    declarations: dict[str, ElementDeclaration] = {}
    for path in sorted(xsd_root.rglob("*.xsd")):
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            continue
        relative = path.relative_to(xsd_root).as_posix()
        for element in tree.iter(f"{XSD_NS}element"):
            name = element.get("name")
            if not name:
                continue
            type_name = (element.get("type") or "").rsplit(":", 1)[-1]
            documentation = _documentation(element) or type_docs.get(type_name, "")
            declaration = ElementDeclaration(
                name=name,
                source=relative,
                documentation=documentation,
                substitution_group=(element.get("substitutionGroup") or "").strip(),
            )
            current = declarations.get(name)
            if current is None or (not current.documentation and documentation):
                declarations[name] = declaration
    return declarations


def is_recoverable(name: str, declaration: ElementDeclaration | None) -> bool:
    return declaration is not None and name[:1].isupper() and not name.endswith(NON_CLASS_SUFFIXES)


def select_recoverable(
    dangling: dict[str, int], declarations: dict[str, ElementDeclaration], known_classes: set[str]
) -> list[str]:
    """The dangling property targets that become classes, in a stable order."""

    return sorted(
        name for name in dangling if name not in known_classes and is_recoverable(name, declarations.get(name))
    )


def camel_to_words(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name).lower()


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render_class(declaration: ElementDeclaration, known_classes: set[str]) -> str:
    """One class block in the layout the extractor uses (the property enrichment reads it back)."""

    lines = [f"netex:{declaration.name}", "    a owl:Class ;"]
    if declaration.documentation:
        lines.append(f'    skos:definition "{_escape(declaration.documentation)}"@en ;')
    lines.append(f'    skos:prefLabel "{camel_to_words(declaration.name)}"@en ;')
    group = declaration.substitution_group
    if group and ":" not in group and group in known_classes:
        lines.append(f"    rdfs:subClassOf netex:{group} ;")
    lines.append(f'    rdfs:comment "Extracted from: xsd/{declaration.source} {RECOVERY_MARKER}"@en .')
    return "\n".join(lines)


def append_recovered_classes(ttl_text: str, names: list[str], declarations: dict[str, ElementDeclaration], known_classes: set[str]) -> str:
    """The Turtle text with the recovered classes added at the end."""

    if not names:
        return ttl_text
    blocks = [render_class(declarations[name], known_classes) for name in names]
    return ttl_text.rstrip("\n") + "\n\n# Classes recovered from property targets\n\n" + "\n\n".join(blocks) + "\n"
