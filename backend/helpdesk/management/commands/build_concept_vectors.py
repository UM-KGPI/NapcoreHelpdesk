"""Build or update the ontology's concept vectors (services/concept_vectors.py).

Usage: python manage.py build_concept_vectors
Re-embeds only classes whose label, other labels or definition changed; needs GraphDB and the embedder.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from helpdesk.services.concept_vectors import build_concept_vectors


class Command(BaseCommand):
    help = "Embed the ontology's classes for finding them by meaning (only new and changed classes)."

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(build_concept_vectors()))
