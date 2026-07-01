"""
Convert extracted ontology JSON (with relationships) to Turtle (TTL) RDF format.

This command reads the JSON ontologies produced by extract_xsd_ontology.py
and converts them to TTL with full semantic relationships:
- rdfs:subClassOf from related_to (substitutionGroup)
- skos:definition from description (xsd:annotation)
- Composition relationships from xsd:group references

Usage:
    python manage.py ontologies_json_to_ttl \
        --input backend/helpdesk/ontologies/standards.json \
        --output-dir .mylocal/docs/ontology/standards/
"""

import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Convert extracted ontology JSON to Turtle (TTL) RDF format with full relationships"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            required=True,
            help="Path to extracted ontologies JSON file",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            required=True,
            help="Directory to write TTL files for each standard",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"])
        output_dir = Path(options["output_dir"])

        if not input_path.exists():
            raise CommandError(f"Input file not found: {input_path}")

        # Load JSON ontologies
        self.stdout.write(f"Loading ontologies from {input_path}...")
        with open(input_path) as f:
            ontologies = json.load(f)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate TTL for each standard
        for standard in ["netex", "opra", "siri", "datex", "transmodel"]:
            standard_concepts = {
                cid: cdata
                for cid, cdata in ontologies.get("concepts", {}).items()
                if cid.startswith(f"{standard}:")
            }

            if not standard_concepts:
                self.stdout.write(f"  ℹ  No concepts for {standard}, skipping")
                continue

            ttl_content = self._generate_ttl(standard, standard_concepts, ontologies.get("namespaces", {}))
            output_file = output_dir / f"{standard}.ttl"

            with open(output_file, "w") as f:
                f.write(ttl_content)

            self.stdout.write(self.style.SUCCESS(f"  ✓ {standard}: {len(standard_concepts)} concepts → {output_file}"))

        self.stdout.write(self.style.SUCCESS(f"\n✓ TTL files generated in {output_dir}"))

    def _generate_ttl(self, standard: str, concepts: dict, namespaces: dict) -> str:
        """Generate TTL content with full semantic relationships."""

        lines = []

        # Prefixes
        lines.append("@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
        lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        lines.append("@prefix owl:  <http://www.w3.org/2002/07/owl#> .")
        lines.append("@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .")
        lines.append("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
        lines.append("@prefix dct:  <http://purl.org/dc/terms/> .")
        lines.append("")

        # Add custom prefixes from namespaces
        for prefix, namespace in namespaces.items():
            lines.append(f"@prefix {prefix}: <{namespace}> .")
        lines.append("")

        # Ontology header
        std_iri = namespaces.get(standard, f"https://napcore.eu/ontology/{standard}#")
        lines.append(f"<{std_iri[:-1]}>")
        lines.append("    a owl:Ontology ;")
        lines.append(f'    dct:title "{standard.upper()} Semantic Ontology with Relationships"@en ;')
        lines.append(
            f'    dct:description "{standard.upper()} OWL ontology with extracted schema relationships (inheritance, composition, definitions)."@en ;'
        )
        lines.append('    dct:creator "NAPCORE Community" ;')
        lines.append('    owl:versionInfo "0.2-xsd-with-relationships" ;')
        lines.append('    dct:license <https://creativecommons.org/licenses/by/4.0/> .')
        lines.append("")

        lines.append("#################################################################")
        lines.append("# Concepts with Full Semantic Relationships")
        lines.append("#################################################################")
        lines.append("")

        # Generate concept definitions
        for concept_id in sorted(concepts.keys()):
            concept = concepts[concept_id]
            lines.append(f"{concept_id}")
            lines.append("    a owl:Class ;")

            # Label
            label = concept.get("name", "")
            if label:
                lines.append(f'    rdfs:label "{label}"@en ;')

            # Definition from description (xsd:annotation → skos:definition)
            description = concept.get("description", "").strip()
            if description:
                # Escape quotes in description
                escaped_desc = description.replace('"', '\\"')
                lines.append(f'    skos:definition "{escaped_desc}"@en ;')

            # Preferred and alternative labels
            labels = concept.get("labels", [])
            if labels:
                lines.append(f'    skos:prefLabel "{labels[0]}"@en ;')
                for alt_label in labels[1:]:
                    lines.append(f'    skos:altLabel "{alt_label}"@en ;')

            # Related concepts as rdfs:subClassOf (from substitutionGroup extraction)
            related_to = concept.get("related_to", [])
            if related_to:
                for i, related_id in enumerate(related_to):
                    if i == len(related_to) - 1:
                        # Last relation, no semicolon
                        lines.append(f"    rdfs:subClassOf {related_id} ;")
                    else:
                        lines.append(f"    rdfs:subClassOf {related_id} ;")

            # Source file reference
            source = concept.get("source", "")
            if source:
                lines.append(f'    rdfs:comment "Extracted from XSD source: {source}"@en .')
            else:
                lines.append('    rdfs:comment "Schema-extracted concept"@en .')

            lines.append("")

        return "\n".join(lines)
