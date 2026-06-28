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
    """Persist editorial queue item and return created model instance."""

    return EditorialQueueItem.objects.create(**payload)
