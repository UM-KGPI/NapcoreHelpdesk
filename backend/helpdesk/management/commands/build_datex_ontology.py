"""
Generate docs/ontology/standards/datex.ttl from the DATEX II UML model.

The DATEX II XSD and JSON schemas carry no definitions; the Enterprise Architect model published on
docs.datex2.eu does. helpdesk.services.datex.extract_model reads it (every class, enumeration and data type with
namespace, definition, supertypes, attributes and D2Relation associations). This command only translates that
result into Turtle, with no hand edits, so the file can be rebuilt from the model at any time.

Shape (like the other standard ontologies, see extract_xsd_ontology):
- classes, enumerations and data types: owl:Class with rdfs:label, skos:prefLabel / skos:altLabel and
  skos:definition. The IRI carries the model namespace (datex:Situation.Accident) because names repeat across
  namespaces (Accident, Situation, Condition ...);
- generalisations: rdfs:subClassOf, the supertype resolved in the element's own namespace first, then by a name
  that is unique in the model, then in the namespace "Common"; an unresolvable one is counted in the header
  comment and left out;
- D2Relation associations: owl:ObjectProperty with rdfs:domain and rdfs:range (the graph expansion reads these);
- attributes (option --attributes): owl:ObjectProperty (type is an element of the model) or
  owl:DatatypeProperty (primitive type) with rdfs:domain, a label and the definition. Every property with a label
  becomes a concept in the application, so labels and definitions of properties are written only with this
  option; without it the associations carry domain and range only.

- members (option --members, needs --qea): what a class card is built from, written without a label and without a
  domain, so that the application's concept table and relation tables stay what they are. Each class gets
  ea:kind; each attribute of a class is a blank node under ea:attribute (ea:name, ea:position, ea:type as the
  IRI of the type's element, found by the model's classifier id, or ea:typeName where the type is no element, the
  bounds, ea:definition); each value of an enumeration is a blank node under ea:value (ea:name, ea:position,
  ea:definition); each relation gets its bounds (ea:lowerBound and ea:upperBound, or ea:multiplicityText where
  the model's text is not a number pair). The predicates are in the namespace ea: (ea-model#). Nothing is added to
  what an old triple says: every triple of the file without --members is in the file with it.

Output is deterministic: sorted by IRI, no timestamps.

Usage:
    python manage.py build_datex_ontology                      # from docs/datex/model-v3.7.json
    python manage.py build_datex_ontology --qea model.qea      # straight from the Enterprise Architect file
    python manage.py build_datex_ontology --attributes --out /tmp/datex-attributes.ttl
    python manage.py build_datex_ontology --qea model.qea --members     # with the facts of a class card

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-22  |  Modified: 2026-11-25
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services import datex, ea_model

DATEX_NAMESPACE = "https://docs.datex2.eu/v3.7/model#"
EA_NAMESPACE = "https://napcore.eu/ontology/ea-model#"
DEFAULT_OUT = Path(__file__).resolve().parents[4] / "docs" / "ontology" / "standards" / "datex.ttl"
SOURCE = "https://docs.datex2.eu/"
FALLBACK_NAMESPACE = "Common"


def _local(namespace: str, name: str) -> str:
    return f"{namespace}.{name}" if namespace else name


def _literal(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return '"' + cleaned.replace("\\", "\\\\").replace('"', '\\"') + '"@en'


def _labels(name: str) -> list[str]:
    """Query labels from a model name: the words (camelCase split) first, then the compact lowercase form."""
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    words = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", words).replace("_", " ").lower().strip()
    labels = [words]
    if name.lower() not in labels:
        labels.append(name.lower())
    return labels


def _bounds_lines(multiplicity: str) -> list[str]:
    """Predicate lines for a relation's multiplicity text: the two bounds, else (a typo in the model) the text."""
    bounds = ea_model.parse_multiplicity(multiplicity)
    if bounds:
        return [f"    ea:lowerBound {_plain(bounds[0])} ;", f"    ea:upperBound {_plain(bounds[1])} ;"]
    return [f"    ea:multiplicityText {_plain(multiplicity)} ;"] if (multiplicity or "").strip() else []


def _plain(text: str) -> str:
    return '"' + (text or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def _member_blocks(element: dict, own: str, resolver, counts: dict) -> list[str]:
    """The lines of one class's members (ea:kind, ea:attribute, ea:value), each ending in " ;"."""
    lines = [f"    ea:kind {_plain(element['kind'])} ;"]
    for member in element.get("members", []):
        if not member.get("name"):
            continue
        parts = [f"ea:name {_literal(member['name'])}", f"ea:position {member['position']}"]
        if element["kind"] == "enumeration":
            key = "ea:value"
            counts["values"] += 1
        else:
            key = "ea:attribute"
            counts["attributes"] += 1
            target = None
            if member.get("type_namespace") is not None:
                target = resolver.resolve(member["type_element"], member["type_namespace"], member["type_namespace"])
            if target:
                parts.append("ea:type datex:" + _local(target["namespace"], target["name"]))
                counts["typed_by_element"] += 1
                counts["typed_by_enumeration"] += int(target["kind"] == "enumeration")
            elif member.get("type"):
                parts.append(f"ea:typeName {_literal(member['type'])}")
                counts["typed_by_name"] += 1
        for name, value in (("ea:lowerBound", member.get("lower")), ("ea:upperBound", member.get("upper"))):
            if value not in (None, ""):
                parts.append(f"{name} {_plain(value)}")
        counts["bounds"] += int(member.get("lower") not in (None, "") and member.get("upper") not in (None, ""))
        if member.get("definition"):
            parts.append(f"ea:definition {_literal(member['definition'])}")
            counts["definitions"] += 1
        lines.append(f"    {key} [ " + " ; ".join(parts) + " ] ;")
    return lines


class _Resolver:
    """Finds the element a name in the model refers to; names repeat across namespaces."""

    def __init__(self, elements: list[dict]):
        self.by_name: dict[str, list[dict]] = defaultdict(list)
        for element in elements:
            self.by_name[element["name"]].append(element)

    def resolve(self, name: str, namespace: str, target_namespace: str | None = None) -> dict | None:
        """The element named `name`. With the target's own namespace (the model gives it) that is exact; without
        it (older model files, attribute types) the owner's namespace, then Common, then a unique name."""
        candidates = self.by_name.get(name, [])
        if target_namespace is not None:
            hits = [c for c in candidates if c["namespace"] == target_namespace]
            return hits[0] if len(hits) == 1 else None
        for preferred in (namespace, FALLBACK_NAMESPACE):
            hits = [c for c in candidates if c["namespace"] == preferred]
            if len(hits) == 1:
                return hits[0]
        if len(candidates) == 1:
            return candidates[0]
        return None


def build_turtle(model: dict, *, attributes: bool = False, members: bool = False, stats: dict | None = None) -> str:
    """The Turtle of the model. members: also the facts of a class card (see the module text); the model must have
    been read with extract_model(member_facts=True). stats, when given, is filled with what members wrote."""
    elements = model["elements"]
    counts = {
        "classes": 0, "attributes": 0, "values": 0, "definitions": 0, "typed_by_element": 0, "typed_by_enumeration": 0,
        "typed_by_name": 0, "bounds": 0, "relations": 0, "relations_with_bounds": 0, "relations_with_text_only": 0,
    }
    if members and any("position" not in m for e in elements for m in e.get("members", [])):
        raise ValueError("members need the facts of extract_model(member_facts=True): read the .qea file")
    resolver = _Resolver(elements)
    unresolved = {"supertypes": 0, "associations": 0, "attributes": 0, "repeated": 0}
    blocks: dict[str, list[str]] = {}
    classes = properties = 0

    def iri(element: dict) -> str:
        return "datex:" + _local(element["namespace"], element["name"])

    for element in elements:
        namespace, name = element["namespace"], element["name"]
        own = iri(element)
        lines = [own, "    a owl:Class ;", f"    rdfs:label {_literal(name)} ;"]
        if element.get("definition"):
            lines.append(f"    skos:definition {_literal(element['definition'])} ;")
        pref, *alts = _labels(name)
        lines.append(f"    skos:prefLabel {_literal(pref)} ;")
        lines.extend(f"    skos:altLabel {_literal(alt)} ;" for alt in alts)
        refs = element.get("supertype_refs") or [{"name": n, "namespace": None} for n in element.get("supertypes", [])]
        for ref in sorted(refs, key=lambda r: (r["name"], r["namespace"] or "")):
            target = resolver.resolve(ref["name"], namespace, ref["namespace"])
            if target is None:
                unresolved["supertypes"] += 1
            elif iri(target) != own and f"    rdfs:subClassOf {iri(target)} ;" not in lines:
                lines.append(f"    rdfs:subClassOf {iri(target)} ;")
        place = " / ".join(p for p in (namespace, element.get("package", "")) if p)
        comment = f"    rdfs:comment {_literal('DATEX II ' + element['kind'] + ' in namespace ' + place)}"
        if members:
            lines.append(comment + " ;")
            lines.extend(_member_blocks(element, own, resolver, counts))
            lines[-1] = lines[-1][:-2] + " ."
            counts["classes"] += 1
        else:
            lines.append(comment + " .")
        blocks[own] = lines
        classes += 1

        for association in element.get("associations", []):
            target = resolver.resolve(association["target"], namespace, association.get("target_namespace"))
            if target is None:
                unresolved["associations"] += 1
                continue
            # A relation the model leaves without a role name is named after its target; a name already taken
            # (another relation of the element, the same name in another namespace) takes the target's namespace.
            role = association["role"] or association["target"]
            prop = f"{own}.{role}"
            if prop in blocks and not association["role"]:
                prop = f"{own}.{_local(target['namespace'], target['name'])}"
            if prop in blocks:  # the same relation twice, or a role name given twice
                unresolved["repeated"] += 1
                continue
            plines = [prop, "    a owl:ObjectProperty ;"]
            if attributes and association["role"]:
                plines.append(f"    rdfs:label {_literal(association['role'])} ;")
                plines.append(f"    skos:prefLabel {_literal(_labels(association['role'])[0])} ;")
            plines.append(f"    rdfs:domain {own} ;")
            bounds = _bounds_lines(association.get("multiplicity", "")) if members else []
            if bounds:
                plines.append(f"    rdfs:range {iri(target)} ;")
                plines.extend(bounds)
                plines[-1] = plines[-1][:-2] + " ."
                counts["relations_with_bounds" if len(bounds) == 2 else "relations_with_text_only"] += 1
            else:
                plines.append(f"    rdfs:range {iri(target)} .")
            counts["relations"] += 1
            blocks[prop] = plines
            properties += 1

        if attributes and element["kind"] != "enumeration":
            for member in element.get("members", []):
                if not member.get("name"):
                    continue
                prop = f"{own}.{member['name']}"
                if prop in blocks:  # an attribute named like an association role
                    continue
                target = resolver.resolve(member.get("type", ""), namespace) if member.get("type") else None
                plines = [prop, "    a owl:ObjectProperty ;" if target else "    a owl:DatatypeProperty ;"]
                plines.append(f"    rdfs:label {_literal(member['name'])} ;")
                plines.append(f"    skos:prefLabel {_literal(_labels(member['name'])[0])} ;")
                if member.get("definition"):
                    plines.append(f"    skos:definition {_literal(member['definition'])} ;")
                plines.append(f"    rdfs:domain {own} ;")
                if target:
                    plines.append(f"    rdfs:range {iri(target)} .")
                else:
                    unresolved["attributes"] += 1  # primitive or unresolved type: counted, not an error
                    plines[-1] = plines[-1].rstrip(" ;") + " ."
                blocks[prop] = plines
                properties += 1

    header = [
        "# Generated by `manage.py build_datex_ontology` from the DATEX II UML model; do not edit, rebuild instead.",
        "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl:  <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix dct:  <http://purl.org/dc/terms/> .",
        "",
        f"@prefix datex: <{DATEX_NAMESPACE}> .",
        *([f"@prefix ea: <{EA_NAMESPACE}> ."] if members else []),
        "",
        f"<{DATEX_NAMESPACE[:-1]}>",
        "    a owl:Ontology ;",
        '    dct:title "DATEX II Ontology generated from the UML model"@en ;',
        '    dct:description "OWL ontology generated from the DATEX II Enterprise Architect model: classes, '
        'enumerations and data types with their definitions, generalisations and associations."@en ;',
        f"    owl:versionInfo {_literal('v' + str(model.get('version', '')))} ;",
        f"    dct:source <{SOURCE}> .",
        "",
        "#################################################################",
        f"# {classes} classes, enumerations and data types; {properties} properties"
        + (" (associations and attributes)" if attributes else " (associations)"),
        f"# unresolved: {unresolved['supertypes']} supertypes, {unresolved['associations']} associations"
        + (f"; {unresolved['repeated']} relations repeating an IRI already written" if unresolved["repeated"] else "")
        + (f"; {unresolved['attributes']} attributes typed by a primitive or a name outside the model" if attributes else ""),
        "#################################################################",
        "",
    ]
    body: list[str] = []
    for key in sorted(blocks):
        body.extend(blocks[key])
        body.append("")
    if stats is not None:
        stats.update(counts)
    return "\n".join(header + body)


class Command(BaseCommand):
    help = "Write docs/ontology/standards/datex.ttl from the DATEX II UML model (generated only, deterministic)."

    def add_arguments(self, parser):
        parser.add_argument("--model", default=str(datex.MODEL_PATH), help="model JSON written by fetch_model")
        parser.add_argument("--qea", default="", help="read the Enterprise Architect file instead of the JSON")
        parser.add_argument("--out", default=str(DEFAULT_OUT), help="Turtle file to write")
        parser.add_argument("--attributes", action="store_true", help="also write attributes (and labels of properties)")
        parser.add_argument(
            "--members",
            action="store_true",
            help="also write the facts of a class card (attributes, types, bounds, values), without labels; needs --qea",
        )

    def handle(self, *args, **options):
        if options["members"] and options["attributes"]:
            raise CommandError("--members and --attributes do not go together: --attributes writes labels")
        if options["members"] and not options["qea"]:
            raise CommandError("--members needs --qea: the model's JSON does not hold the classifier of a type")
        if options["qea"]:
            model = datex.extract_model(Path(options["qea"]), member_facts=bool(options["members"]))
        else:
            path = Path(options["model"])
            if not path.exists():
                raise CommandError(f"model file not found: {path}")
            model = json.loads(path.read_text(encoding="utf-8"))
        stats: dict = {}
        text = build_turtle(model, attributes=bool(options["attributes"]), members=bool(options["members"]), stats=stats)
        out = Path(options["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"wrote {out} ({len(text.splitlines())} lines)"))
        if options["members"]:
            self.stdout.write("members: " + ", ".join(f"{key} {value}" for key, value in stats.items()))
