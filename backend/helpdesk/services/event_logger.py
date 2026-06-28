"""
Persists question orchestration outcomes as QuestionEvent records.

Called at the end of every answer request to record the question text,
selected mode, confidence, generated answer, citations, and the review_required
flag used to surface candidates for editorial triage.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

from helpdesk.models import QuestionEvent


def log_question_event(payload: dict) -> QuestionEvent:
    """Persist a question event and return the created model instance."""

    return QuestionEvent.objects.create(**payload)
