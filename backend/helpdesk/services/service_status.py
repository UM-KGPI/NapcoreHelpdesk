"""Whether the Helpdesk is slower than usual right now, and why: shown to users as a banner.

Two signals, both read without touching the work they describe:

- Indexing: an index or re-embedding command is running in this container (deploy.sh starts them here with
  `docker compose exec`). Found by reading process command lines under /proc, not by probing the commands'
  lock files: a probe that takes a lock, however briefly, can make a command that starts at that moment exit
  with "already running".
- Load: the host's 1-minute load average per CPU. Retrieval is CPU-bound, so answers slow down once the host
  is saturated, whatever the cause (an index run, the nightly refresh in the Celery worker, something outside
  the Helpdesk). A container sees the host's load average and CPU count.

On a system without /proc (macOS development) the indexing signal is simply never raised.
"""

from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings

# Management commands that embed many chunks. Answers stay correct while they run, only slower.
INDEXING_COMMANDS = {
    "index_regulations": "EU legislation",
    "index_napcore_site": "napcore.eu",
    "index_inspire": "INSPIRE",
    "index_datex": "DATEX II",
    "refresh_source_indexes": "standards repositories",
    "reembed_chunks": "search index",
    "build_source_index": "standards repositories",
}


def running_index_sources(proc_root: Path = Path("/proc")) -> list[str]:
    """Names of the sources being indexed by commands running in this container, in a stable order."""
    if not proc_root.is_dir():
        return []
    found: set[str] = set()
    own_pid = str(os.getpid())
    for entry in proc_root.iterdir():
        if not entry.name.isdigit() or entry.name == own_pid:
            continue
        try:
            argv = (entry / "cmdline").read_bytes().split(b"\0")
        except OSError:  # the process ended while we looked, or is not ours to read
            continue
        args = [part.decode("utf-8", "replace") for part in argv if part]
        if not any(arg.endswith("manage.py") for arg in args):
            continue
        for arg in args:
            if arg in INDEXING_COMMANDS:
                found.add(INDEXING_COMMANDS[arg])
    return sorted(found)


def load_per_cpu() -> float | None:
    """The 1-minute load average divided by the CPU count, or None where the platform has no load average."""
    try:
        one_minute, _, _ = os.getloadavg()
    except (AttributeError, OSError):
        return None
    return one_minute / (os.cpu_count() or 1)


def current_status() -> dict:
    """{"state": "ok" | "busy", "reasons": [...]}; each reason has a code the frontend turns into a message."""
    reasons: list[dict] = []
    sources = running_index_sources()
    if sources:
        reasons.append({"code": "indexing", "sources": sources})
    load = load_per_cpu()
    if load is not None and load >= settings.STATUS_BUSY_LOAD_PER_CPU:
        reasons.append({"code": "high_load"})
    return {"state": "busy" if reasons else "ok", "reasons": reasons}
