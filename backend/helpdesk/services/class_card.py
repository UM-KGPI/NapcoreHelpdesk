"""
The class card: one class of a loaded ontology, written by code from what the ontology holds.

Plan: an internal plan (kept outside the repository) (step 2). A card shows, for one class of DATEX II or
Transmodel, its definition, its supertypes and subtypes, its own attributes (type, bounds, definition, the values of
an enumeration type), its own relations (role, target, bounds), and the same for each supertype under "Inherited from".
Every line comes from the ontology graph; nothing is worded by a model and nothing is read from the index.

Where the facts come from. The supertypes, subtypes, relations and definitions are the tables the application
already reads at its ontology load (semantic_graph.DIRECTED_RELATIONS). The rest (kind, label, attributes with type,
bounds and definition, the values of an enumeration, the bounds of a relation) are the members the generators write
under predicates of the namespace ea: (docs/ontology/standards/*.ttl, plan step 1). They are read once, at the same
load, by read_member_rows and build_members into semantic_graph.CLASS_MEMBERS, and only when the setting names an
ontology: with RETRIEVAL_CLASS_CARD_ONTOLOGIES empty nothing is queried and no table exists. The members add no
concept, no alias and no relation; no query per question.

When a card is built (trigger A). After the six passages are chosen, after whole records and path blocks (the hook is
in retrieval_gateway), for a class that a served passage is about: the record of a DATEX II class (the card takes the
record's place, number and rank; the record's source path stays in replacesSourcePath) or an ontology definition
block (the card is added after the blocks, like a path block). Trigger B (a class that an end of a path block names)
is not built; its place is class_of_path_block_ends below.

What the answer checks do with it: a card cited by an answer is a block like a path block. The policy accepts the
ontology file it cites (semantic_path.is_path_ontology_url); the term check reads what the card defines (defines);
the sentence check reads claims "X is a Y", "X can be a Y" and "X has Y" between classes of the card against its
supertype, subtype and relation lines (step_claim_error).

Off by default: RETRIEVAL_CLASS_CARD_ONTOLOGIES is a list of ontology keys ("datex", "transmodel"); EMPTY MEANS OFF,
unlike RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES, where empty means every ontology.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-25  |  Modified: 2026-11-25
"""

from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass
from uuid import uuid4

EA = "https://napcore.eu/ontology/ea-model#"
STANDARD_ONTOLOGIES_URL = "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards"
ONTOLOGY_PATH = "docs/ontology/standards"

MAX_CARD_CHARS = 2400  # the limit of a path block
MAX_CARDS = 3  # per question
MAX_NET_CHARS = 2500  # per question, net of what a card replaced
MAX_SUBTYPES = 12
MAX_VALUES = 15
LADDER_MAX_VALUES = 8
MAX_VALUE_DEFINITIONS = 3  # per card: the values the question names
MIN_VALUE_PHRASE = 3  # characters of a value that can be "named" by a question


# ---------------------------------------------------------------------------------------------------- the setting


def configured_ontologies() -> set[str]:
    """The ontology keys cards are built for (RETRIEVAL_CLASS_CARD_ONTOLOGIES, comma-separated, case ignored).
    Empty means OFF: no card, no member read, no change in evidence."""
    from django.conf import settings

    raw = str(getattr(settings, "RETRIEVAL_CLASS_CARD_ONTOLOGIES", "") or "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def enabled() -> bool:
    return bool(configured_ontologies())


# ---------------------------------------------------------------------------------------------------- reading members

_PREFIXES = "PREFIX ea: <" + EA + ">\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nPREFIX owl: <http://www.w3.org/2002/07/owl#>\n"


def _iri_filter(variable: str, prefixes: list[str]) -> str:
    return " || ".join(f'STRSTARTS(STR({variable}), "{prefix}")' for prefix in prefixes)


def member_queries(prefixes: list[str]) -> dict[str, str]:
    """The three SPARQL queries of the member read, restricted to the classes whose IRI starts with one of the prefixes."""
    classes = (
        _PREFIXES
        + "SELECT DISTINCT ?c ?kind ?label ?comment WHERE { GRAPH ?g { ?c ea:kind ?kind . OPTIONAL { ?c rdfs:label ?label } "
        "OPTIONAL { ?c rdfs:comment ?comment } } "
        + f"FILTER({_iri_filter('?c', prefixes)}) }}"
    )
    members = (
        _PREFIXES
        + "SELECT DISTINCT ?c ?role ?name ?pos ?type ?typeName ?lo ?up ?def WHERE { GRAPH ?g { "
        "?c ?role ?m . FILTER(?role IN (ea:attribute, ea:value)) ?m ea:name ?name . "
        "OPTIONAL { ?m ea:position ?pos } OPTIONAL { ?m ea:type ?type } OPTIONAL { ?m ea:typeName ?typeName } "
        "OPTIONAL { ?m ea:lowerBound ?lo } OPTIONAL { ?m ea:upperBound ?up } OPTIONAL { ?m ea:definition ?def } } "
        + f"FILTER({_iri_filter('?c', prefixes)}) }}"
    )
    relations = (
        _PREFIXES
        + "SELECT DISTINCT ?prop ?d ?r ?label ?lo ?up ?text WHERE { GRAPH ?g { "
        "?prop a owl:ObjectProperty ; rdfs:domain ?d ; rdfs:range ?r . "
        "OPTIONAL { ?prop rdfs:label ?label } OPTIONAL { ?prop ea:lowerBound ?lo } "
        "OPTIONAL { ?prop ea:upperBound ?up } OPTIONAL { ?prop ea:multiplicityText ?text } } "
        + f"FILTER({_iri_filter('?d', prefixes)}) }}"
    )
    return {"classes": classes, "members": members, "relations": relations}


def read_member_rows(sparql_get, namespaces: dict[str, str], ontologies: set[str] | None = None) -> dict[str, list[dict]]:
    """The raw rows of the member read; {} when no ontology is configured. sparql_get(name, query) is the ontology
    load's own query function (it retries while GraphDB starts and raises OntologyQueryError on a failure).
    namespaces: IRI prefix -> ontology key (semantic_graph._IRI_PREFIX_MAP)."""
    ontologies = configured_ontologies() if ontologies is None else ontologies
    prefixes = sorted(prefix for prefix, key in namespaces.items() if key in ontologies)
    if not prefixes:
        return {}
    return {name: sparql_get(f"class members: {name}", query) for name, query in member_queries(prefixes).items()}


def place_of(kind: str, comment: str) -> str:
    """"namespace X / package" from the comment the generator writes on a class of a model with namespaces
    ("DATEX II class in namespace X / package"), else "". It is the text the model record's head carries, so a card's
    head names the same place. A comment of another form (a definition, say) gives nothing."""
    match = re.match(r"^[^.]{0,40}?\b" + re.escape(kind) + r" in (namespace \S.*)$", " ".join((comment or "").split()))
    return match.group(1) if match else ""


def build_members(rows: dict[str, list[dict]], to_concept, relation_name) -> dict:
    """The tables a card is built from, from the rows of read_member_rows.

    {"classes": {concept: {"kind", "label", "place"}}, "attributes": {concept: [member]}, "values": {concept: [member]},
     "relations": {(domain, range, name): {"label", "lower", "upper", "text"}}, "repeated": {concept}}
    A member is {"name", "position", "type" (concept or None), "typeName", "lower", "upper", "definition"}.
    repeated: the classes whose label another class of the same ontology has too (shown with their local name)."""
    classes: dict[str, dict] = {}
    for row in rows.get("classes") or []:
        concept = to_concept(row.get("c", ""))
        if concept and row.get("kind"):
            classes[concept] = {"kind": row["kind"], "label": row.get("label", ""), "place": place_of(row["kind"], row.get("comment", ""))}
    attributes: dict[str, list[dict]] = {}
    values: dict[str, list[dict]] = {}
    for row in rows.get("members") or []:
        concept = to_concept(row.get("c", ""))
        if not concept or concept not in classes or not row.get("name"):
            continue
        member = {
            "name": row["name"],
            "position": int(row["pos"]) if str(row.get("pos", "")).lstrip("-").isdigit() else 0,
            "type": to_concept(row["type"]) if row.get("type") else None,
            "typeName": row.get("typeName", ""),
            "lower": row.get("lo", ""),
            "upper": row.get("up", ""),
            "definition": " ".join(row.get("def", "").split()),
        }
        (values if row.get("role", "").endswith("#value") else attributes).setdefault(concept, []).append(member)
    for table in (attributes, values):
        for members in table.values():
            members.sort(key=lambda m: (m["position"], m["name"]))
    relations: dict[tuple[str, str, str], dict] = {}
    for row in rows.get("relations") or []:
        domain, range_, prop = to_concept(row.get("d", "")), to_concept(row.get("r", "")), to_concept(row.get("prop", ""))
        if not (domain and range_ and prop):
            continue
        relations[(domain, range_, relation_name(prop, domain))] = {
            "label": row.get("label", ""),
            "lower": row.get("lo", ""),
            "upper": row.get("up", ""),
            "text": row.get("text", ""),
        }
    labels = Counter((concept.partition(":")[0], entry["label"]) for concept, entry in classes.items() if entry["label"])
    repeated = {c for c, e in classes.items() if e["label"] and labels[(c.partition(":")[0], e["label"])] > 1}
    return {"classes": classes, "attributes": attributes, "values": values, "relations": relations, "repeated": repeated}


# ---------------------------------------------------------------------------------------------------- names


def _sg():
    from helpdesk.services import semantic_graph

    return semantic_graph


def ontology_key(concept: str) -> str:
    return concept.partition(":")[0]


def ontology_label(concept: str) -> str:
    from helpdesk.services import semantic_path

    key = ontology_key(concept)
    return semantic_path.ONTOLOGY_LABELS.get(key, key)


def shown_name(concept: str, members: dict) -> str:
    """The class as a card writes it: its label; its local name (with the namespace of DATEX II, the object id of
    Transmodel) where another class of the ontology has the same label."""
    entry = members["classes"].get(concept) or {}
    if concept in members["repeated"]:
        return concept.partition(":")[2]
    return entry.get("label") or _sg().concept_own_name(concept)


def _sort_name(concept: str, members: dict) -> tuple[str, str]:
    entry = members["classes"].get(concept) or {}
    return ((entry.get("label") or _sg().concept_own_name(concept)).lower(), concept)


def bounds_text(lower: str, upper: str, text: str = "") -> str:
    """"1" when both bounds are one number, "lower..upper" otherwise, the model's own text where it is no number pair."""
    if text:
        return text
    if lower == "" and upper == "":
        return ""
    return lower if lower == upper else f"{lower}..{upper}"


def _attribute_bounds(member: dict) -> str:
    lower, upper = member["lower"], member["upper"]
    return "" if lower == "" and upper == "" else f"{lower}..{upper}"


# ---------------------------------------------------------------------------------------------------- the card


@dataclass
class Card:
    concept: str
    text: str
    ladder: int  # 0: whole; 1 to 5: the step of the ladder that made it fit (see build_card)
    left_out: list[str]
    nodes: list[str]
    steps: list[list[str]]
    defined: list[str]
    trigger: str = ""  # "record" or "definition": what served evidence the card is about (set by with_cards)

    @property
    def chars(self) -> int:
        return len(self.text)


@dataclass
class _Options:
    definitions_inherited: bool = True
    definitions_own: bool = True
    max_values: int = MAX_VALUES
    groups: int | None = None  # supertype groups kept (None: all)
    own_relations: int | None = None
    own_attributes: int | None = None


def _words(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text).lower()).split())


def _named_in(value: str, question_words: str) -> bool:
    phrase = _words(value)
    return len(phrase.replace(" ", "")) >= MIN_VALUE_PHRASE and f" {phrase} " in f" {question_words} "


def _ancestors(concept: str, supers: dict, members: dict) -> list[str]:
    """The supertypes, nearest first (breadth first; within a level, by name), each once."""
    seen, frontier, found = {concept}, [concept], []
    while frontier:
        following = []
        for node in frontier:
            for parent in sorted(supers.get(node, []), key=lambda c: _sort_name(c, members)):
                if parent not in seen:
                    seen.add(parent)
                    found.append(parent)
                    following.append(parent)
        frontier = following
    return found


def _member_lines(concept: str, members: dict, question_words: str) -> list[dict]:
    """The attributes of a class as card lines: {"head", "definition", "type", "values", "value_definitions"}."""
    lines = []
    for member in members["attributes"].get(concept, []):
        type_concept = member["type"]
        if type_concept:
            type_name = shown_name(type_concept, members)
        else:
            type_name = member["typeName"] or "no type"
        bounds = _attribute_bounds(member)
        head = f"- {member['name']} ({type_name}{', ' + bounds if bounds else ''})"
        entry = {"head": head, "definition": member["definition"], "name": member["name"], "type": None, "values": [], "value_definitions": []}
        if type_concept and (members["classes"].get(type_concept) or {}).get("kind") == "enumeration":
            values = members["values"].get(type_concept, [])
            named = [v for v in values if _named_in(v["name"], question_words)]
            ordered = named + [v for v in values if v not in named]
            entry["type"] = type_name
            entry["values"] = [v["name"] for v in ordered]
            entry["value_definitions"] = [(v["name"], v["definition"]) for v in named if v["definition"]]
        lines.append(entry)
    return lines


def _relation_lines(concept: str, members: dict, directed: dict) -> list[dict]:
    """The relations of a class: {"text", "target", "sort"}, sorted by role (a relation without a role last), target."""
    sg = _sg()
    lines = []
    for target, name in directed.get("out", {}).get(concept, []):
        fact = members["relations"].get((concept, target, name)) or {}
        target_label = (members["classes"].get(target) or {}).get("label") or sg.concept_own_name(target)
        candidate = fact.get("label") or sg.local_own_name(name)
        bare = candidate[4:] if candidate.startswith("has ") else candidate
        role = "" if bare == target_label or candidate == target_label else candidate
        bounds = bounds_text(fact.get("lower", ""), fact.get("upper", ""), fact.get("text", ""))
        target_name = shown_name(target, members)
        text = f"- {role or 'relation without a role name'} -> {target_name}" + (f" ({bounds})" if bounds else "")
        lines.append({"text": text, "target": target, "target_name": target_name, "sort": ((role or "~").lower(), target_name, bounds)})
    lines.sort(key=lambda line: line["sort"])
    return lines


def _render_member(entry: dict, options: _Options, inherited: bool, left: dict) -> list[str]:
    show_definition = options.definitions_inherited if inherited else options.definitions_own
    head = entry["head"]
    lines = []
    if entry["definition"]:
        if show_definition:
            head += f": {entry['definition']}"
        else:
            left["definitions_inherited" if inherited else "definitions_own"] += 1
    lines.append(head)
    if entry["type"]:
        total = len(entry["values"])
        kept = entry["values"][: options.max_values]
        line = f"  values of {entry['type']}: " + ", ".join(kept)
        if total > len(kept):
            line += f" (and {total - len(kept)} more, not shown)"
            left["values"].setdefault(entry["type"], total - len(kept))
        lines.append(line)
        for name, definition in entry["value_definitions"][:MAX_VALUE_DEFINITIONS]:
            if name not in kept:
                continue
            if show_definition:
                lines.append(f"  {name}: {definition}")
            else:
                left["definitions_inherited" if inherited else "definitions_own"] += 1
    return lines


def _render(parts: dict, options: _Options) -> tuple[str, list[str], dict]:
    """(text, left out, shown) of the card parts under the options; shown: what the facts of the checks are read from."""
    left = {"subtypes": 0, "values": {}, "definitions_inherited": 0, "definitions_own": 0, "groups": [], "own_relations": 0, "own_attributes": 0}
    lines = [parts["head"]]
    if parts["definition"]:
        lines.append(f"Definition: {parts['definition']}")
    if parts["supers"]:
        lines.append("Supertypes: " + ", ".join(parts["supers"]))
    shown_subs = parts["subs"][:MAX_SUBTYPES]
    if parts["subs"]:
        extra = len(parts["subs"]) - len(shown_subs)
        lines.append("Subtypes: " + ", ".join(shown_subs) + (f" (and {extra} more, not shown)" if extra else ""))
        left["subtypes"] = extra
    shown_attributes = parts["attributes"][: options.own_attributes]
    shown_relations = parts["relations"][: options.own_relations]
    left["own_attributes"] = len(parts["attributes"]) - len(shown_attributes)
    left["own_relations"] = len(parts["relations"]) - len(shown_relations)
    if parts["enumeration"]:
        values = parts["enumeration_values"]
        kept = values[: options.max_values]
        line = f"Values ({len(values)}): " + ", ".join(kept)
        if len(values) > len(kept):
            line += f" (and {len(values) - len(kept)} more, not shown)"
            left["values"].setdefault(parts["name"], len(values) - len(kept))
        lines.append(line)
        shown_definitions = 0
        for name, definition in parts["enumeration_value_definitions"][:MAX_VALUE_DEFINITIONS]:
            if name not in kept:
                continue
            if options.definitions_own:
                lines.append(f"  {name}: {definition}")
                shown_definitions += 1
        # every definition of a value the card does not show is counted: those of values the question did not name,
        # those past the cap of MAX_VALUE_DEFINITIONS, those of values left out, and those the ladder dropped
        left["definitions_own"] += parts["enumeration_definition_count"] - shown_definitions
    elif shown_attributes:
        lines.append("Attributes:")
        for entry in shown_attributes:
            lines.extend(_render_member(entry, options, False, left))
    if shown_relations:
        lines.append("Relations:")
        lines.extend(line["text"] for line in shown_relations)
    groups = parts["groups"] if options.groups is None else parts["groups"][: options.groups]
    left["groups"] = [group["name"] for group in parts["groups"][len(groups) :]]
    for group in groups:
        lines.append(f"Inherited from {group['name']}:")
        for entry in group["attributes"]:
            lines.extend(_render_member(entry, options, True, left))
        lines.extend(line["text"] for line in group["relations"])
    out: list[str] = []
    if left["subtypes"]:
        out.append(f"{left['subtypes']} subtypes")
    out.extend(f"{count} values of {name}" for name, count in left["values"].items())
    if left["definitions_inherited"]:
        out.append(f"{left['definitions_inherited']} definitions of inherited members")
    if left["definitions_own"]:
        out.append(f"{left['definitions_own']} definitions of own members")
    if left["groups"]:
        out.append(f"{len(left['groups'])} inherited groups ({', '.join(left['groups'])})")
    if left["own_relations"]:
        out.append(f"{left['own_relations']} relations of the class")
    if left["own_attributes"]:
        out.append(f"{left['own_attributes']} attributes of the class")
    lines.append(f"Source: {ONTOLOGY_PATH}/{parts['key']}.ttl; " + (f"left out: {'; '.join(out)}." if out else "nothing left out."))
    return "\n".join(lines), out, {"attributes": shown_attributes, "relations": shown_relations, "groups": groups, "subs": shown_subs}


def build_card(
    concept: str,
    *,
    members: dict | None = None,
    directed: dict | None = None,
    question: str = "",
    with_definition: bool = True,
    max_chars: int = MAX_CARD_CHARS,
) -> Card | None:
    """The card of a class, or None when the members of the class are not loaded (no card is made without facts) or
    when not even the head, the definition and the source line fit within max_chars.

    The ladder when the card is longer than max_chars, whole lines only, in this order, each step adding to the count
    in the last line: (1) the definitions of inherited members go; (2) the definitions of own members go; (3) at most
    LADDER_MAX_VALUES values per enumeration; (4) the farthest supertype groups go, one at a time; (5) the last own
    relations, then the last own attributes. The ladder does not depend on the question; the question only puts the
    values it names first, and shows the definition of at most MAX_VALUE_DEFINITIONS of them."""
    sg = _sg()
    members = sg.CLASS_MEMBERS if members is None else members
    directed = sg.DIRECTED_RELATIONS if directed is None else directed
    entry = (members.get("classes") or {}).get(concept)
    if not entry:
        return None
    question_words = _words(question)
    key = ontology_key(concept)
    name = shown_name(concept, members)
    supers_table, subs_table = directed.get("supers", {}), directed.get("subs", {})
    ancestors = _ancestors(concept, supers_table, members)
    groups = []
    for ancestor in ancestors:
        attributes = _member_lines(ancestor, members, question_words) if (members["classes"].get(ancestor) or {}).get("kind") != "enumeration" else []
        relations = _relation_lines(ancestor, members, directed)
        if attributes or relations:
            groups.append({"concept": ancestor, "name": shown_name(ancestor, members), "attributes": attributes, "relations": relations})
    enumeration = entry["kind"] == "enumeration"
    ordered_values: list[str] = []
    value_definitions: list[tuple[str, str]] = []
    if enumeration:
        own_values = members["values"].get(concept, [])
        named = [v for v in own_values if _named_in(v["name"], question_words)]
        ordered_values = [v["name"] for v in named + [v for v in own_values if v not in named]]
        value_definitions = [(v["name"], v["definition"]) for v in named if v["definition"]]
    parts = {
        "key": key,
        "name": name,
        "head": f"{ontology_label(concept)} {entry['kind']} {name}" + (f" ({entry['place']})" if entry.get("place") else ""),
        "definition": (directed.get("definitions", {}).get(concept) or "") if with_definition else "",
        "supers": [shown_name(s, members) for s in sorted(supers_table.get(concept, []), key=lambda c: _sort_name(c, members))],
        "subs": [shown_name(s, members) for s in sorted(subs_table.get(concept, []), key=lambda c: _sort_name(c, members))],
        "enumeration": enumeration,
        "enumeration_values": ordered_values,
        "enumeration_value_definitions": value_definitions,
        "enumeration_definition_count": sum(1 for v in members["values"].get(concept, []) if v["definition"]) if enumeration else 0,
        "attributes": [] if enumeration else _member_lines(concept, members, question_words),
        "relations": _relation_lines(concept, members, directed),
        "groups": groups,
    }
    ladder = [
        _Options(),
        _Options(definitions_inherited=False),
        _Options(definitions_inherited=False, definitions_own=False),
        _Options(definitions_inherited=False, definitions_own=False, max_values=LADDER_MAX_VALUES),
    ]
    chosen = None
    for step, options in enumerate(ladder):
        text, left_out, shown = _render(parts, options)
        if len(text) <= max_chars:
            chosen = (step, options, text, left_out, shown)
            break
    if chosen is None:
        for count in range(len(groups) - 1, -1, -1):
            options = _Options(False, False, LADDER_MAX_VALUES, groups=count)
            text, left_out, shown = _render(parts, options)
            if len(text) <= max_chars:
                chosen = (4, options, text, left_out, shown)
                break
        if chosen is None:
            options = _Options(False, False, LADDER_MAX_VALUES, groups=0)
            while True:
                text, left_out, shown = _render(parts, options)
                if len(text) <= max_chars:
                    chosen = (5, options, text, left_out, shown)
                    break
                relations = len(parts["relations"]) if options.own_relations is None else options.own_relations
                attributes = len(parts["attributes"]) if options.own_attributes is None else options.own_attributes
                if relations:
                    options = _Options(False, False, LADDER_MAX_VALUES, 0, relations - 1, options.own_attributes)
                elif attributes:
                    options = _Options(False, False, LADDER_MAX_VALUES, 0, 0, attributes - 1)
                else:
                    return None
    step, options, text, left_out, shown = chosen
    nodes, edges, has, defined = _facts(concept, name, parts, shown, supers_table, subs_table, members)
    steps = [[a, "up", b] for a, b in edges] + [[b, "down", a] for a, b in edges] + has
    return Card(concept=concept, text=text, ladder=step, left_out=left_out, nodes=nodes, steps=steps, defined=defined)


def _facts(concept: str, name: str, parts: dict, shown: dict, supers_table: dict, subs_table: dict, members: dict):
    """(nodes, is-a edges, has steps, defined names) of the card as shown: what the answer checks read."""
    nodes: list[str] = [name]
    edges: list[tuple[str, str]] = []
    has: list[list[str]] = []
    in_card = {concept: name}
    for parent in sorted(supers_table.get(concept, []), key=lambda c: _sort_name(c, members)):
        in_card[parent] = shown_name(parent, members)
    for group in shown["groups"]:
        in_card[group["concept"]] = group["name"]
    for sub in sorted(subs_table.get(concept, []), key=lambda c: _sort_name(c, members))[:MAX_SUBTYPES]:
        in_card[sub] = shown_name(sub, members)
    nodes.extend(n for c, n in in_card.items() if c != concept)
    for child, child_name in in_card.items():
        for parent in supers_table.get(child, []):
            if parent in in_card:
                edges.append((child_name, in_card[parent]))
    for owner, owner_name, relations in [(concept, name, shown["relations"])] + [(g["concept"], g["name"], g["relations"]) for g in shown["groups"]]:
        for line in relations:
            has.append([owner_name, "has", line["target_name"]])
            nodes.append(line["target_name"])
    # every class the card names (supertype, subtype, relation target, inherited group) counts as defined, as the text
    # of the record it replaces did: the card states what the model says about it, and the answer cannot misstate that
    defined = [name, *nodes]
    label = (members["classes"].get(concept) or {}).get("label")
    if label:
        defined.append(label)
    for entry in list(shown["attributes"]) + [e for g in shown["groups"] for e in g["attributes"]]:
        defined.append(entry["name"])
        if entry["type"]:
            defined.append(entry["type"])
    return list(dict.fromkeys(nodes)), list(dict.fromkeys(edges)), has, list(dict.fromkeys(defined))


# ---------------------------------------------------------------------------------------------------- the chunk


def card_chunk_id(concept: str) -> str:
    chunk_id = f"class-card-{ontology_key(concept)}-{concept.partition(':')[2]}".lower().replace(" ", "-")
    if len(chunk_id) > 120:  # RetrievalEvent.chunk_id holds 128 characters
        chunk_id = f"{chunk_id[:100]}-{abs(hash(chunk_id)) % 10**8:08d}"
    return chunk_id


def card_source_path(concept: str) -> str:
    return f"{ONTOLOGY_PATH}/{ontology_key(concept)}.ttl#class={concept.partition(':')[2]}"


def _card_fields(card: Card, members: dict) -> dict:
    concept = card.concept
    name = shown_name(concept, members)
    return {
        "chunkId": card_chunk_id(concept),
        "sourcePath": card_source_path(concept),
        "repositoryUrl": f"{STANDARD_ONTOLOGIES_URL}/{ontology_key(concept)}.ttl",
        "commitSha": "main",
        "label": f"Class card: {name} ({ontology_label(concept)})",
        "heading": card.text.split("\n", 1)[0],
        "text": card.text,
        "docType": "ontology-card",
        "chunkType": "class-card",
        "classCard": True,
        "classCardConcept": concept,
        "classCardNodes": card.nodes,
        "classCardSteps": card.steps,
        "classCardDefined": card.defined,
    }


def added_card_chunk(card: Card, members: dict) -> dict:
    """A card added after the passages and the path blocks, numbered after the last passage like a path block."""
    chunk_id = card_chunk_id(card.concept)
    return {
        "id": hash(chunk_id) % (10**8),
        **_card_fields(card, members),
        "standardsScope": [ontology_label(card.concept)],
        "structuredMetadata": {},
        "score": 1.0,
        "retrievalEventId": f"re-{uuid4().hex[:8]}",
        "classCardAdded": True,
    }


def replacing_card_chunk(card: Card, record: dict, members: dict) -> dict:
    """The card in the place of a record: the record's place, rank, score and event stay; what the record was is kept
    in replacesSourcePath, replacesRepositoryUrl and replacesChunkId, which the yardstick and locate_answer_sources read."""
    replaced = {key: value for key, value in record.items() if key not in _DROPPED_FROM_RECORD}
    return {
        **replaced,
        **_card_fields(card, members),
        "structuredMetadata": {},
        "replacesSourcePath": record.get("sourcePath", ""),
        "replacesRepositoryUrl": record.get("repositoryUrl", ""),
        "replacesChunkId": record.get("chunkId", ""),
    }


_DROPPED_FROM_RECORD = frozenset(
    {"sourceUrl", "source_url", "pieceText", "wholeRecord", "baseText", "inheritedBaseChars", "inheritedGroups", "source_path", "repository_url", "chunk_id", "commit_sha"}
)


def is_card(chunk: dict) -> bool:
    return bool(chunk.get("classCard"))


def is_added_card(chunk: dict) -> bool:
    return bool(chunk.get("classCardAdded"))


def found_source(chunk: dict) -> tuple[str, str]:
    """(repository URL, source path) of the file a served chunk stands for: the record a card replaced, else the chunk's own."""
    return (
        str(chunk.get("replacesRepositoryUrl") or chunk.get("repositoryUrl") or ""),
        str(chunk.get("replacesSourcePath") or chunk.get("sourcePath") or ""),
    )


def citation_title(source_path: str) -> str:
    """"DATEX II ontology: class Accident" for the source path of a card, else ""."""
    path, _, fragment = (source_path or "").partition("#class=")
    if not fragment or not path.startswith(f"{ONTOLOGY_PATH}/") or not path.endswith(".ttl"):
        return ""
    key = path.rsplit("/", 1)[-1].removesuffix(".ttl")
    concept = f"{key}:{fragment}"
    sg = _sg()
    entry = (getattr(sg, "CLASS_MEMBERS", {}).get("classes") or {}).get(concept) or {}
    from helpdesk.services import semantic_path

    return f"{semantic_path.ONTOLOGY_LABELS.get(key, key)} ontology: class {entry.get('label') or sg.local_own_name(fragment)}"


# ---------------------------------------------------------------------------------------------------- the answer checks


def defines(chunk: dict, element_name: str) -> bool:
    """Whether a card defines the element: its class, the enumeration types whose values it lists, the attributes it
    lists, and no other."""
    return element_name in (chunk.get("classCardDefined") or [])


def step_claim_error(sentence: str, chunk: dict) -> str | None:
    """Why a sentence that cites a card claims a step between two classes of the card that the card does not hold, or
    None. The claim shapes and the reading are those of semantic_path.step_claim_error ('X is a Y', 'X can be a Y',
    'X has Y'), against the card's supertype, subtype and relation lines (and the inherited groups it shows)."""
    from helpdesk.services import semantic_path

    return semantic_path.step_claim_error(
        sentence, {"semanticPathNodes": chunk.get("classCardNodes") or [], "semanticPathSteps": chunk.get("classCardSteps") or []}
    )


# ---------------------------------------------------------------------------------------------------- which classes get a card


def class_of_record(chunk: dict) -> str | None:
    """The class an indexed record of the chunk is the record of, else None. The record readers (the inverse of the
    function that wrote the source path) live beside the writers: datex.concept_id_of_source_path."""
    from helpdesk.services import datex

    return datex.concept_id_of_source_path(str(chunk.get("sourcePath") or ""))


_IRI_LINE = re.compile(r"^IRI:\s*(\S+)\s*$", re.MULTILINE)


def class_of_definition_block(chunk: dict) -> str | None:
    """The class an ontology definition block was made for: the concept of the 'IRI:' line its text carries."""
    if str(chunk.get("docType") or "") != "ontology-definition":
        return None
    match = _IRI_LINE.search(str(chunk.get("text") or ""))
    return _sg().iri_to_concept_id(match.group(1)) if match else None


def class_of_path_block_ends(chunks: list[dict]) -> list[str]:
    """Trigger B (a class that an end of a served path block names): NOT BUILT in step 2. The decision is Andrej's
    (plan, section 7: "whether trigger B is wanted at all"); the plan gives it its own gate in step 3. The place is
    here: with_cards would take these classes after those of trigger A, when trigger A did not already give them one."""
    return []


def with_cards(
    chunks: list[dict],
    max_passages: int,
    question: str = "",
    members: dict | None = None,
    directed: dict | None = None,
) -> tuple[list[dict], dict]:
    """chunks with a card for each class of a listed ontology that a served passage is about (trigger A), at most
    MAX_CARDS, in the order of the evidence; and {"cards": [...], "ms"}.

    Only the first max_passages passages (the six the prompt shows) are looked at. A record's card takes its place;
    a definition block's card goes to the end. A card whose net addition would take the question over MAX_NET_CHARS
    is built again down the ladder (definitions first) until it fits, and is not made when no rung fits (the record or
    block stays). A class whose members are not loaded gets no card: with no member in the graph the chunks come back
    as they were."""
    started = time.perf_counter()
    sg = _sg()
    members = sg.CLASS_MEMBERS if members is None else members
    directed = sg.DIRECTED_RELATIONS if directed is None else directed
    allowed = configured_ontologies()
    info: dict = {"cards": [], "ms": 0.0}
    if not members.get("classes"):
        info["ms"] = round((time.perf_counter() - started) * 1000, 2)
        return chunks, info
    result = list(chunks)
    added: list[dict] = []
    seen: set[str] = set()
    left = MAX_NET_CHARS
    passages = 0
    for index, chunk in enumerate(chunks):
        if chunk.get("semanticPath") or is_card(chunk) or is_added_card(chunk):
            continue
        passages += 1
        if passages > max_passages or len(info["cards"]) >= MAX_CARDS:
            break
        record = class_of_record(chunk)
        concept, trigger = (record, "record") if record else (class_of_definition_block(chunk), "definition")
        if not concept or concept in seen or ontology_key(concept) not in allowed or concept not in members["classes"]:
            continue
        replaced = len(str(chunk.get("text", ""))) if trigger == "record" else 0
        # a card longer than what is left of the question's net budget is built again down the ladder (definitions
        # first), that is, under the size that fits; it is skipped only when no rung of the ladder fits
        card = build_card(
            concept, members=members, directed=directed, question=question, with_definition=trigger == "record",
            max_chars=min(MAX_CARD_CHARS, left + replaced),
        )
        if card is None:
            continue
        net = card.chars - replaced
        seen.add(concept)
        left -= max(0, net)
        card.trigger = trigger
        if trigger == "record":
            result[index] = replacing_card_chunk(card, chunk, members)
        else:
            added.append(added_card_chunk(card, members))
        info["cards"].append(
            {
                "chunkId": card_chunk_id(concept),
                "concept": concept,
                "trigger": trigger,
                "chars": card.chars,
                "netChars": net,
                "ladder": card.ladder,
                "leftOut": card.left_out,
            }
        )
    info["ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result + added, info
