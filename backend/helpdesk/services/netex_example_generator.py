"""NeTEx XML fragments generated for a question, validated against the NeTEx XSD.

"Show an example of a bus with 50 seats and 20 standing places" has no verbatim answer in the NeTEx
examples. The model writes one frame from the elements in the evidence (schema definitions and real
examples), the frame is wrapped in a minimal PublicationDelivery and validated against
NeTEx_publication.xsd from the indexed NeTEx checkout, and validator errors go back to the model for
another attempt. Only a fragment that validates and contains the question's values is returned; it is
labelled as generated, never presented as an example from the standard.

XSD validity checks structure, not modelling choices: a valid fragment can still put a value on a
less usual element. The evidence it was built from is cited with it.
"""

from __future__ import annotations

import json
import logging
import re
import time

from django.conf import settings

logger = logging.getLogger(__name__)

SCHEMA_ENTRY = "xsd/NeTEx_publication.xsd"
MAX_ATTEMPTS = 3
MAX_EVIDENCE_CHUNKS = 6
MAX_EVIDENCE_CHARS = 1800
MAX_REPORTED_ERRORS = 5
VALIDATOR_TIMEOUT_SECONDS = 10

_EXAMPLE_WORDS = re.compile(r"\b(?:examples?|samples?|snippets?|fragments?|show\s+(?:me\s+)?(?:how|the\s+xml))\b", re.I)
_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")
# Straight or curly double quotes, in pairs; an apostrophe ("don't") is no quote.
_QUOTED = re.compile(r'"([^"]{1,60})"|“([^”]{1,60})”')
_XML_BLOCK = re.compile(r"<(?P<tag>[A-Za-z][\w.-]*)[\s>].*</(?P=tag)>", re.S)


def requested_values(question: str) -> list[str]:
    """The concrete values a question asks to see: numbers and quoted names."""
    values = [(straight or curly).strip() for straight, curly in _QUOTED.findall(question or "")]
    values += _NUMBER.findall(_QUOTED.sub(" ", question or ""))
    return list(dict.fromkeys(value for value in values if value))


def wants_generated_example(question: str, scope: list[str] | None) -> bool:
    """A request for a NeTEx example with concrete values ("a bus with 50 seats and 20 standing places")."""
    if not getattr(settings, "NETEX_EXAMPLE_GENERATOR_ENABLED", True):
        return False
    names = {(name or "").strip().lower() for name in scope or []}
    if "netex" not in names and "netex" not in (question or "").lower():
        return False
    return bool(_EXAMPLE_WORDS.search(question or "")) and bool(requested_values(question))


# --- validation (netex-validator service, helpdesk/netex_validator_service.py) -------------------


class ValidatorUnavailable(RuntimeError):
    pass


def validate_fragment(fragment: str) -> dict:
    """{"valid", "errors", "schemaVersion", "commit"} from the validation service."""
    from urllib import error, request

    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/validate"
    body = json.dumps({"fragment": fragment}).encode("utf-8")
    http_request = request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(http_request, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except error.HTTPError as exc:
        raise ValidatorUnavailable(f"validator answered {exc.code}") from exc
    except (error.URLError, OSError, ValueError) as exc:
        raise ValidatorUnavailable(f"validator unreachable: {exc}") from exc


NETEX_NAMESPACE = "http://www.netex.org.uk/netex"


def _indented(xml: str) -> str:
    """The XML indented two spaces per level. Only for validated fragments: a DOCTYPE inside the
    wrapper makes the document malformed, so these hold no DTD or entities."""
    from xml.dom import minidom

    try:
        pretty = minidom.parseString(xml.encode("utf-8")).toprettyxml(indent="  ")
    except Exception:
        return xml
    lines = [line for line in pretty.splitlines() if line.strip()]
    return "\n".join(lines[1:] if lines and lines[0].startswith("<?xml") else lines)


def indented_fragment(fragment: str) -> str:
    """The frame indented, without a namespace declaration of its own (it sits inside dataObjects)."""
    lines = _indented(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>').splitlines()
    if len(lines) < 3 or not lines[0].startswith("<root"):
        return fragment.strip()
    return "\n".join(line[2:] if line.startswith("  ") else line for line in lines[1:-1])


def publication_document(fragment: str) -> str:
    """The validated document: a minimal PublicationDelivery around the frame (as the validator wraps it)."""
    from helpdesk.netex_validator_service import wrap_fragment

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + _indented(wrap_fragment(fragment)) + "\n"


def missing_values(fragment: str, values: list[str]) -> list[str]:
    """Requested values that appear nowhere in the fragment's text or attributes."""
    return [value for value in values if not re.search(rf"(?<![\w.]){re.escape(value)}(?![\w.])", fragment)]


# --- generation ----------------------------------------------------------------------------------

_PROMPT = (
    "You write NeTEx XML for a standards helpdesk. Write ONE NeTEx frame (for example a ResourceFrame, "
    "ServiceFrame, SiteFrame or TimetableFrame, with version and id attributes) that shows what the question "
    "asks, using the values it gives. Put each object in the frame the evidence examples put it in (vehicle "
    "types, for example, in a ResourceFrame). Use only element and attribute names that appear in the evidence blocks "
    "(schema definitions and example files), in the order the schema definitions give. Give every element that "
    "needs one a version and an id; use the prefix 'hd:' for ids. Do not add elements the question does not "
    "need. The frame goes inside <dataObjects> of a PublicationDelivery; do not write the PublicationDelivery, "
    "an XML declaration or namespace declarations.\n"
    'Return ONLY JSON: {"xml": "<...Frame ...>...</...Frame>"}'
)


def _evidence_text(chunks: list[dict]) -> tuple[str, list[dict]]:
    used = [chunk for chunk in chunks if "netex" in str(chunk.get("repositoryUrl", "")).lower()][:MAX_EVIDENCE_CHUNKS]
    blocks = [
        f"[E{index}] source={chunk.get('sourcePath', '')}\n{str(chunk.get('text', ''))[:MAX_EVIDENCE_CHARS]}"
        for index, chunk in enumerate(used, start=1)
    ]
    return "\n\n".join(blocks), used


def _extract_fragment(content: str) -> str:
    try:
        payload = json.loads(content)
        if isinstance(payload, dict) and isinstance(payload.get("xml"), str):
            return payload["xml"].strip()
    except (ValueError, TypeError):
        pass
    match = _XML_BLOCK.search(content or "")
    return match.group(0).strip() if match else ""


def _ask_model(messages: list[dict]) -> str:
    from helpdesk.services.llm_generator import _request_chat_completion
    from helpdesk.services.llm_options import answer_max_tokens

    response = _request_chat_completion(
        api_base_url=(settings.LLM_API_BASE_URL or "").strip(),
        api_key=(settings.LLM_API_KEY or "").strip(),
        model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        temperature=0.0,
        max_tokens=answer_max_tokens(1600),
        messages=messages,
    )
    return str(response["choices"][0]["message"]["content"] or "")


def generate_netex_example(question: str, chunks: list[dict], scope: list[str] | None = None) -> dict | None:
    """A validated NeTEx fragment for the question, or a record of why there is none.

    Returns None when the question does not ask for one. Otherwise a dict with valid (bool), attempts,
    and, when valid, xml, schema, schemaVersion and evidenceChunkIds; when not valid, errors.
    """
    if not wants_generated_example(question, scope):
        return None
    if not getattr(settings, "LLM_ENABLED", False):
        return None
    evidence, used = _evidence_text(chunks)
    if not used:
        return {"valid": False, "attempts": 0, "errors": ["no NeTEx evidence to build the example from"]}
    values = requested_values(question)
    messages = [
        {"role": "system", "content": _PROMPT},
        {"role": "user", "content": f"Question:\n{question}\n\nValues to use: {', '.join(values)}\n\nEVIDENCE BLOCKS:\n{evidence}"},
    ]
    errors: list[str] = []
    # Time spent waiting for the model and for the validator, so the validator's share of an answer's
    # latency shows in the trace.
    timing = {"generationMs": 0, "validationMs": 0}

    def timed(key: str, call):
        started = time.perf_counter()
        try:
            return call()
        finally:
            timing[key] += round((time.perf_counter() - started) * 1000)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            content = timed("generationMs", lambda: _ask_model(messages))
        except Exception as exc:
            logger.warning("NeTEx example generation failed: %s", exc)
            return {"valid": False, "attempts": attempt, "errors": [f"generation failed: {exc}"[:200]], **timing}
        fragment = _extract_fragment(content)
        checked: dict = {}
        if not fragment:
            errors = ["the reply contained no XML frame"]
        else:
            try:
                checked = timed("validationMs", lambda: validate_fragment(fragment))
            except ValidatorUnavailable as exc:
                logger.warning("NeTEx example not validated: %s", exc)
                return {"valid": False, "attempts": attempt, "errors": [str(exc)[:200]], **timing}
            errors = list(checked.get("errors") or [])
            if checked.get("valid") and not errors:
                errors = [f"the value {value} from the question is missing" for value in missing_values(fragment, values)]
        if not errors:
            return {
                "valid": True,
                "attempts": attempt,
                "xml": indented_fragment(fragment),
                "document": publication_document(fragment),
                "schema": SCHEMA_ENTRY,
                "schemaVersion": checked.get("schemaVersion", ""),
                "schemaCommit": checked.get("commit", ""),
                "evidenceChunkIds": [chunk.get("chunkId") for chunk in used],
                **timing,
            }
        messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": "The frame is not valid NeTEx:\n- " + "\n- ".join(errors)
                + "\nFix these errors and return the whole frame again as JSON {\"xml\": \"...\"}.",
            },
        ]
    return {"valid": False, "attempts": MAX_ATTEMPTS, "errors": errors, **timing}
