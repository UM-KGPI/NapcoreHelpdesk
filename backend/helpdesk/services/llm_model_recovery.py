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

import json
import logging
import re
import ssl
import threading
from urllib import error, request

logger = logging.getLogger(__name__)

# Timeout for the live "list models" probe used by the LLM status endpoint --
# deliberately short and independent of LLM_TIMEOUT_SECONDS (which sizes full
# generation calls): this is a diagnostic check, not an answer request, and
# should stay responsive even if the gateway is slow or down.
_STATUS_PROBE_TIMEOUT_SECONDS = 6

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

# Separate from _corrected_model_cache: records (base_url, configured_model)
# pairs the live gateway probe has already confirmed are fine, so
# resolve_effective_model() doesn't re-probe on every call once resolved.
# Kept apart from the correction cache so get_cached_correction() /
# get_all_corrections() -- and the /health/llm endpoint's "autoCorrected"
# field -- stay true to their name: they answer "was this corrected", not
# "was this ever checked".
_verified_ok_cache: set[tuple[str, str]] = set()


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


def get_all_corrections() -> dict[tuple[str, str], str]:
    """Return a snapshot of every (base_url, configured_model) -> corrected_model discovered so far.

    Used by the LLM status endpoint to report whether self-healing has already
    fired for this process, independent of the live gateway probe below.
    """
    with _cache_lock:
        return dict(_corrected_model_cache)


def _build_ssl_context(*, verify_ssl: bool, ca_bundle: str) -> ssl.SSLContext:
    if not verify_ssl:
        return ssl._create_unverified_context()
    context = ssl.create_default_context()
    if ca_bundle:
        context.load_verify_locations(cafile=ca_bundle)
    return context


def check_gateway_models(
    *,
    api_base_url: str,
    api_key: str,
    verify_ssl: bool,
    ca_bundle: str,
) -> dict:
    """Live-probe the gateway's OpenAI-compatible GET /models endpoint.

    Returns {"reachable": bool, "modelIds": list[str] | None, "error": str | None}.
    A free, read-only call (no completion tokens billed) used to check gateway
    reachability and the current model allowlist without generating an answer.
    """
    url = api_base_url.rstrip("/") + "/models"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = request.Request(url, method="GET", headers=headers)
    try:
        with request.urlopen(
            req,
            timeout=_STATUS_PROBE_TIMEOUT_SECONDS,
            context=_build_ssl_context(verify_ssl=verify_ssl, ca_bundle=ca_bundle),
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return {"reachable": False, "modelIds": None, "error": f"HTTP {exc.code}: {detail[:300]}"}
    except (error.URLError, TimeoutError, OSError) as exc:
        return {"reachable": False, "modelIds": None, "error": str(exc)}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"reachable": True, "modelIds": None, "error": f"unparseable response body: {exc}"}

    model_ids = [entry.get("id") for entry in body.get("data", []) if isinstance(entry, dict) and entry.get("id")]
    return {"reachable": True, "modelIds": model_ids, "error": None}


def resolve_effective_model(
    *,
    api_base_url: str,
    api_key: str,
    configured_model: str,
    verify_ssl: bool,
    ca_bundle: str,
    source: str,
) -> str:
    """Return the model a call should use, resolving drift proactively via check_gateway_models().

    Reuses the same live /models probe the /health/llm endpoint calls, so the
    self-heal and the status API share one source of truth for "is the
    configured model actually authorized" instead of the self-heal only ever
    finding out reactively from a failed completion call.

    Fast paths (no network call) once a (base_url, configured_model) pair has
    been resolved once in this process: a previously discovered correction,
    or a previous live confirmation that the configured model is fine.
    Otherwise probes the gateway once; if the probe fails or the result is
    ambiguous (configured model missing from an allowlist of more than one),
    this returns the configured model unchanged and leaves correction to the
    existing reactive 403 handler at the call site, which has the gateway's
    own authoritative error to go on.
    """
    cached_correction = get_cached_correction(api_base_url, configured_model)
    if cached_correction:
        return cached_correction

    key = (api_base_url.strip(), configured_model.strip())
    with _cache_lock:
        if key in _verified_ok_cache:
            return configured_model

    probe = check_gateway_models(api_base_url=api_base_url, api_key=api_key, verify_ssl=verify_ssl, ca_bundle=ca_bundle)
    if not probe["reachable"] or probe["modelIds"] is None:
        # Preflight couldn't confirm anything either way -- proceed with the
        # configured model rather than block the real call on it; the
        # reactive 403 handler remains the safety net if it's actually wrong.
        return configured_model

    model_ids = probe["modelIds"]
    if configured_model in model_ids:
        with _cache_lock:
            _verified_ok_cache.add(key)
        return configured_model

    if len(model_ids) == 1 and model_ids[0] != configured_model:
        remember_correction(
            api_base_url=api_base_url,
            configured_model=configured_model,
            corrected_model=model_ids[0],
            source=f"{source}_preflight",
        )
        return model_ids[0]

    # Configured model isn't authorized and the allowlist has zero or several
    # entries -- can't safely guess which one replaces it. Leave it to the
    # reactive path, which reads the gateway's own "key can only access
    # models=[...]" error instead of guessing from this list.
    return configured_model
