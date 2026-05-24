from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from helpdesk.services.semantic_clustering import build_semantic_clusters


class Command(BaseCommand):
    help = "Run semantic clustering over recent question events and print JSON summary."

    def add_arguments(self, parser):
        parser.add_argument("--window-days", type=int, default=30)
        parser.add_argument("--min-cluster-size", type=int, default=2)
        parser.add_argument("--similarity-threshold", type=float, default=0.82)
        parser.add_argument("--max-events", type=int, default=500)

    def handle(self, *args, **options):
        result = build_semantic_clusters(
            window_days=options["window_days"],
            min_cluster_size=options["min_cluster_size"],
            similarity_threshold=options["similarity_threshold"],
            max_events=options["max_events"],
        )
        self.stdout.write(json.dumps(result, indent=2))
