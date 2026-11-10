"""
NeTEx validation service.

One process compiles NeTEx_publication.xsd from the indexed NeTEx checkout (about 20 s and 170 MB,
2026-11-08) and validates XML fragments for the backend's example generator
(services/netex_example_generator.py), so the schema is not loaded in every gunicorn worker and the
model-written XML is parsed outside the backend process.

    GET  /health    -> {"status": "ok" | "loading" | "error", "schemaVersion": "2.0", "commit": "...", ...}
    GET  /declarations?q=coach+seat+wheelchair+area&c=seat+wheelchair   (c: words that follow a number)
                    -> {"declarations": [{"name": "SeatingCapacity", "parents": ["PassengerCapacity"],
                                          "documentation": "The seating capacity of vehicles of the type. ..."}]}
                    element declarations whose name or documentation contains the words, best first: the
                    generator's evidence for the elements a question needs, independent of text retrieval.
    GET  /structure?element=StopPlace
                    -> {"found": true, "element": "StopPlace", "documentation": "...", "source": "xsd/...xsd",
                        "groups": [{"owner": "StopPlace", "inherited": false, "children": [{"name", "documentation"}]},
                                   {"owner": "Site", "inherited": true, "children": [...]}, ...],
                        "attributes": [{"name": "id", "documentation": "Identifier of STOP PLACE.", "owner": "StopPlace"}]}
                    what the element contains according to the schema: its own child elements first, then
                    those inherited from each base type, and its attributes. Grounded by construction.
    POST /validate  {"fragment": "<ResourceFrame ...>...</ResourceFrame>"}
                    -> {"valid": bool, "errors": ["line 3: ...", ...], "schemaVersion": "2.0", "commit": "...",
                        "elements": [{"name": "SeatingCapacity", "parent": "PassengerCapacity",
                                      "documentation": "The seating capacity of vehicles of the type. ..."}],
                        "diagnostics": [{"line": 3, "element": "FarePrice", "parent": "prices", "kind": "abstract",
                                         "detail": "`FarePrice` is abstract ... concrete elements: ..."}]}
                    diagnostics (invalid fragments only): what is wrong in terms a model can act on, from the
                    schema's content models (helpdesk/netex_content_model.py): abstract, undeclared,
                    wrong-parent, order, missing-required, min-count, keyref, not-expected.

A fragment is one NeTEx frame; it is wrapped in a minimal PublicationDelivery before validation, and
error line numbers count from the fragment's first line. For a valid fragment, "elements" gives each
element's xsd:documentation from the schema (ElementDocs), so the generated example can be explained
from the standard's own words without a model. Every CHECK_SECONDS the service compares the
checkout's commit with the loaded one; after a source refresh it compiles the new schema in the
background and keeps answering with the old one until then.

Run with: python -m helpdesk.netex_validator_service  (no Django needed). Settings: NETEX_VALIDATOR_*.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-08  |  Modified: 2026-11-10
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
from urllib.parse import parse_qs, urlparse

NETEX_NAMESPACE = "http://www.netex.org.uk/netex"
CHECKOUT = Path(os.environ.get("NETEX_VALIDATOR_CHECKOUT", "/app/repos/NeTEx"))
SCHEMA_ENTRY = "xsd/NeTEx_publication.xsd"
CHECK_SECONDS = int(os.environ.get("NETEX_VALIDATOR_CHECK_SECONDS", "300"))
MAX_FRAGMENT_BYTES = 200_000
MAX_ERRORS = 5
MAX_DIAGNOSTICS = 6
MAX_ELEMENT_NOTES = 40
MAX_DECLARATIONS = 20
MAX_PARENT_DECLARATIONS = 15
MAX_PARENTS = 12  # alphabetical; PassengerCapacity has eleven, VehicleType among the last
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
        self.refs: dict[str, set[str]] = {}  # global element name -> containers that reference it
        self.parents: dict[str, set[str]] = {}  # container -> elements whose content comes from it
        self.attrs: dict[str, list[tuple[str, str]]] = {}  # container -> [(attribute name, documentation)]
        self.base: dict[str, str] = {}  # container -> the type it extends or restricts
        self.children: dict[str, list[str]] = {}  # container -> element names declared in it, in order
        self.sources: dict[str, str] = {}  # element name -> schema file of its first declaration
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

    @staticmethod
    def _documentation(node) -> str:
        return " ".join(
            " ".join((doc.text or "").split()) for doc in node.findall(f"{{{XSD_NS}}}annotation/{{{XSD_NS}}}documentation")
        ).strip()

    def add_schema(self, root, source: str = "") -> None:
        self.files += 1
        for node in root.iter(f"{{{XSD_NS}}}element"):
            name = node.get("name")
            if not name:
                if node.get("ref"):
                    container = self._container(node)
                    self.refs.setdefault(_local(node.get("ref")), set()).add(container)
                    self.children.setdefault(container, []).append(_local(node.get("ref")))
                continue
            container = self._container(node)
            self.children.setdefault(container, []).append(name)
            self.sources.setdefault(name, source)
            documentation = self._documentation(node)
            if documentation:
                self.docs.setdefault(name, []).append((container, documentation))
            is_global = _local(node.getparent().tag) == "schema"
            type_name = _local(node.get("type")) or name  # anonymous content: the element is its own container
            if is_global or name not in self.element_type:
                self.element_type[name] = type_name
        for tag in ("extension", "restriction"):
            for node in root.iter(f"{{{XSD_NS}}}{tag}"):
                if node.get("base"):
                    container = self._container(node)
                    self.links.setdefault(container, set()).add(_local(node.get("base")))
                    self.base.setdefault(container, _local(node.get("base")))
        for tag in ("group", "attributeGroup"):
            for node in root.iter(f"{{{XSD_NS}}}{tag}"):
                if node.get("ref"):
                    self.links.setdefault(self._container(node), set()).add(_local(node.get("ref")))
        for node in root.iter(f"{{{XSD_NS}}}attribute"):
            if node.get("name"):
                parent = node.getparent()
                # An attribute of a named attributeGroup belongs to that group; _container skips it otherwise.
                container = parent.get("name") if _local(parent.tag) == "attributeGroup" and parent.get("name") else self._container(node)
                self.attrs.setdefault(container, []).append((node.get("name"), self._documentation(node)))

    def load_directory(self, directory: Path) -> None:
        from lxml import etree

        for path in sorted(directory.rglob("*.xsd")):
            try:
                root = etree.parse(str(path), parser=_parser()).getroot()
            except (etree.XMLSyntaxError, OSError) as exc:
                logger.warning("element documentation: %s skipped: %s", path.name, exc)
                continue
            self.add_schema(root, source=str(path.relative_to(directory.parent)))
        self.index_parents()

    _OWNER_SUFFIXES = ("_VersionedChildStructure", "_VersionStructure", "Structure")

    def _owner_of(self, container: str, current: str) -> str:
        """The element a container's declarations belong to: a type name gives it (Site_VersionStructure ->
        Site); a group keeps the owner of the type that referenced it."""
        for suffix in self._OWNER_SUFFIXES:
            if container.endswith(suffix) and len(container) > len(suffix):
                return container[: -len(suffix)].rstrip("_")
        return current

    def structure(self, element: str) -> dict:
        """What the element contains according to the schema: child elements by owner (its own first, then
        each base type's), and attributes. {"found": False} for an unknown element."""
        if element not in self.element_type and element not in self.docs:
            return {"found": False, "element": element}
        groups: dict[str, list[dict]] = {}
        attributes: list[dict] = []
        seen_children: set[str] = set()
        reached: set[str] = set()

        def walk(start: str) -> None:
            pending = [(start, element)]
            while pending:
                container, owner = pending.pop(0)
                if not container or container in reached:
                    continue
                reached.add(container)
                owner = self._owner_of(container, owner)
                for child in self.children.get(container, ()):
                    if child not in seen_children:
                        seen_children.add(child)
                        groups.setdefault(owner, []).append(
                            {"name": child, "documentation": self.documentation(child, element)}
                        )
                for name, text in self.attrs.get(container, ()):
                    if not any(a["name"] == name for a in attributes):
                        attributes.append({"name": name, "documentation": text, "owner": owner})
                pending.extend((linked, owner) for linked in self.links.get(container, ()))

        # The type chain first: each group is owned by the type that references it (Site_VersionStructure
        # -> SiteGroup -> Site). A NeTEx global element has no type attribute: it restricts its
        # StopPlace_VersionStructure inline, repeating every inherited group; walked second, those are
        # already seen, so only genuinely own content is added.
        type_name = self.element_type.get(element, "")
        if not type_name or type_name == element:
            type_name = self.base.get(element, "")
        if type_name and type_name != element:
            walk(type_name)
        walk(element)
        global_text = next((t for c, t in self.docs.get(element, []) if c == ""), None)
        documentation = global_text or (self.docs.get(element) or [("", "")])[0][1]
        ordered = sorted(groups.items(), key=lambda item: item[0] != element)  # own first, then as met
        return {
            "found": True,
            "element": element,
            "documentation": documentation,
            "source": self.sources.get(element, ""),
            "groups": [
                {"owner": owner, "inherited": owner != element, "children": children}
                for owner, children in ordered
                if children
            ],
            "attributes": attributes,
        }

    def index_parents(self) -> None:
        """For each container, the elements whose content comes from it: the possible parents of the
        elements declared there (CapacityGroup -> PassengerCapacity)."""
        self.parents = {}
        for element in self.element_type:
            for container in self._containers_of(element):
                self.parents.setdefault(container, set()).add(element)

    def _parents_of(self, name: str, container: str) -> list[str]:
        containers = {container} if container else self.refs.get(name, set())
        found = {parent for c in containers for parent in self.parents.get(c, ())} - {name}
        return sorted(found)[:MAX_PARENTS]

    def is_object(self, name: str) -> bool:
        """Whether the element is an object of its own (a versioned entity with an id: LiftEquipment, Quay)
        rather than a property (ReachedFloorAnnouncement, Name)."""
        type_name = self.element_type.get(name, "")
        if not type_name or type_name == name:
            type_name = self.base.get(name, "")
        return type_name.endswith(("_VersionStructure", "_VersionedChildStructure"))

    def _is_count(self, name: str) -> bool:
        """Whether the element holds a number (its type: NumberOfPassengers, xsd:integer, ...)."""
        type_name = self.element_type.get(name, "").lower()
        return any(part in type_name for part in ("number", "integer", "count", "capacity", "decimal", "quantity"))

    def search(self, words: list[str], counted: list[str] = (), limit: int = MAX_DECLARATIONS) -> list[dict]:
        """Declarations whose name or documentation contains the words (lower-cased substrings).

        Each word gets its own best matches (so "wheelchair area" compounds cannot crowd out
        SeatingCapacity), merged best first. A word in the name counts double; a declaration with known
        parents beats one without; for a `counted` word (one that follows a number in the question:
        "49 seats") an element that holds a number counts extra. {"name", "parents", "documentation"}.
        """
        stems = [word.lower() for word in words if len(word) >= 4]
        if not stems:
            return []
        per_word = max(4, limit // max(1, len(stems)) + 2)
        ranked: dict[tuple[str, str], tuple[tuple, list[str]]] = {}
        for stem in stems:
            matches = []
            for name, declarations in self.docs.items():
                in_name = stem in name.lower()
                for container, text in declarations:
                    score = (2 if in_name else 0) + (1 if stem in text.lower() else 0)
                    if not score:
                        continue
                    if stem in counted and self._is_count(name):
                        score += 2
                    parents = self._parents_of(name, container)
                    matches.append(((-score, 0 if parents else 1, len(text)), name, container, text, parents))
            matches.sort(key=lambda match: match[0])
            for key, name, container, text, parents in matches[:per_word]:
                current = ranked.get((name, container))
                if current is None or key < current[0]:
                    ranked[(name, container)] = (key, [name, container, text, parents])
        ordered = sorted(ranked.values(), key=lambda item: item[0])[:limit]
        results = [
            {"name": name, "parents": parents, "documentation": text, "object": self.is_object(name)}
            for _, (name, _, text, parents) in ordered
        ]
        return self._with_parent_declarations(results, limit + MAX_PARENT_DECLARATIONS)

    def _with_parent_declarations(self, results: list[dict], limit: int) -> list[dict]:
        """The results followed by the declarations of their parents (one hop up), so the model sees what
        each parent is: "Seats (child of CarModelProfile)" against "SeatingCapacity (child of
        PassengerCapacity)" reads differently once PassengerCapacity and CarModelProfile are defined too."""
        seen = {result["name"] for result in results}
        extra = []
        for result in results:
            for parent in result["parents"]:
                if parent in seen or not self.docs.get(parent):
                    continue
                seen.add(parent)
                # Text from the global declaration when there is one, else the first; parents from every
                # declaration (PassengerCapacity is declared globally and, by name, in the vehicle type group).
                _, text = next(((c, t) for c, t in self.docs[parent] if c == ""), self.docs[parent][0])
                parents = sorted({p for c, _ in self.docs[parent] for p in self._parents_of(parent, c)})[:MAX_PARENTS]
                extra.append({"name": parent, "parents": parents, "documentation": text, "object": self.is_object(parent)})
        return (results + extra)[:limit]

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


def load_content_models(checkout: Path):
    from helpdesk.netex_content_model import ContentModels

    models = ContentModels()
    models.load_directory((checkout / SCHEMA_ENTRY).parent, parser=_parser())
    models.count_usage(checkout / "examples")
    return models


_ELEMENT_MESSAGE = re.compile(r"Element '([^']+)': (.*)", re.S)
_KEYREF = re.compile(r"No match found for key-sequence \['([^']*)'(?:, '([^']*)')?\] of keyref '([^']+)'")


def diagnostics(models, document, log: list[tuple[int, str]], offset: int) -> list[dict]:
    """What is wrong with an invalid document, one entry per problem, in words a model can act on.

    Abstract and undeclared elements are looked for in the whole fragment (libxml2 reports only the
    first error under a parent); the other kinds start from libxml2's messages and are explained with
    the parent's content model: its children in schema order, required ones marked, substitution heads
    expanded to the concrete elements."""
    entries: list[dict] = []
    seen: set = set()
    namespace = "{" + NETEX_NAMESPACE + "}"

    def add(kind: str, node, detail: str) -> None:
        name = _local(node.tag) if node is not None else ""
        parent_node = node.getparent() if node is not None else None
        parent = _local(parent_node.tag) if parent_node is not None else ""
        key = (kind, name, parent) if kind != "keyref" else (kind, name, detail)
        if key in seen:
            return
        seen.add(key)
        line = max(1, (node.sourceline or offset + 1) - offset) if node is not None else 0
        entries.append({"line": line, "element": name, "parent": parent, "kind": kind, "detail": detail})

    def children(node) -> list[str]:
        return [_local(child.tag) for child in node if isinstance(child.tag, str) and child.tag.startswith(namespace)]

    def child_list(node, focus) -> str:
        return f"`{_local(node.tag)}` children in schema order: {models.child_list(models.type_of(node), set(focus))}"

    flagged = set()
    for node in document.iter():
        if not isinstance(node.tag, str) or not node.tag.startswith(namespace):
            continue
        name = _local(node.tag)
        if name in _WRAPPER_ELEMENTS:
            continue
        if name in models.abstract:
            members = models.in_place_of(name)[:8]
            add("abstract", node, f"`{name}` is abstract and cannot appear in a document; write one of these concrete "
                f"elements in its place (most used in the standard's examples first): {', '.join(members) or 'none'}.")
            flagged.add(name)
        elif name not in models.declared:
            add("undeclared", node, f"`{name}` is not an element of the NeTEx schema; use only declared elements.")
            flagged.add(name)

    by_line: dict[int, list] = {}
    for node in document.iter():
        if isinstance(node.tag, str):
            by_line.setdefault(node.sourceline, []).append(node)

    for line, message in log:
        match = _ELEMENT_MESSAGE.match(message)
        if not match:
            continue
        name, text = _local(match.group(1)), match.group(2)
        candidates = [n for n in by_line.get(line, []) if _local(n.tag) == name]
        # A model's fragment is often one line: of the elements of that name on the line, the one whose
        # place (or, for missing children, whose content) does not fit the schema.
        if "Missing child element(s)" in text:
            misfit = [n for n in candidates if models.match_children(models.type_of(n), children(n))]
        else:
            misfit = [
                n for n in candidates
                if n.getparent() is not None
                and any(i.child == name for i in models.match_children(models.type_of(n.getparent()), children(n.getparent())))
            ]
        node = (misfit or candidates or [None])[0]
        if node is None or name in flagged:
            continue
        parent = node.getparent()
        if "No match found for key-sequence" in text:
            keyref = _KEYREF.search(text)
            ref, version = (keyref.group(1), keyref.group(2)) if keyref else (node.get("ref", ""), node.get("version", ""))
            target = (keyref.group(3) if keyref else "").removesuffix("_KeyRef") or name.removesuffix("Ref")
            add("keyref", node, f"`{name}` points to `{ref}`{' version ' + version if version else ''}, which is not "
                f"defined in the fragment. Either define a `{target}` with that id and version in the frame, or, for an "
                f"object outside the fragment, leave out the version attribute: <{name} ref=\"{ref}\"/>.")
        elif "This element is not expected" in text and parent is not None:
            issues = [i for i in models.match_children(models.type_of(parent), children(parent)) if i.child == name]
            issue = issues[0] if issues else None
            focus = children(parent) + [name]
            if issue is not None and issue.kind == "wrong-parent":
                where = models.parents_of(name)
                add("wrong-parent", node, f"`{name}` is not a child of `{_local(parent.tag)}`"
                    + (f"; it belongs under one of: {', '.join(where)}" if where else "") + f". {child_list(parent, focus)}.")
            elif issue is not None and issue.kind == "order":
                add("order", node, f"`{name}` is out of order in `{_local(parent.tag)}`: it comes before `{issue.detail.get('before')}` "
                    f"in the schema. {child_list(parent, focus)}.")
            elif issue is not None and issue.kind == "missing-required":
                add("missing-required", node, f"`{_local(parent.tag)}` needs {', '.join(issue.detail['missing'])} before "
                    f"`{name}` (required by the schema). {child_list(parent, focus)}.")
            else:
                add("not-expected", node, f"`{name}` is not expected at this place in `{_local(parent.tag)}`. {child_list(parent, focus)}.")
        elif "Missing child element(s)" in text:
            issues = models.match_children(models.type_of(node), children(node))
            counted = next((i for i in issues if i.kind == "min-count"), None)
            missing = next((i for i in issues if i.kind == "missing-required" and not i.child), None)
            if counted is not None:
                add("min-count", node, f"`{name}` needs at least {counted.detail['min']} of {counted.detail['slot']}; "
                    f"the fragment has {counted.detail['count']}.")
            elif missing is not None:
                add("missing-required", node, f"`{name}` is missing the required {', '.join(missing.detail['missing'])}. "
                    f"{child_list(node, children(node))}.")
            else:
                add("missing-required", node, f"`{name}` is missing required children. {child_list(node, children(node))}.")
    return entries


class SchemaHolder:
    """The compiled schema of the checkout's current commit; recompiled in the background when it moves."""

    def __init__(self, checkout: Path = CHECKOUT):
        self.checkout = checkout
        self.schema = None
        self.element_docs = ElementDocs()
        self.content = None  # ContentModels of the loaded schema
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
            content = load_content_models(self.checkout)
        except Exception as exc:  # missing checkout or a broken schema: keep the previous one
            self.error = str(exc)[:300]
            logger.warning("NeTEx schema not compiled: %s", exc)
        else:
            self.schema, self.element_docs, self.content = schema, element_docs, content
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
            log = [(error.line, error.message.replace("{" + NETEX_NAMESPACE + "}", "")) for error in schema.error_log]
        errors = [f"line {max(1, line - offset)}: {message}" for line, message in log]
        try:
            found = diagnostics(self.content, document, log, offset) if self.content is not None else []
        except Exception as exc:  # feedback is an aid: never fail the validation over it
            logger.warning("diagnostics failed: %s", exc)
            found = []
        # Definitions for any well-formed fragment: an excerpt of a standard example can fail only on
        # references to objects outside it, and is still described.
        return {
            **result, "valid": False, "errors": errors[:MAX_ERRORS], "elements": self.element_docs.notes(document),
            "diagnostics": found[:MAX_DIAGNOSTICS],
        }


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
            if self.path.startswith("/structure"):
                element = parse_qs(urlparse(self.path).query).get("element", [""])[0].strip()
                if not re.fullmatch(r"[A-Za-z][\w.-]{0,80}", element):
                    self._reply(400, {"error": "expected ?element=<ElementName>"})
                    return
                self._reply(200, holder.element_docs.structure(element))
                return
            if self.path.startswith("/declarations"):
                parameters = parse_qs(urlparse(self.path).query)
                words = re.findall(r"[^\W\d_]{4,}", parameters.get("q", [""])[0])[:12]
                counted = [word.lower() for word in re.findall(r"[^\W\d_]{4,}", parameters.get("c", [""])[0])]
                self._reply(200, {"declarations": holder.element_docs.search(words, counted=counted)})
                return
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
