"""Warm retrieval after a start: have the database read the vector index before users ask.

Usage: python manage.py warm_retrieval
The first question after a deploy took 77 s on prod (2026-11-09), 55 s of it in the vector query: the
ivfflat index (~1 GB) was read from disk on first use; warm, the same query takes 0.3 s. This runs in its own
process, so it warms the database's pages, not the caches inside each web worker. deploy.sh runs it once
after the migrations; a failure only prints, and the deploy goes on.
"""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

# One general question per core standard and one without a scope, so each scope's rows of the index are read.
WARM_QUESTIONS = (
    ("What is a StopPlace in NeTEx?", ["NeTEx"]),
    ("How does SIRI describe a vehicle monitoring message?", ["SIRI"]),
    ("How is a vehicle journey modelled in OpRa?", ["OpRa"]),
    ("What is a journey pattern in Transmodel?", ["Transmodel"]),
    ("Which standards describe public transport timetables?", None),
)


class Command(BaseCommand):
    help = "Run a few retrievals so the first user question after a start is not the one that reads the index."

    def handle(self, *args, **options):
        for question, scope in WARM_QUESTIONS:
            started = time.perf_counter()
            try:
                retrieve_chunks_with_trace(
                    question=question, top_k=6, min_score=0.62, scope=scope, graph_rag_enabled=True, min_results=3,
                    english_question=None,
                )
            except Exception as exc:  # a warm-up must never fail a deploy
                self.stdout.write(f"warm-up failed for {scope}: {exc}")
                continue
            self.stdout.write(f"warmed {scope or 'all'}: {time.perf_counter() - started:.1f} s")
