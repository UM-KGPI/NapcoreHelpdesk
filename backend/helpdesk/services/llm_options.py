"""
Optional OpenAI-compatible request fields, switched per endpoint in settings.

Some gateways reject fields that others need. A vLLM/LiteLLM gateway serving a reasoning model (Qwen)
needs `chat_template_kwargs` to switch thinking off, and accepts JSON mode and streaming. A managed
model-as-a-service endpoint (SLAIF MaaS, 2026-11-04) answers HTTP 400 `unsupported_option` to all
three. These helpers build the optional part of a request from the LLM_* settings (answer
generation) or the CONTROLLER_LLM_* settings (routing, vocabulary bridge, relevance check).

When thinking cannot be switched off, a reasoning model spends part of max_tokens on reasoning
before it writes the answer, so the reasoning allowance is added to every token budget.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-04  |  Modified: 2026-11-04
"""

from __future__ import annotations

from django.conf import settings


def _options(*, json_mode: bool, disable_thinking: bool) -> dict:
    options: dict = {}
    if json_mode:
        options["response_format"] = {"type": "json_object"}
    if disable_thinking:
        options["chat_template_kwargs"] = {"enable_thinking": False}
    return options


def answer_request_options() -> dict:
    """Optional fields for answer generation requests (LLM_JSON_MODE, LLM_DISABLE_THINKING)."""

    return _options(json_mode=settings.LLM_JSON_MODE, disable_thinking=settings.LLM_DISABLE_THINKING)


def controller_request_options(*, json_mode: bool = True) -> dict:
    """Optional fields for controller-endpoint requests. json_mode=False for calls that expect plain text."""

    return _options(
        json_mode=json_mode and settings.CONTROLLER_LLM_JSON_MODE,
        disable_thinking=settings.CONTROLLER_LLM_DISABLE_THINKING,
    )


def answer_max_tokens(base: int) -> int:
    return int(base) + int(settings.LLM_REASONING_TOKEN_ALLOWANCE)


def controller_max_tokens(base: int) -> int:
    return int(base) + int(settings.CONTROLLER_LLM_REASONING_TOKEN_ALLOWANCE)
