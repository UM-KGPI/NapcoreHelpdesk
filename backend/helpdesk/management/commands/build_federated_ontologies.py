from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError


PREFIX_LINES = [
    "@prefix nits: <https://napcore.eu/ontology/nits#> .",
    "@prefix netex: <https://napcore.eu/ontology/netex#> .",
    "@prefix opra: <https://napcore.eu/ontology/opra#> .",
    "@prefix siri: <https://napcore.eu/ontology/siri#> .",
    "@prefix datex: <https://napcore.eu/ontology/datex#> .",
    "@prefix transmodel: <https://napcore.eu/ontology/transmodel#> .",
    "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
    "@prefix dcterms: <http://purl.org/dc/terms/> .",
    "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
]

MODULE_METADATA = {
    "netex": {
        "iri": "https://napcore.eu/ontology/netex-federated",
        "title": "NeTEx Federated Ontology",
        "description": "NeTEx-focused federated ontology module generated from the local glossary and linked to NAPCORE ITS core concepts.",
        "file_name": "netex-federated.ttl",
    },
    "opra": {
        "iri": "https://napcore.eu/ontology/opra-federated",
        "title": "OpRa Federated Ontology",
        "description": "OpRa-focused federated ontology module generated from the local glossary and linked to NAPCORE ITS core concepts.",
        "file_name": "opra-federated.ttl",
    },
    "siri": {
        "iri": "https://napcore.eu/ontology/siri-federated",
        "title": "SIRI Federated Ontology",
        "description": "SIRI-focused federated ontology module generated from the local glossary and linked to NAPCORE ITS core concepts.",
        "file_name": "siri-federated.ttl",
    },
    "datex": {
        "iri": "https://napcore.eu/ontology/datex-federated",
        "title": "DATEX II Federated Ontology",
        "description": "DATEX II-focused federated ontology module generated from the local glossary and linked to NAPCORE ITS core concepts.",
        "file_name": "datex-federated.ttl",
    },
}


def _concept_namespace(concept_id: str) -> str:
    return concept_id.split(":", 1)[0].lower() if ":" in concept_id else ""


def _escape_literal(value: str) -> str:
    normalized = " ".join(str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ").split())
    return normalized.replace("\\", "\\\\").replace('"', '\\"')


def _normalize_nits_target(raw_target: str) -> str | None:
    target = (raw_target or "").strip()
    if not target:
        return None
    if target.startswith("nch:"):
        return f"nits:{target.split(':', 1)[1]}"
    if target.startswith("nits:"):
        return target
    if ":" not in target:
        return f"nits:{target}"
    return None


def _dedupe_labels(raw_labels: list[str]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for label in raw_labels:
        normalized = str(label).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        labels.append(normalized)
    return labels


def _render_concept(concept_id: str, concept_data: dict, known_concepts: set[str]) -> str:
    labels = _dedupe_labels(list(concept_data.get("labels") or []))
    predicates: list[str] = ["a skos:Concept"]

    if labels:
        predicates.append(f'skos:prefLabel "{_escape_literal(labels[0])}"@en')
        for label in labels[1:]:
            predicates.append(f'skos:altLabel "{_escape_literal(label)}"@en')

    description = str(concept_data.get("description") or "").strip()
    if description:
        predicates.append(f'rdfs:comment "{_escape_literal(description)}"@en')

    maps_to = concept_data.get("maps_to_nits") or concept_data.get("maps_to_nch")
    if isinstance(maps_to, str):
        normalized = _normalize_nits_target(maps_to)
        if normalized:
            predicates.append(f"skos:exactMatch {normalized}")

    parent = concept_data.get("parent")
    if isinstance(parent, str) and parent in known_concepts:
        predicates.append(f"skos:broader {parent}")

    synonym_of = concept_data.get("synonym_of")
    if isinstance(synonym_of, str) and synonym_of in known_concepts and synonym_of != concept_id:
        predicates.append(f"skos:closeMatch {synonym_of}")

    related_values = []
    for related in concept_data.get("related_to") or []:
        if isinstance(related, str) and related in known_concepts and related != concept_id:
            related_values.append(related)
    if related_values:
        predicates.append(f"skos:related {', '.join(sorted(set(related_values)))}")

    rendered = f"{concept_id} " + " ;\n    ".join(predicates) + " ."
    return rendered


def _build_module_ttl(*, namespace: str, concepts: dict, created_date: str, version: str) -> tuple[str, int]:
    metadata = MODULE_METADATA[namespace]
    known_concepts = {concept_id for concept_id in concepts if isinstance(concept_id, str) and ":" in concept_id}
    module_concepts = sorted(
        concept_id
        for concept_id in concepts
        if _concept_namespace(concept_id) == namespace
    )

    lines = list(PREFIX_LINES)
    lines.extend(
        [
            "",
            f"<{metadata['iri']}>",
            "    a owl:Ontology ;",
            f'    dcterms:title "{metadata["title"]}"@en ;',
            f'    dcterms:description "{metadata["description"]}"@en ;',
            f'    dcterms:created "{created_date}"^^xsd:date ;',
            f'    owl:versionInfo "{version}" ;',
            "    owl:imports <https://napcore.eu/ontology/napcore-its> ;",
            "    dcterms:license <https://creativecommons.org/licenses/by/4.0/> .",
            "",
        ]
    )

    for concept_id in module_concepts:
        concept_data = concepts.get(concept_id) or {}
        lines.append(_render_concept(concept_id, concept_data, known_concepts))
        lines.append("")

    return "\n".join(lines), len(module_concepts)


class Command(BaseCommand):
    help = "Build standard federated ontology modules (NeTEx, OpRa, SIRI, DATEX II) from backend ontology glossary (standards.yaml)."

    def add_arguments(self, parser):
        repo_root = Path(__file__).resolve().parents[4]
        parser.add_argument(
            "--input",
            default=str(repo_root / "backend" / "helpdesk" / "ontologies" / "standards.yaml"),
            help="Path to source standards.yaml glossary.",
        )
        parser.add_argument(
            "--output-dir",
            default=str(repo_root / "docs" / "ontology"),
            help="Directory where standard federated module TTL files are written.",
        )
        parser.add_argument(
            "--ontology-version",
            default="0.3.0",
            help="Version string written as owl:versionInfo.",
        )
        parser.add_argument(
            "--created-date",
            default=date.today().isoformat(),
            help="ISO date for dcterms:created (YYYY-MM-DD).",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"]).expanduser().resolve()
        output_dir = Path(options["output_dir"]).expanduser().resolve()
        version = (options.get("ontology_version") or "0.3.0").strip()
        created_date = (options.get("created_date") or "").strip()

        if not input_path.exists():
            raise CommandError(f"Input glossary not found: {input_path}")
        if len(created_date) != 10 or created_date.count("-") != 2:
            raise CommandError("--created-date must be in YYYY-MM-DD format")

        payload = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
        concepts = payload.get("concepts")
        if not isinstance(concepts, dict):
            raise CommandError("Input glossary is invalid: expected top-level 'concepts' mapping")

        output_dir.mkdir(parents=True, exist_ok=True)

        for namespace, metadata in MODULE_METADATA.items():
            ttl, concept_count = _build_module_ttl(
                namespace=namespace,
                concepts=concepts,
                created_date=created_date,
                version=version,
            )
            output_path = output_dir / metadata["file_name"]
            output_path.write_text(ttl, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Generated {output_path.name}"))
            self.stdout.write(f"concepts={concept_count}")
