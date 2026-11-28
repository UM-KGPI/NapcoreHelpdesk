"""Celery Beat schedule, kept free of Django imports so it can be unit-tested."""

from __future__ import annotations

from celery.schedules import crontab


def build_beat_schedule(*, refresh_enabled: bool, hour: int, minute: int) -> dict:
    """The daily source refresh is scheduled only when it is switched on."""

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"SOURCE_REFRESH_HOUR/MINUTE out of range: {hour}:{minute}")
    schedule: dict = {}
    if refresh_enabled:
        schedule["helpdesk-refresh-source-indexes-daily"] = {
            "task": "helpdesk.refresh_source_indexes",
            "schedule": crontab(hour=hour, minute=minute),
        }
    return schedule
