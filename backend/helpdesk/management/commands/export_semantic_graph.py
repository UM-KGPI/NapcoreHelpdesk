from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.models import SourceChunk
from helpdesk.services.semantic_graph import build_semantic_graph_snapshot


class Command(BaseCommand):
    help = "Export a semantic graph snapshot from indexed SourceChunk records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            required=True,
            help="Path to output JSON file (for bootstrap import into graph databases).",
        )
        parser.add_argument(
            "--repo-url",
            default="",
            help="Optional repository URL filter (e.g., https://github.com/OpRa-CEN/OpRa).",
        )
        parser.add_argument(
            "--min-quality",
            type=float,
            default=0.0,
            help="Optional minimum chunk quality score included in export (0.0-1.0).",
        )

    def handle(self, *args, **options):
        output = Path(options["output"]).expanduser().resolve()
        repo_url = (options.get("repo_url") or "").strip()
        min_quality = float(options.get("min_quality", 0.0))

        if min_quality < 0.0 or min_quality > 1.0:
            raise CommandError("--min-quality must be between 0.0 and 1.0")

        queryset = SourceChunk.objects.all().order_by("chunk_id")
        if repo_url:
            queryset = queryset.filter(repository_url=repo_url)
        if min_quality > 0.0:
            queryset = queryset.filter(quality_score__gte=min_quality)

        snapshot = build_semantic_graph_snapshot(queryset)
        snapshot["meta"] = {
            "repositoryUrl": repo_url or "all",
            "minQuality": min_quality,
            "chunkCountScanned": queryset.count(),
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS("Semantic graph export completed."))
        self.stdout.write(f"output={output}")
        self.stdout.write(f"repository_url={snapshot['meta']['repositoryUrl']}")
        self.stdout.write(f"chunk_count_scanned={snapshot['meta']['chunkCountScanned']}")
        self.stdout.write(f"concept_nodes={snapshot['stats']['conceptNodeCount']}")
        self.stdout.write(f"chunk_nodes={snapshot['stats']['chunkNodeCount']}")
        self.stdout.write(f"mention_edges={snapshot['stats']['mentionEdgeCount']}")
        self.stdout.write(f"related_edges={snapshot['stats']['relatedEdgeCount']}")
