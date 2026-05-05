from __future__ import annotations

from dataclasses import dataclass
import json
import re
import subprocess

from django.conf import settings


class ControllerLLMError(Exception):
    """Raised when controller decisioning cannot be completed safely."""


@dataclass(frozen=True)
class ControllerDecision:
    route: str
    intent: str
    confidence: float


_JSON_OBJECT_PATTERN = re.compile(r"\{[\s\S]*\}")
_ALLOWED_ROUTES = {"faq", "rag"}


def _extract_json_payload(text: str) -> dict:
    """Extract a JSON object from mixed llama-cli output (logs + model text)."""

    candidate = ""
    for match in _JSON_OBJECT_PATTERN.findall(text or ""):
        if '"route"' in match and '"confidence"' in match:
            candidate = match
    if not candidate:
        raise ControllerLLMError("Controller output did not include a valid JSON payload.")

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ControllerLLMError("Controller JSON payload could not be parsed.") from exc

    return payload


def _validate_payload(payload: dict) -> ControllerDecision:
    route = str(payload.get("route", "")).strip().lower()
    if route not in _ALLOWED_ROUTES:
        raise ControllerLLMError("Controller route must be 'faq' or 'rag'.")

    intent = str(payload.get("intent", "unknown")).strip() or "unknown"

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError) as exc:
        raise ControllerLLMError("Controller confidence must be numeric.") from exc

    confidence = max(0.0, min(1.0, confidence))
    return ControllerDecision(route=route, intent=intent, confidence=confidence)


def _build_prompt(question: str, requested_scope: list[str], semantic_query: dict | None = None) -> str:
    scope_text = ", ".join(requested_scope) if requested_scope else "unspecified"
    semantic_text = json.dumps(semantic_query or {}, ensure_ascii=True)

    return (
        "You are a controller for a standards helpdesk pipeline. "
        "Choose route='faq' only when the question likely matches a stable canonical FAQ intent. "
        "Choose route='rag' for specific, novel, cross-standard, implementation-detail, or ambiguous requests. "
        "Return ONLY strict JSON with this schema: "
        '{"route":"faq|rag","intent":"short_intent_label","confidence":0.0}. '\
        "Do not include markdown, explanations, or extra keys.\n\n"
        f"Question: {question}\n"
        f"RequestedScope: {scope_text}\n"
        f"SemanticQuery: {semantic_text}\n"
    )


def decide_route_with_controller_llm(
    *,
    question: str,
    requested_scope: list[str],
    semantic_query: dict | None = None,
) -> ControllerDecision | None:
    """Return FAQ/RAG route from local controller model when enabled."""

    if not getattr(settings, "CONTROLLER_LLM_ENABLED", False):
        return None

    executable = getattr(settings, "CONTROLLER_LLM_EXECUTABLE", "").strip()
    model_path = getattr(settings, "CONTROLLER_LLM_MODEL_PATH", "").strip()
    if not executable or not model_path:
        raise ControllerLLMError("Controller LLM executable/model path is not configured.")

    command = [
        executable,
        "--device",
        getattr(settings, "CONTROLLER_LLM_DEVICE", "none"),
        "-m",
        model_path,
        "-c",
        str(getattr(settings, "CONTROLLER_LLM_CTX_SIZE", 2048)),
        "-n",
        str(getattr(settings, "CONTROLLER_LLM_MAX_TOKENS", 96)),
        "-t",
        str(getattr(settings, "CONTROLLER_LLM_THREADS", 8)),
        "--temp",
        str(getattr(settings, "CONTROLLER_LLM_TEMPERATURE", 0.0)),
        "--reasoning",
        "off",
        "-p",
        _build_prompt(question=question, requested_scope=requested_scope, semantic_query=semantic_query),
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=int(getattr(settings, "CONTROLLER_LLM_TIMEOUT_SECONDS", 20)),
        )
    except subprocess.TimeoutExpired as exc:
        raise ControllerLLMError("Controller LLM timed out.") from exc
    except FileNotFoundError as exc:
        raise ControllerLLMError("Controller LLM executable was not found.") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or "").strip()
        raise ControllerLLMError(f"Controller LLM failed: {message[:400]}") from exc

    mixed_output = "\n".join([result.stdout or "", result.stderr or ""]).strip()
    payload = _extract_json_payload(mixed_output)
    return _validate_payload(payload)
