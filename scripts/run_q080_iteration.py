#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from urllib import request


QUESTION = "How does OpRa service intensity relate to NeTEx line and network concepts?"


def _post(base_url: str, path: str, payload: dict, headers: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = request.Request(f"{base_url}{path}", data=body, headers=req_headers, method="POST")
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run q080 iteration and write artifacts")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--out-unscoped",
        default="docs/testing/q080-e2e-artifact-rerun-tuned.json",
    )
    parser.add_argument(
        "--out-scoped",
        default="docs/testing/q080-e2e-artifact-scoped-rerun-tuned.json",
    )
    args = parser.parse_args()

    token_resp = _post(args.base_url, "/api/v1/auth/dev-token", {})
    token = token_resp.get("token")

    common_headers = {"Authorization": f"Bearer {token}"}

    unscoped = _post(
        args.base_url,
        "/api/v1/questions/answer",
        {"question": QUESTION},
        {
            **common_headers,
            "X-Request-Id": "q080-e2e-rerun-tuned-unscoped-20260419",
        },
    )

    scoped = _post(
        args.base_url,
        "/api/v1/questions/answer",
        {"question": QUESTION, "standardsScope": ["OpRa", "NeTEx"]},
        {
            **common_headers,
            "X-Request-Id": "q080-e2e-rerun-tuned-scoped-20260419",
        },
    )

    Path(args.out_unscoped).write_text(json.dumps(unscoped, ensure_ascii=False), encoding="utf-8")
    Path(args.out_scoped).write_text(json.dumps(scoped, ensure_ascii=False), encoding="utf-8")

    print("q080 tuning run summary:")
    print(
        "  unscoped:",
        f"mode={unscoped.get('mode')}",
        f"confidence={unscoped.get('confidence')}",
        f"abstained={unscoped.get('abstained')}",
        f"concepts={unscoped.get('trace', {}).get('graphConceptIds', [])}",
    )
    print(
        "  scoped:",
        f"mode={scoped.get('mode')}",
        f"confidence={scoped.get('confidence')}",
        f"abstained={scoped.get('abstained')}",
        f"concepts={scoped.get('trace', {}).get('graphConceptIds', [])}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
