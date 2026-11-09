"""Where an answer's time went, stored in its question event's trace (timingsMs).

Prod could not be profiled without a session on the server: the stored trace had retrievalLatencyMs fixed
at 0.0 (docs/plans/2026-11-09-example-question-latency.md, P0). An answer endpoint starts a record for its
request; question parsing, every retrieval call and every model call add their milliseconds (and counts)
to it. The record lives in a context variable, so code that runs outside a request adds nothing.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-09  |  Modified: 2026-11-09
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar

_TIMINGS: ContextVar[dict | None] = ContextVar("request_timings", default=None)


def start() -> dict:
    """A new, empty record for the current request (and its thread)."""
    record: dict = {"_started": time.perf_counter()}
    _TIMINGS.set(record)
    return record


def add(key: str, milliseconds: float, count_key: str | None = None) -> None:
    record = _TIMINGS.get()
    if record is None:
        return
    record[key] = round(record.get(key, 0.0) + milliseconds, 1)
    if count_key:
        record[count_key] = record.get(count_key, 0) + 1


@contextmanager
def timed(key: str, count_key: str | None = None):
    started = time.perf_counter()
    try:
        yield
    finally:
        add(key, (time.perf_counter() - started) * 1000, count_key)


def snapshot() -> dict:
    """The record so far, with totalMs since start(); {} outside a request."""
    record = _TIMINGS.get()
    if record is None:
        return {}
    result = {k: v for k, v in record.items() if not k.startswith("_")}
    result["totalMs"] = round((time.perf_counter() - record["_started"]) * 1000, 1)
    return result
