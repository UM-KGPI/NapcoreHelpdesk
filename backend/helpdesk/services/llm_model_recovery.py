"""
Self-heals from LLM gateway model-alias drift.

The shared litellm gateway (https://litellm.lhrs.si) has twice rescoped which
model alias its API key is authorized for, without notice: once against dev
(qwen36-35b-a3b -> nvidia/Qwen3.6-35B-A3B-NVFP4, discovered 2026-09-21) and,
because production's `.env.prod` is a separate file on the server that
nothing in this repo can reach, the same break persisted in production after
the dev fix landed until it was reported separately.

When the configured model is wrong, the gateway's own 403 response body names
the model the key IS authorized for (litellm's `key_model_access_denied`
error). Rather than let every answer-generation or routing call fail until a
human notices and hand-edits the environment config, parse that name out of
the error, retry once with the corrected model, and cache the correction for
the rest of the process so subsequent calls skip straight to it. Always logs
loudly (WARNING on first discovery) -- this is a live workaround to keep the
app answering, not a substitute for fixing LLM_MODEL / CONTROLLER_LLM_API_MODEL
in the environment.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-09-21
"""

from __future__ import annotations

import logging
import re
import threading

logger = logging.getLogger(__name__)

# litellm's key_model_access_denied error body looks like:
#   {"error":{"message":"key not allowed to access model. This key can only
#   access models=['nvidia/Qwen3.6-35B-A3B-NVFP4']. Tried to access ...",
#   "type":"key_model_access_denied", ...}}
_MODEL_ACCESS_DENIED_RE = re.compile(r"can only access models=\[['\"]([^'\"]+)['\"]")

_cache_lock = threading.Lock()
# Per-process only (no shared cache backend is configured -- see settings.py,
# CACHES is unset, so Django's default is also per-process LocMemCache; a
# plain dict here is equivalent, not a regression). Each worker process
# discovers the correction independently on its own first affected call,
# which still self-heals correctly, just without cross-worker sharing.
_corrected_model_cache: dict[tuple[str, str], str] = {}


def extract_authorized_model(error_body: str) -> str | None:
    """Parse the model name a litellm 403 key_model_access_denied body says the key IS authorized for."""
    if not error_body:
        return None
    match = _MODEL_ACCESS_DENIED_RE.search(error_body)
    return match.group(1) if match else None


def get_cached_correction(api_base_url: str, configured_model: str) -> str | None:
    """Return a previously-discovered correction for this (base_url, configured_model), if any."""
    return _corrected_model_cache.get((api_base_url.strip(), configured_model.strip()))


def remember_correction(*, api_base_url: str, configured_model: str, corrected_model: str, source: str) -> None:
    """Cache a discovered model correction and log it -- WARNING the first time, INFO on repeats."""
    key = (api_base_url.strip(), configured_model.strip())
    with _cache_lock:
        is_new = _corrected_model_cache.get(key) != corrected_model
        _corrected_model_cache[key] = corrected_model

    log = logger.warning if is_new else logger.info
    log(
        "LLM_MODEL_AUTO_CORRECTED (%s): configured model '%s' at %s was rejected (403 "
        "key_model_access_denied); the gateway says the key is authorized for '%s' "
        "instead. Using the corrected model for this request. This is a live workaround, "
        "not a fix -- update the model setting in the environment config to '%s' to avoid "
        "this detour on every call.",
        source,
        configured_model,
        api_base_url,
        corrected_model,
        corrected_model,
    )
