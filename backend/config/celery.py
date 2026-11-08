import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("napcore_helpdesk")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


from celery.signals import worker_ready  # noqa: E402


@worker_ready.connect
def _build_concept_vectors_on_start(sender=None, **kwargs):
    """Bring the concept vectors in line with the ontology after a deploy; a minute later, so the embedder
    and GraphDB are up. Only new and changed classes are embedded (seconds when nothing changed)."""
    sender.app.send_task("helpdesk.build_concept_vectors", countdown=60)
