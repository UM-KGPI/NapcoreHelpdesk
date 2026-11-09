"""
Anthropic (Claude) provider for the helpdesk's chat calls, through the official `anthropic` SDK.

The rest of the backend builds OpenAI-style chat requests (a `messages` list with system/user/assistant
roles) and reads OpenAI-style responses (`choices[0].message.content`). When LLM_PROVIDER or
CONTROLLER_LLM_PROVIDER is "anthropic", the request builders hand their messages to `chat_completion`
here, which calls the Messages API and returns the same response shape, so callers stay unchanged.

Differences from the OpenAI-compatible gateways that this module absorbs:
- System prompts go in the top-level `system` field, and turns must alternate user/assistant.
- No `temperature`: current Claude models reject sampling parameters.
- Thinking cannot be switched off on every model (Claude Opus 5.5); `output_config.effort` sets how much
  the model thinks (LLM_ANTHROPIC_EFFORT, CONTROLLER_LLM_ANTHROPIC_EFFORT), and thinking tokens count
  towards max_tokens (see LLM_REASONING_TOKEN_ALLOWANCE).
- JSON answers are asked for in the prompt, as with the plain gateways; a reply wrapped in a ```json
  fence is unwrapped here.
- A `refusal` stop reason is raised as an error, so callers fall back as for any failed call.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-04  |  Modified: 2026-11-09
"""

from __future__ import annotations

import re
from functools import lru_cache

import anthropic

PROVIDER = "anthropic"
_FENCED_JSON = re.compile(r"^\s*```(?:json)?\s*\n(.*?)\n?\s*```\s*$", re.DOTALL)


class AnthropicRequestError(Exception):
    """An Anthropic API call failed, timed out, or the model declined it."""


@lru_cache(maxsize=4)
def _client(api_key: str) -> anthropic.Anthropic:
    # One client per key: it keeps the HTTP connection pool between calls.
    return anthropic.Anthropic(api_key=api_key or None)


def to_messages_api(messages: list[dict]) -> tuple[str, list[dict]]:
    """Split OpenAI-style messages into (system text, alternating user/assistant turns)."""

    system_parts: list[str] = []
    turns: list[dict] = []
    for message in messages:
        role = message.get("role")
        content = str(message.get("content") or "")
        if role == "system":
            system_parts.append(content)
            continue
        role = "assistant" if role == "assistant" else "user"
        if turns and turns[-1]["role"] == role:
            turns[-1]["content"] += "\n\n" + content
        else:
            turns.append({"role": role, "content": content})
    if not turns or turns[0]["role"] != "user":
        turns.insert(0, {"role": "user", "content": "Follow the instructions above."})
    if turns[-1]["role"] != "user":
        # The Messages API rejects a trailing assistant turn (prefill) on current models.
        turns.append({"role": "user", "content": "Continue."})
    return "\n\n".join(part for part in system_parts if part), turns


def unwrap_json_fence(text: str) -> str:
    match = _FENCED_JSON.match(text)
    return match.group(1).strip() if match else text


def chat_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    timeout_seconds: float,
    effort: str = "low",
    json_answer: bool = False,
    thinking: str = "adaptive",
) -> dict:
    """Call the Messages API and return an OpenAI-shaped payload: {"choices": [{"message": {"content"}}], ...}.

    thinking="adaptive" leaves thinking to the model (its default); "disabled" answers without thinking.
    """

    system, turns = to_messages_api(messages)
    params: dict = {
        "model": model,
        "max_tokens": int(max_tokens),
        "messages": turns,
        "output_config": {"effort": effort},
    }
    if system:
        params["system"] = system
    if thinking == "disabled":
        params["thinking"] = {"type": "disabled"}
    try:
        response = _client(api_key).with_options(timeout=timeout_seconds, max_retries=1).messages.create(**params)
    except anthropic.APIStatusError as exc:
        raise AnthropicRequestError(f"Anthropic API error {exc.status_code}: {str(exc)[:300]}") from exc
    except anthropic.APIConnectionError as exc:  # includes timeouts
        raise AnthropicRequestError(f"Anthropic API request failed: {exc}") from exc

    if response.stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        category = getattr(details, "category", None) if details else None
        raise AnthropicRequestError(f"Anthropic model declined the request (refusal, category={category}).")

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if json_answer:
        text = unwrap_json_fence(text)
    return {
        "model": response.model,
        "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": response.stop_reason}],
        "usage": {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
        },
    }


def check_models(*, api_key: str) -> dict:
    """Health probe in check_gateway_models' shape: a free GET /v1/models listing the key's models."""

    try:
        model_ids = [model.id for model in _client(api_key).with_options(timeout=5.0, max_retries=0).models.list()]
    except anthropic.APIStatusError as exc:
        return {"reachable": False, "modelIds": None, "error": f"HTTP {exc.status_code}: {str(exc)[:300]}"}
    except anthropic.APIConnectionError as exc:
        return {"reachable": False, "modelIds": None, "error": str(exc)}
    return {"reachable": True, "modelIds": model_ids, "error": None}
