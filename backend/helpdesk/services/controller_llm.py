from __future__ import annotations

from dataclasses import dataclass
import json
import re
import ssl
import subprocess
from urllib import error, request

from django.conf import settings


class ControllerLLMError(Exception):
    """Raised when controller decisioning cannot be completed safely."""


@dataclass(frozen=True)
class ControllerDecision:
    route: str
    intent: str
    confidence: float


_JSON_OBJECT_PATTERN = re.compile(r"\{[\s\S]*?\}")
_ALLOWED_ROUTES = {"faq", "rag"}


def _extract_json_payload(text: str) -> dict:
    """Extract a JSON object from mixed llama-cli output (logs + model text)."""

    candidate_payload: dict | None = None
    for match in _JSON_OBJECT_PATTERN.findall(text or ""):
        if '"route"' not in match or '"confidence"' not in match:
            continue
        try:
            parsed = json.loads(match)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidate_payload = parsed

    if candidate_payload is None:
        raise ControllerLLMError("Controller output did not include a valid JSON payload.")

    return candidate_payload


def _build_ssl_context() -> ssl.SSLContext:
    if not getattr(settings, "CONTROLLER_LLM_VERIFY_SSL", True):
        return ssl._create_unverified_context()

    context = ssl.create_default_context()
    ca_bundle = getattr(settings, "CONTROLLER_LLM_CA_BUNDLE", "").strip()
    if ca_bundle:
        context.load_verify_locations(cafile=ca_bundle)
    return context


def _validate_payload(payload: dict) -> ControllerDecision:
    route = str(payload.get("route", "")).strip().lower()
    if route not in _ALLOWED_ROUTES:
        has_faq = "faq" in route
        has_rag = "rag" in route
        if has_rag and not has_faq:
            route = "rag"
        elif has_faq and not has_rag:
            route = "faq"
        elif has_faq and has_rag:
            # Ambiguous placeholder outputs (for example "faq|rag") default to safer RAG path.
            route = "rag"

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


def _decide_via_http(*, question: str, requested_scope: list[str], semantic_query: dict | None = None) -> ControllerDecision:
    base_url = getattr(settings, "CONTROLLER_LLM_API_BASE_URL", "").strip()
    model = getattr(settings, "CONTROLLER_LLM_API_MODEL", "").strip()
    if not base_url or not model:
        raise ControllerLLMError("Controller HTTP provider requires base URL and model.")

    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": _build_prompt(
                    question=question,
                    requested_scope=requested_scope,
                    semantic_query=semantic_query,
                ),
            }
        ],
        "temperature": float(getattr(settings, "CONTROLLER_LLM_TEMPERATURE", 0.0)),
        "max_tokens": int(getattr(settings, "CONTROLLER_LLM_MAX_TOKENS", 96)),
    }

    headers = {"Content-Type": "application/json"}
    api_key = getattr(settings, "CONTROLLER_LLM_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )

    try:
        with request.urlopen(
            req,
            timeout=int(getattr(settings, "CONTROLLER_LLM_TIMEOUT_SECONDS", 20)),
            context=_build_ssl_context(),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = f"Controller HTTP error: {exc.code}"
        raise ControllerLLMError(detail) from exc
    except Exception as exc:
        raise ControllerLLMError(f"Controller HTTP request failed: {exc}") from exc

    choices = payload.get("choices") or []
    if not choices:
        raise ControllerLLMError("Controller HTTP response has no choices.")

    message = choices[0].get("message", {})
    content = str(message.get("content") or "").strip()
    if not content:
        raise ControllerLLMError("Controller HTTP response was empty.")

    decision_payload = _extract_json_payload(content)
    return _validate_payload(decision_payload)


def decide_route_with_controller_llm(
    *,
    question: str,
    requested_scope: list[str],
    semantic_query: dict | None = None,
) -> ControllerDecision | None:
    """Return FAQ/RAG route from local controller model when enabled."""

    if not getattr(settings, "CONTROLLER_LLM_ENABLED", False):
        return None

    provider = getattr(settings, "CONTROLLER_LLM_PROVIDER", "subprocess").strip().lower() or "subprocess"
    if provider == "openai-compatible":
        return _decide_via_http(
            question=question,
            requested_scope=requested_scope,
            semantic_query=semantic_query,
        )

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
        "--simple-io",
        "-no-cnv",
        "-st",
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
    except OSError as exc:
        raise ControllerLLMError(f"Controller LLM executable error: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or "").strip()
        raise ControllerLLMError(f"Controller LLM failed: {message[:400]}") from exc

    mixed_output = "\n".join([result.stdout or "", result.stderr or ""]).strip()
    payload = _extract_json_payload(mixed_output)
    return _validate_payload(payload)
