#!/usr/bin/env python3

import argparse
import json
from urllib import request


QUESTION = "Show me a NeTEx XML example for a simple line with stop points."


def _post(base_url: str, path: str, payload: dict, headers: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = request.Request(f"{base_url}{path}", data=body, headers=req_headers, method="POST")
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_status(base_url: str, path: str) -> int:
    req = request.Request(f"{base_url}{path}", method="GET")
    with request.urlopen(req, timeout=15) as response:
        return response.status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run q070 regression assertions against local API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument(
        "--require-canonical-line-source",
        action="store_true",
        help="Fail if the canonical simple-line example is still missing from scoped citations.",
    )
    args = parser.parse_args()

    if _get_status(args.base_url, "/api/v1/health/live") != 200:
        print("FAIL: health endpoint is not ready.")
        return 1

    token_resp = _post(args.base_url, "/api/v1/auth/dev-token", {})
    token = token_resp.get("token")
    if not token:
        print("FAIL: dev token endpoint did not return token.")
        return 1

    unscoped = _post(
        args.base_url,
        "/api/v1/questions/answer",
        {"question": QUESTION},
        {
            "Authorization": f"Bearer {token}",
            "X-Request-Id": "q070-regression-unscoped-20260419",
        },
    )
    scoped = _post(
        args.base_url,
        "/api/v1/questions/answer",
        {"question": QUESTION, "standardsScope": ["NeTEx"]},
        {
            "Authorization": f"Bearer {token}",
            "X-Request-Id": "q070-regression-scoped-20260419",
        },
    )

    failures: list[str] = []
    warnings: list[str] = []

    if unscoped.get("mode") != "rag":
        failures.append(f"unscoped mode expected rag, got {unscoped.get('mode')}")
    if unscoped.get("abstained"):
        failures.append("unscoped expected abstained=false")
    if float(unscoped.get("confidence", 0.0)) < 0.90:
        failures.append(f"unscoped expected confidence >= 0.90, got {unscoped.get('confidence')}")
    if unscoped.get("trace", {}).get("semanticDisambiguationRequired") is not True:
        failures.append("unscoped expected semanticDisambiguationRequired=true")
    unscoped_core_concepts = unscoped.get("trace", {}).get("semanticQuery", {}).get("coreConcepts", [])
    if "nits:line" not in unscoped_core_concepts:
        failures.append(f"unscoped expected coreConcepts to include nits:line, got {unscoped_core_concepts}")

    if scoped.get("mode") != "rag":
        failures.append(f"scoped mode expected rag, got {scoped.get('mode')}")
    if scoped.get("abstained"):
        failures.append("scoped expected abstained=false")
    if float(scoped.get("confidence", 0.0)) < 0.90:
        failures.append(f"scoped expected confidence >= 0.90, got {scoped.get('confidence')}")
    scoped_candidate_standards = scoped.get("trace", {}).get("semanticQuery", {}).get("candidateStandards", [])
    if scoped_candidate_standards != ["NeTEx"]:
        failures.append(f"scoped expected candidateStandards=['NeTEx'], got {scoped_candidate_standards}")

    answer = scoped.get("answer", "")
    if "```xml" not in answer:
        failures.append("scoped answer should contain a fenced XML block")
    if "StopPlace" not in answer or "ScheduledStopPoint" not in answer or "StopAssignment" not in answer:
        failures.append("scoped answer should contain StopPlace, ScheduledStopPoint, and StopAssignment")

    citations = scoped.get("citations", [])
    if len(citations) < 3:
        failures.append(f"scoped expected at least 3 citations, got {len(citations)}")

    canonical_line_source = "examples/functions/line/NeTEx_01_simple_line.xml"
    scoped_source_paths = [citation.get("sourcePath", "") for citation in citations]
    if canonical_line_source not in scoped_source_paths:
        message = (
            "scoped citations still miss canonical simple-line source "
            f"{canonical_line_source}"
        )
        if args.require_canonical_line_source:
            failures.append(message)
        else:
            warnings.append(message)

    print("q070 regression summary:")
    print(
        "  unscoped:",
        f"mode={unscoped.get('mode')}",
        f"abstained={unscoped.get('abstained')}",
        f"confidence={unscoped.get('confidence')}",
        f"semanticDisambiguationRequired={unscoped.get('trace', {}).get('semanticDisambiguationRequired')}",
    )
    print(
        "  scoped:",
        f"mode={scoped.get('mode')}",
        f"abstained={scoped.get('abstained')}",
        f"confidence={scoped.get('confidence')}",
    )
    print("  scoped_top_citations:")
    for source_path in scoped_source_paths[:5]:
        print(f"    - {source_path}")

    if warnings:
        print("WARN:")
        for warning in warnings:
            print(f"  - {warning}")

    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS: q070 guardrail expectations satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
