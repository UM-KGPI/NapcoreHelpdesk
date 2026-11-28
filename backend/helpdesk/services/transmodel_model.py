"""
The Transmodel ontology (docs/ontology/standards/transmodel.ttl) from the Transmodel Enterprise Architect model.

The tables are read by the general reader (services/ea_model.py) with the Transmodel profile below; this module
only turns the result into Turtle. The rules are those of the generator that wrote transmodel.ttl on 6 May
(scripts/regenerate_transmodel_from_qea.py, removed in 3f1c9a8), except the scope (now written as the Transmodel
v6.2 root minus the excluded packages, the same classes in this model), the relation IRIs (now one per
association end) and skos:definition, so the file is rebuilt from the model, never edited by hand:

- classes: every UML class of the packages in scope, in Object_ID order. IRI tm:UPPER_SNAKE from the words of
  the name; a name already taken by an earlier class (lower Object_ID) gets _<Object_ID>; rdfs:label is the
  name, rdfs:comment and skos:definition the Note (stripped; line breaks become spaces);
- generalisations between two classes in scope: rdfs:subClassOf, sorted;
- associations and aggregations between two classes in scope: a relation each way. The relation of the start
  class is named by the role at the destination end and the other way round; without a role it is "has" plus
  the target's name (hasSTOPPLACE). The label is the role, else "has <target name>"; a later connector with the
  same domain, name and range replaces the label of an earlier one. Each relation has its own IRI with exactly
  one domain and one range: tm:<name>.<DOMAIN> (tm:hasSITEFRAME.STOP_PLACE), and tm:<name>.<DOMAIN>.<RANGE>
  when the domain has the same name towards several ranges (tm:in.STOP_PLACE.QUAY, tm:in.STOP_PLACE.ACCESS_SPACE).
  The name comes first and starts lower case, so a relation is never read as a class (a class name starts upper
  case) and its own name is the first part (semantic_graph.local_own_name).
  Until 24 November (step R4 of the plan) the IRI was the name alone, shared by every class pair with that
  role, so a graph could not tell which domain went with which range. Sorted by IRI;
- members (option members=True, command option --members): what a class card is built from, written without a
  label and without a domain, so that the application's concept table and relation tables stay what they are.
  Each class gets ea:kind ("class", or "enumeration" for the four classes with that stereotype); each attribute
  is a blank node under ea:attribute (ea:name, ea:position, ea:type as the IRI of the class its classifier id
  names, else ea:typeName, ea:lowerBound, ea:upperBound, ea:definition from the attribute's own Notes); each
  value of an enumeration class is a blank node under ea:value; each relation gets its bounds from the end of the
  connector that gives its multiplicity (the later connector of two with the same name, domain and range
  replaces the earlier, as for the label), or ea:multiplicityText where the model's text is not a number pair.
  Every triple of the file without members is in the file with them;
- the EA GUID of each class (tmalign:eaGuid) in a marked section at the end of the file
  (services/transmodel_guids.py reads it for the ?guid= links of the Transmodel HTML export, issue #151).

No timestamp: the same model gives the same file.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-24  |  Modified: 2026-11-25
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from helpdesk.services import ea_model
from helpdesk.services.transmodel_guids import guid_section

# The root package of Transmodel v6.2 in the model file; the file holds other models beside it (NeTEx and SIRI
# physical models, OSDM, "Transmodel New Development 2025", ...), which stay out.
ROOT_PACKAGE = "Transmodel v6.2  2024"
# Packages below the root that are not part of the ontology. "TM Glossary" holds 47 classes that are glossary
# entries (abbreviations such as SIRI, IT, PT and data-modelling terms such as entity or graph), not Transmodel
# concepts; left out by decision of 24 November.
EXCLUDED_PACKAGES = ("TM Glossary",)

# What the general reader keeps of the Transmodel model: the UML classes of every package below the root except the
# excluded ones; the definition is the Note; associations and aggregations are the relations (the model's
# Dependency, Abstraction, Package and Nesting connectors are not). Until 24 November (step R2 of the plan) the
# scope was the packages whose path names one of the parts 1 to 8 or 10; in this model that is the same classes.
PROFILE = ea_model.Profile(
    element_types=("Class",),
    package_path_patterns=(rf"^{re.escape(' '.join(ROOT_PACKAGE.split()))}(?: > |$)",),
    excluded_packages=EXCLUDED_PACKAGES,
    definition_text=ea_model.STRIPPED,
    relation_types=("Association", "Aggregation"),
    attribute_definition_from_notes=True,
)
EA_NAMESPACE = "https://napcore.eu/ontology/ea-model#"

HEADER = """# Transmodel RDF/Turtle Ontology
# Source: {source}

@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix tm: <https://transmodel-cen.eu/6.2/> .{members_prefix}

tm:TransmodelOntology a owl:Ontology ;
  rdfs:label "Transmodel Core Ontology v6.2" ;
  rdfs:comment "Transmodel v6.2 (2024) generated from EA UML model with class hierarchy, association roles, and multiplicity restrictions." ;
  owl:versionInfo "6.2" ."""


@dataclass
class _Class:
    local: str
    label: str
    comment: str
    guid: str
    parents: set[str] = field(default_factory=set)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", " ").replace("\n", " ").strip()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text or "")


def class_local(name: str) -> str:
    """tm: local name of a class name: its words joined by "_" ("PRE-ASSIGNED FARE PRODUCT" ->
    PRE_ASSIGNED_FARE_PRODUCT); a leading digit gets a leading "_"."""
    tokens = _tokens(name)
    if not tokens:
        return "UnnamedClass"
    local = "_".join(tokens)
    return f"_{local}" if local[0].isdigit() else local


def property_local(role: str, target_name: str) -> str:
    """tm: local name of a relation: the role in lowerCamelCase, else "has" plus the target's name."""
    tokens = _tokens((role or "").strip()) or ["has"] + _tokens(target_name)
    if not tokens:
        return "relatedTo"
    return tokens[0].lower() + "".join(token[:1].upper() + token[1:] for token in tokens[1:])


def relation_iri_keys(relations: dict[tuple[str, str, str], str]) -> dict[str, tuple[str, str, str]]:
    """{IRI local name: (name, domain, range)} for relations keyed (name, domain, range): name.DOMAIN, and
    name.DOMAIN.RANGE when the domain has that name towards more than one range."""
    ranges: dict[tuple[str, str], set[str]] = {}
    for name, domain, range_ in relations:
        ranges.setdefault((domain, name), set()).add(range_)
    return {
        (f"{name}.{domain}" if len(ranges[(domain, name)]) == 1 else f"{name}.{domain}.{range_}"): (name, domain, range_)
        for (name, domain, range_) in relations
    }


def relation_iris(relations: dict[tuple[str, str, str], str]) -> dict[str, tuple[str, str, str]]:  # (domain, range, label)
    """{IRI local name: (domain, range, label)} for relations keyed (name, domain, range): name.DOMAIN, and
    name.DOMAIN.RANGE when the domain has the same name towards several ranges. Every IRI gets one pair."""
    return {iri: (key[1], key[2], relations[key]) for iri, key in relation_iri_keys(relations).items()}


def _plain(text: str) -> str:
    return '"' + _escape(text) + '"'


def _bounds_text(card: str) -> list[str]:
    """Predicate texts for a relation's multiplicity: the two bounds, else (a typo in the model) the text."""
    bounds = ea_model.parse_multiplicity(card)
    if bounds:
        return [f"ea:lowerBound {_plain(bounds[0])}", f"ea:upperBound {_plain(bounds[1])}"]
    return [f"ea:multiplicityText {_plain(card)}"] if (card or "").strip() else []


def build_turtle(
    qea_path: Path, profile: ea_model.Profile = PROFILE, *, members: bool = False, stats: dict | None = None
) -> str:
    """transmodel.ttl for the model at qea_path. Raises ValueError when the profile keeps no class. members: also the
    facts of a class card (see the module text); stats, when given, is filled with what members wrote."""
    model = ea_model.read_model(qea_path, profile, attributes=members)
    counts = {
        "classes": 0, "enumerations": 0, "attributes": 0, "values": 0, "definitions": 0, "typed_by_element": 0,
        "typed_by_name": 0, "untyped": 0, "bounds": 0, "relations": 0, "relations_with_bounds": 0,
        "relations_with_text_only": 0,
    }
    classes: list[_Class] = []
    local_of: dict[int, str] = {}
    used: set[str] = set()
    for element in model.elements.values():
        label = element.name.strip()
        if not label:
            continue
        local = class_local(label)
        if local in used:
            local = f"{local}_{element.id}"
        used.add(local)
        classes.append(_Class(local=local, label=label, comment=element.definition, guid=element.guid))
        local_of[element.id] = local
    if not classes:
        raise ValueError(f"no Transmodel classes in scope in {qea_path.name}")
    by_local = {cls.local: cls for cls in classes}

    for connector in model.generalizations:
        child, parent = local_of.get(connector.start), local_of.get(connector.end)
        if child and parent and child != parent:
            by_local[child].parents.add(parent)

    properties: dict[tuple[str, str, str], str] = {}
    cards: dict[tuple[str, str, str], str] = {}

    def add(domain: str, range_: str, role: str, target_name: str, card: str = "") -> None:
        label = role.strip() if role.strip() else f"has {target_name}".strip()
        key = (property_local(role, target_name), domain, range_)
        properties[key] = label
        cards[key] = card or ""

    for connector in model.relations:
        start, end = local_of.get(connector.start), local_of.get(connector.end)
        if not start or not end or start == end:
            continue
        # The role at the destination end names the start class's property, and the other way round.
        add(start, end, connector.dest_role, model.elements[connector.end].name or by_local[end].label, connector.dest_card)
        add(end, start, connector.source_role, model.elements[connector.start].name or by_local[start].label, connector.source_card)

    members_of: dict[str, list[str]] = {}
    if members:
        for ident, element in model.elements.items():
            local = local_of.get(ident)
            if not local:
                continue
            kind = ea_model.element_kind(element)
            lines = [f"  ; ea:kind {_plain(kind)}"]
            counts["classes"] += 1
            counts["enumerations"] += int(kind == "enumeration")
            for attribute in model.attributes.get(ident, []):
                parts = [f"ea:name {_plain(attribute.name)}", f"ea:position {attribute.position}"]
                if kind == "enumeration":
                    key = "ea:value"
                    counts["values"] += 1
                else:
                    key = "ea:attribute"
                    counts["attributes"] += 1
                    target = local_of.get(attribute.classifier) if attribute.classifier else None
                    if target:
                        parts.append(f"ea:type tm:{target}")
                        counts["typed_by_element"] += 1
                    elif attribute.type.strip():
                        parts.append(f"ea:typeName {_plain(attribute.type.strip())}")
                        counts["typed_by_name"] += 1
                    else:
                        counts["untyped"] += 1
                for name, value in (("ea:lowerBound", attribute.lower), ("ea:upperBound", attribute.upper)):
                    if value:
                        parts.append(f"{name} {_plain(value)}")
                counts["bounds"] += int(bool(attribute.lower and attribute.upper))
                if attribute.definition:
                    parts.append(f"ea:definition {_plain(attribute.definition)}")
                    counts["definitions"] += 1
                lines.append(f"  ; {key} [ " + " ; ".join(parts) + " ]")
            members_of[local] = lines
    header = HEADER.format(source=qea_path.name, members_prefix=f"\n@prefix ea: <{EA_NAMESPACE}> ." if members else "")
    out = [header, ""]
    for cls in classes:
        lines = [f"tm:{cls.local} a owl:Class ;", f'  rdfs:label "{_escape(cls.label)}"']
        if cls.comment:
            lines.append(f'  ; rdfs:comment "{_escape(cls.comment)}"')
            lines.append(f'  ; skos:definition "{_escape(cls.comment)}"')
        lines.extend(f"  ; rdfs:subClassOf tm:{parent}" for parent in sorted(cls.parents))
        lines.extend(members_of.get(cls.local, []))
        lines.append("  .")
        out.append("\n".join(lines))
    out.extend(["", "# Object properties derived from UML associations/aggregations", ""])
    keys = relation_iri_keys(properties)
    for iri, (domain, range_, label) in sorted(relation_iris(properties).items()):
        bounds = _bounds_text(cards[keys[iri]]) if members else []
        counts["relations"] += int(members)
        counts["relations_with_bounds"] += int(len(bounds) == 2)
        counts["relations_with_text_only"] += int(len(bounds) == 1)
        tail = (" ;\n  " + " ;\n  ".join(bounds) + " .") if bounds else " ."
        out.append(
            f'tm:{iri} a owl:ObjectProperty ;\n  rdfs:label "{_escape(label)}" ;\n'
            f"  rdfs:domain tm:{domain} ;\n  rdfs:range tm:{range_}{tail}"
        )
    text = "\n\n".join(out).rstrip() + "\n"
    guids = {cls.local: [cls.guid] for cls in classes if cls.guid}
    if stats is not None:
        stats.update(counts)
    return text + guid_section(sorted(by_local), guids, qea_path.name)
