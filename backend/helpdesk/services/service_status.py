"""Whether the Helpdesk is slower than usual right now, and why: shown to users as a banner.

Two signals, both read without touching the work they describe:

- Indexing: an index or re-embedding command is running in this container (deploy.sh starts them here with
  `docker compose exec`). Found by reading process command lines under /proc, not by probing the commands'
  lock files: a probe that takes a lock, however briefly, can make a command that starts at that moment exit
  with "already running". The source commands deploy.sh runs on every deploy (MARKED_COMMANDS) count only
  once they start embedding (mark_embedding): when nothing changed they only compare file hashes, which slows
  nothing down, and the banner would otherwise appear for minutes after every deploy.
- Load: the host's 1-minute load average per CPU. Retrieval is CPU-bound, so answers slow down once the host
  is saturated, whatever the cause (an index run, the nightly refresh in the Celery worker, something outside
  the Helpdesk). A container sees the host's load average and CPU count.

On a system without /proc (macOS development) the indexing signal is simply never raised.
"""

from __future__ import annotations

import atexit
import os
import tempfile
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


# Run on every deploy and usually find nothing to do; reported only after mark_embedding().
MARKED_COMMANDS = frozenset({"index_regulations", "index_napcore_site", "index_inspire", "index_datex"})
MARKER_DIR = Path(tempfile.gettempdir())
MARKER_PREFIX = "helpdesk-embedding-"


def mark_embedding() -> None:
    """Record that this process has started embedding content. Called by the index services before each embedding
    batch; cheap after the first call. The marker is removed when the process exits. A killed process leaves it
    behind, but its PID is then gone from /proc, so it is never reported."""
    marker = MARKER_DIR / f"{MARKER_PREFIX}{os.getpid()}"
    if marker.exists():
        return
    try:
        marker.write_text("")
    except OSError:  # the banner is a hint; never fail an index run over it
        return
    atexit.register(marker.unlink, missing_ok=True)


def running_index_sources(proc_root: Path = Path("/proc"), marker_dir: Path | None = None) -> list[str]:
    """Names of the sources being indexed by commands running in this container, in a stable order."""
    if not proc_root.is_dir():
        return []
    marker_dir = MARKER_DIR if marker_dir is None else marker_dir
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
            if arg not in INDEXING_COMMANDS:
                continue
            if arg in MARKED_COMMANDS and not (marker_dir / f"{MARKER_PREFIX}{entry.name}").exists():
                continue  # comparing hashes only, nothing to embed (yet)
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
