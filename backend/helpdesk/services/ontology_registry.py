"""
Tracks and validates versioned ontology assets loaded into the semantic layer.

Compares content hashes of local TTL files against OntologyAssetVersion
records to detect when ontologies must be re-loaded into GraphDB named graphs.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-26  |  Modified: 2026-06-28
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from django.utils import timezone

from helpdesk.models import OntologyAssetVersion


ONTOLOGY_SPECS = [
    {
        "ontology_key": "napcore-its",
        "file_path": "napcore-its.ttl",
        "graph_uri": "https://napcore.eu/graph/core/napcore-its",
    },
    {
        "ontology_key": "transmodel",
        "file_path": "standards/transmodel.ttl",
        "graph_uri": "https://napcore.eu/graph/standards/transmodel",
    },
    {
        "ontology_key": "netex",
        "file_path": "standards/netex.ttl",
        "graph_uri": "https://napcore.eu/graph/standards/netex",
    },
    {
        "ontology_key": "opra",
        "file_path": "standards/opra.ttl",
        "graph_uri": "https://napcore.eu/graph/standards/opra",
    },
    {
        "ontology_key": "siri",
        "file_path": "standards/siri.ttl",
        "graph_uri": "https://napcore.eu/graph/standards/siri",
    },
    {
        "ontology_key": "datex",
        "file_path": "standards/datex.ttl",
        "graph_uri": "https://napcore.eu/graph/standards/datex",
    },
    {
        "ontology_key": "netex-examples",
        "file_path": "examples/netex-examples.ttl",
        "graph_uri": "https://napcore.eu/graph/examples/netex",
    },
    {
        "ontology_key": "nits-transmodel-align",
        "file_path": "alignments/nits-transmodel-align.ttl",
        "graph_uri": "https://napcore.eu/graph/alignments/transmodel",
    },
    {
        "ontology_key": "nits-netex-align",
        "file_path": "alignments/nits-netex-align.ttl",
        "graph_uri": "https://napcore.eu/graph/alignments/netex",
    },
    {
        "ontology_key": "nits-opra-align",
        "file_path": "alignments/nits-opra-align.ttl",
        "graph_uri": "https://napcore.eu/graph/alignments/opra",
    },
    {
        "ontology_key": "nits-siri-align",
        "file_path": "alignments/nits-siri-align.ttl",
        "graph_uri": "https://napcore.eu/graph/alignments/siri",
    },
    {
        "ontology_key": "nits-datex-align",
        "file_path": "alignments/nits-datex-align.ttl",
        "graph_uri": "https://napcore.eu/graph/alignments/datex",
    },
    {
        "ontology_key": "netex-artifact-rules-v1.0",
        "file_path": "artifact-rules/netex-artifact-rules-v1.0.ttl",
        "graph_uri": "https://napcore.eu/graph/artifact-rules/netex/v1.0",
    },
    {
        "ontology_key": "opra-artifact-rules-v1.0",
        "file_path": "artifact-rules/opra-artifact-rules-v1.0.ttl",
        "graph_uri": "https://napcore.eu/graph/artifact-rules/opra/v1.0",
    },
    {
        "ontology_key": "siri-artifact-rules-v1.0",
        "file_path": "artifact-rules/siri-artifact-rules-v1.0.ttl",
        "graph_uri": "https://napcore.eu/graph/artifact-rules/siri/v1.0",
    },
    {
        "ontology_key": "datex-artifact-rules-v1.0",
        "file_path": "artifact-rules/datex-artifact-rules-v1.0.ttl",
        "graph_uri": "https://napcore.eu/graph/artifact-rules/datex/v1.0",
    },
]


def _ontology_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "ontology"


def _extract_version_info(content: str) -> str:
    match = re.search(r'owl:versionInfo\s+"([^"]+)"', content)
    if match:
        return match.group(1).strip()
    return "unknown"


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def collect_ontology_asset_versions() -> list[dict]:
    ontology_dir = _ontology_dir()
    items: list[dict] = []
    for spec in ONTOLOGY_SPECS:
        file_path = ontology_dir / spec["file_path"]
        if not file_path.exists():
            continue
        content = file_path.read_text(encoding="utf-8")
        items.append(
            {
                "ontology_key": spec["ontology_key"],
                "file_path": str(file_path),
                "graph_uri": spec["graph_uri"],
                "version": _extract_version_info(content),
                "content_hash": _content_hash(content),
            }
        )
    return items


def record_ontology_asset_versions(
    *,
    graphdb_repository: str = "",
    loaded: bool = False,
    loaded_ontology_keys: set[str] | None = None,
) -> list[OntologyAssetVersion]:
    recorded: list[OntologyAssetVersion] = []
    loaded_at = timezone.now() if loaded else None
    for item in collect_ontology_asset_versions():
        defaults = {
            "file_path": item["file_path"],
            "graph_uri": item["graph_uri"],
            "version": item["version"],
            "content_hash": item["content_hash"],
            "graphdb_repository": graphdb_repository,
        }
        if loaded and (
            loaded_ontology_keys is None or item["ontology_key"] in loaded_ontology_keys
        ):
            defaults["last_loaded_at"] = loaded_at
        record, _created = OntologyAssetVersion.objects.update_or_create(
            ontology_key=item["ontology_key"],
            defaults=defaults,
        )
        recorded.append(record)
    return recorded


def current_ontology_version_payload() -> list[dict]:
    records = list(OntologyAssetVersion.objects.all())
    if not records:
        return [
            {
                "ontologyKey": item["ontology_key"],
                "version": item["version"],
                "graphUri": item["graph_uri"],
                "contentHash": item["content_hash"],
            }
            for item in collect_ontology_asset_versions()
        ]

    return [
        {
            "ontologyKey": record.ontology_key,
            "version": record.version,
            "graphUri": record.graph_uri,
            "contentHash": record.content_hash,
        }
        for record in records
    ]
