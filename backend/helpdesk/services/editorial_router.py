"""
Routes accepted question events into the editorial review queue.

Creates an EditorialQueueItem with status in_review (the entry point for
the workflow state machine in editorial_workflow.py). Routing the same
question_event_id twice is rejected to prevent duplicate queue entries.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

from helpdesk.models import EditorialQueueItem


def route_to_editorial_queue(payload: dict) -> EditorialQueueItem:
    """Persist editorial queue item and return created model instance.

    Raises IntegrityError if an item already exists for this question_event_id.
    """
    question_event_id = payload["question_event"].id

    if EditorialQueueItem.objects.filter(question_event_id=question_event_id).exists():
        # Return existing item instead of creating duplicate
        return EditorialQueueItem.objects.get(question_event_id=question_event_id)

    return EditorialQueueItem.objects.create(**payload)
