from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError


def _concept_namespace(concept_id: str) -> str:
    return concept_id.split(":", 1)[0].lower() if ":" in concept_id else ""


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


def _build_alignment_sets(concepts: dict, include_related: bool) -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str]]]:
    exact: set[tuple[str, str]] = set()
    close: set[tuple[str, str]] = set()
    related_raw: set[tuple[str, str]] = set()

    standard_namespaces = {"netex", "opra", "siri", "datex"}

    for concept_id, concept_data in concepts.items():
        if not isinstance(concept_id, str) or not isinstance(concept_data, dict):
            continue
        namespace = _concept_namespace(concept_id)
        if namespace not in standard_namespaces:
            continue

        maps_to = concept_data.get("maps_to_nits") or concept_data.get("maps_to_nch")
        if isinstance(maps_to, str):
            normalized = _normalize_nits_target(maps_to)
            if normalized:
                exact.add((concept_id, normalized))

        synonym_of = concept_data.get("synonym_of")
        if isinstance(synonym_of, str) and ":" in synonym_of and synonym_of != concept_id:
            other_ns = _concept_namespace(synonym_of)
            if other_ns in standard_namespaces and other_ns != namespace:
                close.add((concept_id, synonym_of))

        if include_related:
            for related_to in concept_data.get("related_to") or []:
                if not isinstance(related_to, str) or ":" not in related_to or related_to == concept_id:
                    continue
                other_ns = _concept_namespace(related_to)
                if other_ns in standard_namespaces and other_ns != namespace:
                    related_raw.add(tuple(sorted((concept_id, related_to))))

    return exact, close, related_raw


def _build_ttl(
    *,
    created_date: str,
    version: str,
    exact: set[tuple[str, str]],
    close: set[tuple[str, str]],
    related: set[tuple[str, str]],
) -> str:
    lines = [
        "@prefix nits: <https://napcore.eu/ontology/nits#> .",
        "@prefix netex: <https://napcore.eu/ontology/netex#> .",
        "@prefix opra: <https://napcore.eu/ontology/opra#> .",
        "@prefix siri: <https://napcore.eu/ontology/siri#> .",
        "@prefix datex: <https://napcore.eu/ontology/datex#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "",
        "<https://napcore.eu/ontology/standards-alignment>",
        "    a owl:Ontology ;",
        "    dcterms:title \"NAPCORE Standards Alignment Ontology\"@en ;",
        "    dcterms:description \"Alignment module generated from local glossary mappings across NeTEx, OpRa, SIRI, DATEX II, and NAPCORE ITS core concepts, including exact, close, and related cross-standard links.\"@en ;",
        f"    dcterms:created \"{created_date}\"^^xsd:date ;",
        f"    owl:versionInfo \"{version}\" ;",
        "    owl:imports <https://napcore.eu/ontology/napcore-its>,",
        "                <https://napcore.eu/ontology/netex-federated>,",
        "                <https://napcore.eu/ontology/opra-federated>,",
        "                <https://napcore.eu/ontology/siri-federated>,",
        "                <https://napcore.eu/ontology/datex-federated> ;",
        "    dcterms:license <https://creativecommons.org/licenses/by/4.0/> .",
        "",
        "# Core anchors (standard concept -> nits core concept)",
    ]

    for source, target in sorted(exact):
        lines.append(f"{source} skos:exactMatch {target} .")

    lines.extend(["", "# Cross-standard close matches (lexical/semantic synonym links)"])
    for source, target in sorted(close):
        lines.append(f"{source} skos:closeMatch {target} .")

    lines.extend(["", "# Cross-standard related matches (operational/contextual relations)"])
    for left, right in sorted(related):
        lines.append(f"{left} skos:relatedMatch {right} .")

    lines.append("")
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Build standards-alignment.ttl from backend ontology glossary (standards.yaml)."

    def add_arguments(self, parser):
        repo_root = Path(__file__).resolve().parents[4]
        parser.add_argument(
            "--input",
            default=str(repo_root / "backend" / "helpdesk" / "ontologies" / "standards.yaml"),
            help="Path to source standards.yaml glossary.",
        )
        parser.add_argument(
            "--output",
            default=str(repo_root / "docs" / "ontology" / "standards-alignment.ttl"),
            help="Path to output standards-alignment.ttl file.",
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
        parser.add_argument(
            "--no-related",
            action="store_true",
            help="Skip skos:relatedMatch generation and emit only exact/close alignments.",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"]).expanduser().resolve()
        output_path = Path(options["output"]).expanduser().resolve()
        include_related = not bool(options.get("no_related"))
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

        exact, close, related = _build_alignment_sets(concepts, include_related=include_related)
        ttl = _build_ttl(
            created_date=created_date,
            version=version,
            exact=exact,
            close=close,
            related=related,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ttl, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS("Standards alignment ontology generated."))
        self.stdout.write(f"input={input_path}")
        self.stdout.write(f"output={output_path}")
        self.stdout.write(f"exact_matches={len(exact)}")
        self.stdout.write(f"close_matches={len(close)}")
        self.stdout.write(f"related_matches={len(related)}")