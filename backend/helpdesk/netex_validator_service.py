"""
NeTEx validation service.

One process compiles NeTEx_publication.xsd from the indexed NeTEx checkout (about 20 s and 170 MB,
2026-11-08) and validates XML fragments for the backend's example generator
(services/netex_example_generator.py), so the schema is not loaded in every gunicorn worker and the
model-written XML is parsed outside the backend process.

    GET  /health    -> {"status": "ok" | "loading" | "error", "schemaVersion": "2.0", "commit": "...", ...}
    POST /validate  {"fragment": "<ResourceFrame ...>...</ResourceFrame>"}
                    -> {"valid": bool, "errors": ["line 3: ...", ...], "schemaVersion": "2.0", "commit": "...",
                        "elements": [{"name": "SeatingCapacity", "parent": "PassengerCapacity",
                                      "documentation": "The seating capacity of vehicles of the type. ..."}]}

A fragment is one NeTEx frame; it is wrapped in a minimal PublicationDelivery before validation, and
error line numbers count from the fragment's first line. For a valid fragment, "elements" gives each
element's xsd:documentation from the schema (ElementDocs), so the generated example can be explained
from the standard's own words without a model. Every CHECK_SECONDS the service compares the
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
MAX_ELEMENT_NOTES = 40
XSD_NS = "http://www.w3.org/2001/XMLSchema"
_WRAPPER_ELEMENTS = frozenset({"PublicationDelivery", "PublicationTimestamp", "ParticipantRef", "dataObjects"})

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


def _local(name: str | None) -> str:
    """'netex:VehicleTypeGroup' or '{ns}Quay' -> 'VehicleTypeGroup' / 'Quay'."""
    name = name or ""
    return name.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _first_sentence(text: str) -> str:
    match = re.match(r"(.+?[.!?])(?:\s|$)", text)
    return match.group(1) if match else text


class ElementDocs:
    """The xsd:documentation of each element, chosen through the parent element's type.

    NeTEx documents an element where it is declared, inside a named complexType, group or global
    element (the "container"); the same name is declared in several containers with different text
    (SeatingCapacity under CapacityGroup and under VehicleManoeuvringRequirementCapacityGroup). A
    fragment element's parent names its type; the type's base types and group references, followed
    transitively, are the containers the element can be declared in. The note for an element is the
    text from a container reached that way, else the global element's own text, else the text all
    declarations agree on (first sentence), else none.
    """

    def __init__(self) -> None:
        self.docs: dict[str, list[tuple[str, str]]] = {}  # element name -> [(container, documentation)]
        self.element_type: dict[str, str] = {}  # element name -> type name; a global declaration wins
        self.links: dict[str, set[str]] = {}  # container -> base types and groups it uses
        self.files = 0

    @staticmethod
    def _container(node) -> str:
        """The nearest named complexType, group or element above the node ("" at schema level)."""
        parent = node.getparent()
        while parent is not None:
            if _local(parent.tag) in {"complexType", "group", "element"} and parent.get("name"):
                return parent.get("name")
            parent = parent.getparent()
        return ""

    def add_schema(self, root) -> None:
        self.files += 1
        for node in root.iter(f"{{{XSD_NS}}}element"):
            name = node.get("name")
            if not name:
                continue
            documentation = " ".join(
                " ".join((doc.text or "").split())
                for doc in node.findall(f"{{{XSD_NS}}}annotation/{{{XSD_NS}}}documentation")
            ).strip()
            if documentation:
                self.docs.setdefault(name, []).append((self._container(node), documentation))
            is_global = _local(node.getparent().tag) == "schema"
            type_name = _local(node.get("type")) or name  # anonymous content: the element is its own container
            if is_global or name not in self.element_type:
                self.element_type[name] = type_name
        for tag in ("extension", "restriction"):
            for node in root.iter(f"{{{XSD_NS}}}{tag}"):
                if node.get("base"):
                    self.links.setdefault(self._container(node), set()).add(_local(node.get("base")))
        for node in root.iter(f"{{{XSD_NS}}}group"):
            if node.get("ref"):
                self.links.setdefault(self._container(node), set()).add(_local(node.get("ref")))

    def load_directory(self, directory: Path) -> None:
        from lxml import etree

        for path in sorted(directory.rglob("*.xsd")):
            try:
                self.add_schema(etree.parse(str(path), parser=_parser()).getroot())
            except (etree.XMLSyntaxError, OSError) as exc:
                logger.warning("element documentation: %s skipped: %s", path.name, exc)

    def _containers_of(self, parent: str) -> dict[str, int]:
        """Containers the parent's content can come from, with their distance along the type chain."""
        reached: dict[str, int] = {}
        pending = [(parent, 0), (self.element_type.get(parent, ""), 0)]
        while pending:
            container, distance = pending.pop(0)
            if container and container not in reached:
                reached[container] = distance
                pending.extend((linked, distance + 1) for linked in self.links.get(container, ()))
        return reached

    def documentation(self, name: str, parent: str) -> str:
        candidates = self.docs.get(name) or []
        if not candidates:
            return ""
        reachable = self._containers_of(parent)
        nearest = min((reachable[c], text) for c, text in candidates if c in reachable) if any(c in reachable for c, _ in candidates) else None
        if nearest:
            return nearest[1]
        for container, text in candidates:
            if container == "":
                return text
        sentences = {_first_sentence(text) for _, text in candidates}
        return sentences.pop() if len(sentences) == 1 else ""

    def notes(self, document) -> list[dict]:
        """One note per distinct element and parent of the document, in document order."""
        notes, seen = [], set()
        for node in document.iter():
            if not isinstance(node.tag, str):
                continue
            name = _local(node.tag)
            parent_node = node.getparent()
            parent = _local(parent_node.tag) if parent_node is not None else ""
            if name in _WRAPPER_ELEMENTS or (name, parent) in seen:
                continue
            seen.add((name, parent))
            text = self.documentation(name, parent)
            if text:
                notes.append({"name": name, "parent": parent, "documentation": text})
            if len(notes) >= MAX_ELEMENT_NOTES:
                break
        return notes


class SchemaHolder:
    """The compiled schema of the checkout's current commit; recompiled in the background when it moves."""

    def __init__(self, checkout: Path = CHECKOUT):
        self.checkout = checkout
        self.schema = None
        self.element_docs = ElementDocs()
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
            element_docs = ElementDocs()
            element_docs.load_directory((self.checkout / SCHEMA_ENTRY).parent)
        except Exception as exc:  # missing checkout or a broken schema: keep the previous one
            self.error = str(exc)[:300]
            logger.warning("NeTEx schema not compiled: %s", exc)
        else:
            self.schema, self.element_docs = schema, element_docs
            self.commit, self.version, self.error = commit, schema_version(self.checkout), ""
            self.loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            logger.info(
                "NeTEx schema %s at %s compiled in %.1f s; documentation of %d elements from %d files",
                self.version, commit[:12], time.time() - started, len(element_docs.docs), element_docs.files,
            )
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
                return {**result, "valid": True, "errors": [], "elements": self.element_docs.notes(document)}
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
