"""
NeTEx validation service.

One process compiles NeTEx_publication.xsd from the indexed NeTEx checkout (about 20 s and 170 MB,
2026-11-08) and validates XML fragments for the backend's example generator
(services/netex_example_generator.py), so the schema is not loaded in every gunicorn worker and the
model-written XML is parsed outside the backend process.

    GET  /health    -> {"status": "ok" | "loading" | "error", "schemaVersion": "2.0", "commit": "...", ...}
    POST /validate  {"fragment": "<ResourceFrame ...>...</ResourceFrame>"}
                    -> {"valid": bool, "errors": ["line 3: ...", ...], "schemaVersion": "2.0", "commit": "..."}

A fragment is one NeTEx frame; it is wrapped in a minimal PublicationDelivery before validation, and
error line numbers count from the fragment's first line. Every CHECK_SECONDS the service compares the
checkout's commit with the loaded one; after a source refresh it compiles the new schema in the
background and keeps answering with the old one until then.

Run with: python -m helpdesk.netex_validator_service  (no Django needed). Settings: NETEX_VALIDATOR_*.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-08  |  Modified: 2026-11-08
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

NETEX_NAMESPACE = "http://www.netex.org.uk/netex"
CHECKOUT = Path(os.environ.get("NETEX_VALIDATOR_CHECKOUT", "/app/repos/NeTEx"))
SCHEMA_ENTRY = "xsd/NeTEx_publication.xsd"
CHECK_SECONDS = int(os.environ.get("NETEX_VALIDATOR_CHECK_SECONDS", "300"))
MAX_FRAGMENT_BYTES = 200_000
MAX_ERRORS = 5

logger = logging.getLogger("netex_validator_service")

_WRAPPER_HEAD = (
    f'<PublicationDelivery xmlns="{NETEX_NAMESPACE}" version="1.0">\n'
    "<PublicationTimestamp>{timestamp}</PublicationTimestamp>\n"
    "<ParticipantRef>NAPCORE-Helpdesk</ParticipantRef>\n"
    "<dataObjects>\n"
)
_WRAPPER_TAIL = "\n</dataObjects>\n</PublicationDelivery>\n"


def wrap_fragment(fragment: str) -> str:
    """A PublicationDelivery around one frame, with the NeTEx namespace as default namespace."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return _WRAPPER_HEAD.replace("{timestamp}", timestamp) + fragment.strip() + _WRAPPER_TAIL


def checkout_commit(checkout: Path = CHECKOUT) -> str:
    """The checkout's HEAD commit, read from .git without running git."""
    git = checkout / ".git"
    try:
        head = (git / "HEAD").read_text().strip()
        if not head.startswith("ref: "):
            return head
        ref = head[5:]
        ref_file = git / ref
        if ref_file.exists():
            return ref_file.read_text().strip()
        for line in (git / "packed-refs").read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split(" ", 1)[0]
    except OSError:
        pass
    return ""


def schema_version(checkout: Path = CHECKOUT) -> str:
    try:
        head = (checkout / SCHEMA_ENTRY).read_text(encoding="utf-8", errors="ignore")[:4000]
    except OSError:
        return ""
    match = re.search(r"<xsd:schema\b[^>]*\bversion=\"([^\"]+)\"", head)
    return match.group(1) if match else ""


def _parser():
    from lxml import etree

    # Model-written XML: no entity expansion, no DTD, no network.
    return etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False)


class SchemaHolder:
    """The compiled schema of the checkout's current commit; recompiled in the background when it moves."""

    def __init__(self, checkout: Path = CHECKOUT):
        self.checkout = checkout
        self.schema = None
        self.commit = ""
        self.version = ""
        self.error = ""
        self.loaded_at = ""
        self._loading = False
        self._lock = threading.Lock()
        # schema.error_log belongs to the schema object: one validation at a time (about 20 ms each).
        self._validate_lock = threading.Lock()
        self._checked = 0.0

    def load(self) -> None:
        from lxml import etree

        commit = checkout_commit(self.checkout)
        started = time.time()
        try:
            schema = etree.XMLSchema(etree.parse(str(self.checkout / SCHEMA_ENTRY)))
        except Exception as exc:  # missing checkout or a broken schema: keep the previous one
            self.error = str(exc)[:300]
            logger.warning("NeTEx schema not compiled: %s", exc)
        else:
            self.schema, self.commit, self.version, self.error = schema, commit, schema_version(self.checkout), ""
            self.loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            logger.info("NeTEx schema %s at %s compiled in %.1f s", self.version, commit[:12], time.time() - started)
        finally:
            self._loading = False

    def reload_if_moved(self) -> None:
        """Start a background recompile when the checkout's commit differs from the loaded one."""
        if time.time() - self._checked < CHECK_SECONDS:
            return
        self._checked = time.time()
        with self._lock:
            if self._loading or checkout_commit(self.checkout) == self.commit:
                return
            self._loading = True
        threading.Thread(target=self.load, name="netex-schema-reload", daemon=True).start()

    def status(self) -> dict:
        state = "ok" if self.schema is not None else ("error" if self.error else "loading")
        return {"status": state, "schemaVersion": self.version, "commit": self.commit, "loadedAt": self.loaded_at,
                "error": self.error, "reloading": self._loading}

    def validate(self, fragment: str) -> dict:
        from lxml import etree

        schema = self.schema
        if schema is None:
            raise RuntimeError("schema not loaded")
        offset = _WRAPPER_HEAD.count("\n")
        result = {"schemaVersion": self.version, "commit": self.commit}
        try:
            document = etree.fromstring(wrap_fragment(fragment).encode("utf-8"), parser=_parser())
        except etree.XMLSyntaxError as exc:
            return {**result, "valid": False, "errors": [f"Not well-formed XML: {exc}"]}
        with self._validate_lock:
            if schema.validate(document):
                return {**result, "valid": True, "errors": []}
            errors = [
                f"line {max(1, error.line - offset)}: {error.message.replace('{' + NETEX_NAMESPACE + '}', '')}"
                for error in schema.error_log
            ]
        return {**result, "valid": False, "errors": errors[:MAX_ERRORS]}


def make_handler(holder: SchemaHolder):
    class Handler(BaseHTTPRequestHandler):
        def _reply(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path != "/health":
                self._reply(404, {"error": "not found"})
                return
            holder.reload_if_moved()
            status = holder.status()
            self._reply(200 if status["status"] == "ok" else 503, status)

        def do_POST(self):  # noqa: N802
            if self.path != "/validate":
                self._reply(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length > MAX_FRAGMENT_BYTES:
                self._reply(413, {"error": f"at most {MAX_FRAGMENT_BYTES} bytes"})
                return
            try:
                fragment = json.loads(self.rfile.read(length) or b"{}").get("fragment")
                if not isinstance(fragment, str) or not fragment.strip():
                    raise ValueError('expected {"fragment": "<...Frame>...</...Frame>"}')
            except (ValueError, AttributeError, json.JSONDecodeError) as exc:
                self._reply(400, {"error": str(exc)})
                return
            holder.reload_if_moved()
            try:
                self._reply(200, holder.validate(fragment))
            except RuntimeError as exc:
                self._reply(503, {"error": str(exc), **holder.status()})

        def log_message(self, fmt, *args):
            logger.info("%s %s", self.address_string(), fmt % args)

    return Handler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    port = int(os.environ.get("NETEX_VALIDATOR_PORT", "8091"))
    holder = SchemaHolder()
    holder._loading = True
    threading.Thread(target=holder.load, name="netex-schema-load", daemon=True).start()
    logger.info("listening on port %s; compiling %s", port, CHECKOUT / SCHEMA_ENTRY)
    # Threads so /health answers while the schema compiles; validations take turns (_validate_lock).
    ThreadingHTTPServer(("0.0.0.0", port), make_handler(holder)).serve_forever()


if __name__ == "__main__":
    main()
