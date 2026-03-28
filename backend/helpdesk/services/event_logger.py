from __future__ import annotations

from helpdesk.models import QuestionEvent


def log_question_event(payload: dict) -> QuestionEvent:
    """Persist a question event and return the created model instance."""

    return QuestionEvent.objects.create(**payload)
