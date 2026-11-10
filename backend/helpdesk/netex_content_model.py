"""The NeTEx schema's content models, for validator feedback a model can act on.

libxml2 reports "Element 'ArrivalTime': This element is not expected. Expected is one of ( … )" with the
list cut at ten entries, says nothing when the element is abstract ("FarePrice": its concrete members
UsageParameterPrice, FareProductPrice, … are what may appear) and "Missing child element(s)" without
the minimum count. The example generator's model then repeats the error (2026-11-10: one run gave the
same ArrivalTime error three times; the required PointInJourneyPatternRef was never in libxml2's list).

ContentModels reads every *.xsd of the checkout into compact particle trees (sequence, choice, element,
group reference) per named complexType, group and anonymous element type, and gives for an element of a
document its children *slots* in schema order: each slot is the set of element names that may stand
there (a substitution-group head expanded to its concrete members, a choice to all of its
alternatives), whether it is required, how often it may repeat. match_children() walks a node's
children through the slots and says what is wrong: an element in the wrong order, a required one
missing before it, one that is not a child of this parent at all, too few of a repeated choice.

Extension puts the base type's content before the extension's own (XSD 1.0); restriction restates the
whole content, so only the restriction's particle counts. A repeated sequence or a choice is one
unordered slot. Checked on the standard's example files (examples/**/*.xml): see the order test in
helpdesk/tests/test_netex_example_generator.py and `audit()` below.

No Django: imported by the netex-validator service.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

XSD_NS = "http://www.w3.org/2001/XMLSchema"
NETEX_NS = "http://www.netex.org.uk/netex"
_X = "{" + XSD_NS + "}"
UNBOUNDED = 1_000_000


def _local(name: str | None) -> str:
    name = name or ""
    return name.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _display(key: str) -> str:
    """'http://www.siri.org.uk/siri|LocationStructure' or 'Quay' -> the name as written in a document."""
    return key.rsplit("|", 1)[-1]


def _occurs(node, attribute: str, default: int = 1) -> int:
    value = node.get(attribute)
    if value is None:
        return default
    if value == "unbounded":
        return UNBOUNDED
    try:
        return int(value)
    except ValueError:
        return default


@dataclass
class Slot:
    """One position of a content model: the names that may stand there, as written in a document."""

    names: dict[str, str]  # element name -> type key of its content
    min: int  # 0 optional, 1 required, n: at least n (a choice with minOccurs="2")
    repeat: bool
    label: str  # how the feedback names the slot: "Name", "PointInJourneyPatternRef (one of: …)", "one of (A, B)"
    wildcard: bool = False


@dataclass
class Issue:
    kind: str  # order | missing-required | wrong-parent | min-count
    child: str  # the child element concerned ("" for a missing one at the end)
    detail: dict = field(default_factory=dict)


class ContentModels:
    def __init__(self) -> None:
        # type key -> (derivation "extension" | "restriction" | "", base type key, particle or None)
        self.types: dict[str, tuple[str, str, tuple | None]] = {}
        self.groups: dict[str, tuple | None] = {}  # group name -> particle
        self.globals: dict[str, str] = {}  # global element name -> type key
        self.abstract: set[str] = set()
        self.substitution_head: dict[str, str] = {}  # member -> head
        self.members: dict[str, list[str]] = {}  # head -> direct members
        self.declared: set[str] = set()  # every element name declared anywhere
        self.local_elements: set[tuple[str, str]] = set()  # (name, type key) of local declarations
        self.usage: Counter = Counter()  # element name -> occurrences in the standard's example files
        # simple type key (or a complex type with simple content) -> (base key, facets, member keys of a union)
        self.simple: dict[str, tuple[str, dict, tuple[str, ...]]] = {}
        self._slots: dict[str, list[Slot]] = {}
        self._accepting: dict[str, frozenset[str]] = {}

    # --- loading -------------------------------------------------------------------------------

    def add_schema(self, root) -> None:
        # SIRI's schemas, read from the same directory, declare some of the same names (LocationStructure)
        # in their own namespace: names outside the NeTEx namespace are keyed "namespace|name".
        self._target = root.get("targetNamespace") or ""
        for node in root:
            tag = node.tag if isinstance(node.tag, str) else ""
            name = node.get("name")
            if tag == _X + "complexType" and name:
                self._add_type(self._key(name), node)
            elif tag == _X + "group" and name:
                self.groups[self._key(name)] = self._group_particle(node, self._key(name))
            elif tag == _X + "element" and name:
                self._add_global(self._key(name), node)
            elif tag == _X + "simpleType" and name:
                self._add_simple(self._key(name), node)

    def _key(self, name: str) -> str:
        target = getattr(self, "_target", NETEX_NS) or NETEX_NS
        return name if target == NETEX_NS else f"{target}|{name}"

    @staticmethod
    def _ref(node, attribute: str) -> str:
        """A QName attribute (ref, type, base, substitutionGroup) as a key: its prefix resolved."""
        value = node.get(attribute) or ""
        if not value:
            return ""
        prefix, _, local = value.rpartition(":")
        uri = node.nsmap.get(prefix or None, NETEX_NS if not prefix else "")
        return local if uri in (NETEX_NS, "") else f"{uri}|{local}"

    def _add_global(self, key: str, node) -> None:
        self.declared.add(_display(key))
        if node.get("abstract") == "true":
            self.abstract.add(key)
        head = self._ref(node, "substitutionGroup")
        if head:
            self.substitution_head[key] = head
            self.members.setdefault(head, []).append(key)
        self.globals[key] = self._element_type_key(key, node, "global")

    def _element_type_key(self, name: str, node, owner: str) -> str:
        if node.get("type"):
            return self._ref(node, "type")
        anonymous = node.find(_X + "complexType")
        key = f"{owner}/{name}"
        if anonymous is None:
            simple = node.find(_X + "simpleType")
            if simple is None:
                return ""
            self._add_simple(key, simple)
            return key
        self._add_type(key, anonymous)
        return key

    def _add_simple(self, key: str, node) -> None:
        """A simple type, or the simple content of a complex type: its base, facets and union members."""
        restriction = node.find(_X + "restriction")
        if restriction is not None:
            facets: dict = {}
            for facet in restriction:
                name = _local(facet.tag) if isinstance(facet.tag, str) else ""
                if name in ("enumeration", "pattern"):
                    facets.setdefault(name, []).append(facet.get("value") or "")
                elif name in ("length", "minLength", "maxLength"):
                    facets[name] = _occurs(facet, "value", 0)
            base = self._ref(restriction, "base")
            if not base and restriction.find(_X + "simpleType") is not None:
                base = key + "/base"
                self._add_simple(base, restriction.find(_X + "simpleType"))
            self.simple[key] = (base, facets, ())
            return
        union = node.find(_X + "union")
        if union is not None:
            members = [self._ref_value(union, value) for value in (union.get("memberTypes") or "").split()]
            for index, inner in enumerate(union.findall(_X + "simpleType")):
                self._add_simple(f"{key}/{index}", inner)
                members.append(f"{key}/{index}")
            self.simple[key] = ("", {}, tuple(members))
            return
        # xsd:list and anything else: free text for this purpose.
        self.simple[key] = (XSD_NS + "|string", {}, ())

    @staticmethod
    def _ref_value(node, value: str) -> str:
        prefix, _, local = value.rpartition(":")
        uri = node.nsmap.get(prefix or None, NETEX_NS if not prefix else "")
        return local if uri in (NETEX_NS, "") else f"{uri}|{local}"

    def _add_type(self, key: str, node) -> None:
        content = node.find(_X + "complexContent")
        if content is not None:
            for derivation in ("extension", "restriction"):
                derived = content.find(_X + derivation)
                if derived is not None:
                    self.types[key] = (derivation, self._ref(derived, "base"), self._first_particle(derived, key))
                    return
        simple_content = node.find(_X + "simpleContent")
        if simple_content is not None:
            self.types[key] = ("", "", None)
            derived = simple_content.find(_X + "restriction")
            if derived is not None:
                self._add_simple(key, simple_content)
            else:
                derived = simple_content.find(_X + "extension")
                if derived is not None:
                    self.simple[key] = (self._ref(derived, "base"), {}, ())
            return
        self.types[key] = ("", "", self._first_particle(node, key))

    def _group_particle(self, node, owner: str):
        return self._first_particle(node, owner)

    def _first_particle(self, node, owner: str):
        for child in node:
            if isinstance(child.tag, str) and child.tag in (_X + "sequence", _X + "choice", _X + "all", _X + "group"):
                return self._particle(child, owner)
        return None

    def _particle(self, node, owner: str):
        tag = node.tag
        low, high = _occurs(node, "minOccurs"), _occurs(node, "maxOccurs")
        if tag == _X + "element":
            if node.get("ref"):
                return ("el", self._ref(node, "ref"), None, low, high, True)
            name = node.get("name")
            self.declared.add(name)
            type_key = self._element_type_key(name, node, owner)
            if type_key:
                self.local_elements.add((name, type_key))
            return ("el", name, type_key, low, high, False)
        if tag == _X + "group":
            return ("group", self._ref(node, "ref"), low, high)
        if tag == _X + "any":
            return ("any", low, high)
        kind = {"sequence": "seq", "choice": "choice", "all": "choice"}.get(_local(tag))
        if kind is None:
            return None
        children = tuple(
            particle
            for child in node
            if isinstance(child.tag, str) and child.tag in (_X + "element", _X + "group", _X + "any", _X + "sequence", _X + "choice")
            for particle in [self._particle(child, owner)]
            if particle is not None
        )
        return (kind, children, low, high)

    def load_directory(self, directory: Path, parser=None) -> None:
        from lxml import etree

        for path in sorted(directory.rglob("*.xsd")):
            try:
                root = etree.parse(str(path), parser=parser).getroot()
            except (etree.XMLSyntaxError, OSError):
                continue
            self.add_schema(root)

    def count_usage(self, examples: Path, limit_bytes: int = 200_000_000) -> None:
        """How often each element occurs in the standard's example files: the concrete members of an
        abstract element are named most used first."""
        total = 0
        pattern = re.compile(rb"<([A-Za-z][\w.-]*)[\s>/]")
        for path in sorted(examples.rglob("*.xml")):
            try:
                data = path.read_bytes()
            except OSError:
                continue
            total += len(data)
            if total > limit_bytes:
                break
            self.usage.update(match.decode("ascii", "ignore") for match in pattern.findall(data))

    # --- queries -------------------------------------------------------------------------------

    def in_place_of(self, name: str) -> list[str]:
        """Concrete elements to write instead of an abstract one: its own substitution members, else (an
        abstract element that only marks a kind, FarePrice) the members of the group it belongs to
        (FarePrice_Dummy: UsageParameterPrice, FareProductPrice, …); most used in the examples first."""
        own = [n for n in self.concrete(name) if n != name]
        if own or name not in self.substitution_head:
            return [_display(n) for n in own]
        return [_display(n) for n in self.concrete(self.substitution_head[name]) if n != name]

    def concrete(self, name: str) -> list[str]:
        """The non-abstract elements that may stand where `name` is referenced: itself unless abstract,
        and every member of its substitution group, transitively; most used in the examples first."""
        found, pending, seen = [], [name], set()
        while pending:
            current = pending.pop(0)
            if current in seen:
                continue
            seen.add(current)
            if current not in self.abstract:
                found.append(current)
            pending.extend(self.members.get(current, ()))
        head = found[:1] if found and found[0] == name else []
        rest = sorted((n for n in found if n != name), key=lambda n: (-self.usage.get(_display(n), 0), n))
        return head + rest

    def slots(self, type_key: str) -> list[Slot]:
        """The children slots of a type, in schema order."""
        if type_key in self._slots:
            return self._slots[type_key]
        out: list[Slot] = []
        self._type_slots(type_key, out, set())
        self._slots[type_key] = out
        return out

    def _type_slots(self, type_key: str, out: list[Slot], visiting: set) -> None:
        if not type_key or type_key in visiting or type_key not in self.types:
            return
        visiting = visiting | {type_key}
        derivation, base, particle = self.types[type_key]
        if derivation == "extension":
            self._type_slots(base, out, visiting)
        if particle is not None:
            self._walk(particle, True, out, visiting)

    def _element_entry(self, particle) -> dict[str, str]:
        _, name, type_key, _, _, is_ref = particle
        if not is_ref:
            return {name: type_key or ""}
        return {_display(member): self.globals.get(member, "") for member in self.concrete(name)}

    def _names(self, particle, visiting: set) -> dict[str, str]:
        kind = particle[0]
        if kind == "el":
            return self._element_entry(particle)
        if kind == "group":
            group = self.groups.get(particle[1])
            if group is None or particle[1] in visiting:
                return {}
            return self._names(group, visiting | {particle[1]})
        if kind == "any":
            return {}
        names: dict[str, str] = {}
        for child in particle[1]:
            names.update(self._names(child, visiting))
        return names

    def _can_be_empty(self, particle, visiting: set = frozenset()) -> bool:
        kind = particle[0]
        if kind == "el":
            return particle[3] == 0
        if kind == "any":
            return particle[1] == 0
        if kind == "group":
            group = self.groups.get(particle[1])
            return particle[2] == 0 or group is None or particle[1] in visiting or self._can_be_empty(group, visiting | {particle[1]})
        if particle[2] == 0:
            return True
        children = particle[1]
        if kind == "seq":
            return all(self._can_be_empty(child, visiting) for child in children)
        return any(self._can_be_empty(child, visiting) for child in children) or not children

    def _walk(self, particle, required: bool, out: list[Slot], visiting: set) -> None:
        kind = particle[0]
        if kind == "el":
            _, name, _, low, high, is_ref = particle
            names = self._element_entry(particle)
            if not names:
                return
            label = _display(name)
            if is_ref and (len(names) > 1 or label not in names):
                shown = list(names)[:8]
                label = f"{label} (one of: {', '.join(shown)}{', …' if len(names) > 8 else ''})"
            out.append(Slot(names, low if required else 0, high > 1, label))
            return
        if kind == "any":
            out.append(Slot({}, 0, True, "any element", wildcard=True))
            return
        if kind == "group":
            name, low, high = particle[1], particle[2], particle[3]
            group = self.groups.get(name)
            if group is None or name in visiting:
                return
            if high > 1:
                names = self._names(group, visiting)
                if names:
                    out.append(Slot(names, 1 if required and low >= 1 and not self._can_be_empty(group) else 0, True, self._choice_label(names)))
                return
            self._walk(group, required and low >= 1, out, visiting | {name})
            return
        children, low, high = particle[1], particle[2], particle[3]
        if not children:
            return
        if kind == "seq" and high <= 1:
            for child in children:
                self._walk(child, required and low >= 1, out, visiting)
            return
        if kind == "choice" and len(children) == 1 and high <= 1:
            self._walk(children[0], required and low >= 1, out, visiting)
            return
        # A choice, or a repeated sequence: one unordered slot of all the names inside.
        names = self._names(particle, visiting)
        if not names:
            return
        if kind == "choice":
            empty = any(self._can_be_empty(child, visiting) for child in children)
        else:
            empty = self._can_be_empty(particle, visiting)
        minimum = low if required and not empty else 0
        # An alternative that is more than one element (a sequence, a group) fills the slot with several.
        repeat = high > 1 or any(not (c[0] == "el" and c[4] <= 1) for c in children)
        out.append(Slot(names, minimum, repeat, self._choice_label(names)))

    @staticmethod
    def _choice_label(names: dict[str, str]) -> str:
        shown = list(names)[:8]
        return f"one of ({', '.join(shown)}{', …' if len(names) > 8 else ''})"

    # --- documents -----------------------------------------------------------------------------

    def type_of(self, node, local=_local) -> str:
        """The type key of a document element, from the root's global declaration down the path."""
        path = []
        current = node
        while current is not None:
            path.append(local(current.tag))
            current = current.getparent()
        path.reverse()
        type_key = self.globals.get(path[0], "")
        for name in path[1:]:
            entry = next((slot.names[name] for slot in self.slots(type_key) if name in slot.names), None)
            type_key = entry if entry is not None else self.globals.get(name, "")
        return type_key

    def match_children(self, type_key: str, children: list[str]) -> list[Issue]:
        """What is wrong with the children's names against the type's slots ([] when they fit)."""
        slots = self.slots(type_key)
        if not slots:
            return []
        counts = [0] * len(slots)
        position = 0
        issues: list[Issue] = []
        previous = ""
        for child in children:
            target = None
            for index in range(position, len(slots)):
                slot = slots[index]
                if child in slot.names and (slot.repeat or counts[index] == 0):
                    target = index
                    break
            if target is None and not any(child in slot.names for slot in slots):
                wildcard = next((i for i in range(position, len(slots)) if slots[i].wildcard), None)
                if wildcard is not None:
                    counts[wildcard] += 1
                    position = wildcard
                    previous = child
                    continue
                issues.append(Issue("wrong-parent", child))
                continue
            if target is None:
                earlier = next(i for i, slot in enumerate(slots) if child in slot.names)
                issues.append(Issue("order", child, {"before": previous, "slot": earlier}))
                continue
            missing = [slots[i].label for i in range(position, target) if slots[i].min >= 1 and counts[i] == 0]
            if missing:
                issues.append(Issue("missing-required", child, {"missing": missing}))
            counts[target] += 1
            position = target if slots[target].repeat else target + 1
            previous = child
        for index in range(len(slots)):
            slot = slots[index]
            if slot.min >= 2 and 0 < counts[index] < slot.min:
                issues.append(Issue("min-count", "", {"slot": slot.label, "min": slot.min, "count": counts[index]}))
        missing_end = [slots[i].label for i in range(position, len(slots)) if slots[i].min >= 1 and counts[i] == 0]
        if missing_end:
            issues.append(Issue("missing-required", "", {"missing": missing_end}))
        return issues

    def child_list(self, type_key: str, focus: set[str] = frozenset(), limit: int = 45) -> str:
        """The type's children in schema order, "?" optional, "*" repeatable, required ones marked; a long
        list keeps the required slots, those holding a focus name and their neighbours."""
        slots = self.slots(type_key)

        def shown(slot: Slot) -> str:
            mark = "" if slot.min >= 1 else "?"
            mark += "*" if slot.repeat else ""
            required = f" (required{', at least ' + str(slot.min) if slot.min > 1 else ''})" if slot.min >= 1 else ""
            return f"{slot.label}{mark}{required}"

        if len(slots) <= limit:
            return ", ".join(shown(slot) for slot in slots)
        keep = set()
        for index, slot in enumerate(slots):
            if slot.min >= 1 or focus & set(slot.names):
                keep.update(range(max(0, index - 2), min(len(slots), index + 3)))
        parts, gap = [], False
        for index, slot in enumerate(slots):
            if index in keep:
                parts.append(shown(slot))
                gap = False
            elif not gap:
                parts.append("…")
                gap = True
        return ", ".join(parts)

    def parents_of(self, name: str, limit: int = 8) -> list[str]:
        """Elements whose content model has `name` as a child (global ones and local list wrappers such as
        `prices`), most used in the examples first."""
        candidates = [(e, t) for e, t in self.globals.items() if e not in self.abstract and "|" not in e]
        candidates += sorted(self.local_elements)
        found = []
        for element, type_key in candidates:
            if element in found or not type_key:
                continue
            if any(name in slot.names for slot in self.slots(type_key)):
                found.append(element)
        return sorted(found, key=lambda n: (-self.usage.get(n, 0), n))[:limit]


_NUMERIC = {
    "decimal": r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",
    "float": r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|INF|-INF|NaN",
    "double": r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|INF|-INF|NaN",
    "integer": r"[+-]?\d+", "long": r"[+-]?\d+", "int": r"[+-]?\d+", "short": r"[+-]?\d+", "byte": r"[+-]?\d+",
    "nonNegativeInteger": r"\+?\d+", "positiveInteger": r"\+?0*[1-9]\d*", "unsignedLong": r"\+?\d+",
    "unsignedInt": r"\+?\d+", "unsignedShort": r"\+?\d+", "unsignedByte": r"\+?\d+",
    "nonPositiveInteger": r"-\d+|\+?0+", "negativeInteger": r"-0*[1-9]\d*",
}
_ZONE = r"(?:Z|[+-]\d{2}:\d{2})?"
_BUILTIN = {
    **_NUMERIC,
    "boolean": r"true|false|1|0",
    "date": r"-?\d{4,}-\d{2}-\d{2}" + _ZONE,
    "time": r"\d{2}:\d{2}:\d{2}(?:\.\d+)?" + _ZONE,
    "dateTime": r"-?\d{4,}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?" + _ZONE,
    "duration": r"-?P(?=\d|T\d)(?:\d+Y)?(?:\d+M)?(?:\d+D)?(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?",
    "gYear": r"-?\d{4,}" + _ZONE, "gYearMonth": r"-?\d{4,}-\d{2}" + _ZONE, "gMonthDay": r"--\d{2}-\d{2}" + _ZONE,
    "gDay": r"---\d{2}" + _ZONE, "gMonth": r"--\d{2}" + _ZONE,
    "hexBinary": r"(?:[0-9A-Fa-f]{2})*",
}
_TEXT = {"string", "normalizedString", "token", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREF", "IDREFS",
         "anyURI", "language", "QName", "ENTITY", "ENTITIES", "anySimpleType", "base64Binary"}


def _xsd_pattern(pattern: str) -> str:
    """An XSD pattern as a Python one: the XML name classes \\i and \\c as approximations."""
    return pattern.replace("\\i", "[A-Za-z_:]").replace("\\c", "[\\w.:-]")


def accepts(models: ContentModels, type_key: str, value: str, _depth: int = 0) -> tuple[bool, bool]:
    """(whether a type accepts the value as content, whether the type is *specific*): a number, date, time,
    boolean or duration type, or text narrowed by an enumeration, a pattern or a length. A free-text type
    (Name, Description) accepts every value and says nothing about where a value belongs."""
    if _depth > 30 or not type_key:
        return False, False
    if type_key.startswith(XSD_NS + "|"):
        builtin = type_key.split("|", 1)[1]
        if builtin in _BUILTIN:
            return bool(re.fullmatch(_BUILTIN[builtin], value)), True
        return builtin in _TEXT, False
    if type_key not in models.simple:
        return False, False
    base, facets, members = models.simple[type_key]
    if members:
        results = [accepts(models, member, value, _depth + 1) for member in members]
        if any(ok and specific for ok, specific in results):
            return True, True
        return any(ok for ok, _ in results), all(specific for _, specific in results)
    specific = bool(facets.get("enumeration") or facets.get("pattern") or "length" in facets or "maxLength" in facets)
    if facets.get("enumeration") and value not in facets["enumeration"]:
        return False, True
    for pattern in facets.get("pattern") or ():
        try:
            if not re.fullmatch(_xsd_pattern(pattern), value):
                return False, True
        except re.error:
            specific = False  # a pattern Python cannot read: no judgement from it
    if "length" in facets and len(value) != facets["length"]:
        return False, True
    if len(value) < facets.get("minLength", 0) or len(value) > facets.get("maxLength", 1 << 30):
        return False, True
    ok, base_specific = accepts(models, base, value, _depth + 1) if base else (True, False)
    return ok, specific or base_specific


def accepting_elements(models: ContentModels, value: str) -> frozenset[str]:
    """The names of the elements, global or local, whose declared simple content accepts the value and is
    specific (see accepts): "EUR" -> Currency and the like, not Name nor the AND/OR/XOR grouping types;
    "5" -> Amount, counts, …; the dateTime elements also take a date or a time of the question as one
    ("2026-12-01" as 2026-12-01T00:00:00)."""
    if value in models._accepting:
        return models._accepting[value]
    forms = [value]
    if re.fullmatch(r"\d{2}:\d{2}", value):
        forms += [value + ":00", "2000-01-01T" + value + ":00"]
    elif re.fullmatch(r"\d{2}:\d{2}:\d{2}", value):
        forms += ["2000-01-01T" + value]
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        forms += [value + "T00:00:00"]
    declarations = [(_display(name), type_key) for name, type_key in models.globals.items()]
    declarations += sorted(models.local_elements)
    found = set()
    verdicts: dict[str, bool] = {}
    for name, type_key in declarations:
        if name in found or not type_key:
            continue
        if type_key not in verdicts:
            verdicts[type_key] = any(ok and specific for ok, specific in (accepts(models, type_key, form) for form in forms))
        if verdicts[type_key]:
            found.add(name)
    models._accepting[value] = frozenset(found)
    return models._accepting[value]


def audit(models: ContentModels, files: list[Path]) -> tuple[int, int, Counter]:
    """(elements checked, elements whose children fit, issues by kind) over example documents: the order
    test of the content models. Elements of other namespaces (gml:, siri:) are not checked."""
    from lxml import etree

    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=True, remove_comments=True)
    namespace = "{http://www.netex.org.uk/netex}"
    checked = fitting = 0
    kinds: Counter = Counter()
    for path in files:
        try:
            root = etree.parse(str(path), parser).getroot()
        except (etree.XMLSyntaxError, OSError):
            continue
        for node in root.iter():
            if not isinstance(node.tag, str) or not node.tag.startswith(namespace):
                continue
            children = [_local(c.tag) for c in node if isinstance(c.tag, str) and c.tag.startswith(namespace)]
            if not children:
                continue
            type_key = models.type_of(node)
            if not type_key:
                continue
            checked += 1
            issues = models.match_children(type_key, children)
            if issues:
                kinds.update(issue.kind for issue in issues)
            else:
                fitting += 1
    return checked, fitting, kinds
