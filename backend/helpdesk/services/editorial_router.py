from __future__ import annotations

from helpdesk.models import EditorialQueueItem


def route_to_editorial_queue(payload: dict) -> EditorialQueueItem:
    """Persist editorial queue item and return created model instance."""

    return EditorialQueueItem.objects.create(**payload)
