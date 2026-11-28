"""
A semantic path is evidence of its own.

A question that names two classes of one ontology is answered better when the model sees how the ontology links them.
The six passages of an answer are chosen by similarity and show a class by its own record; the classes between two
named ones (a supertype that carries the relation, the class a relation leads to) are in none of them, so the answer
said the evidence did not state how they are linked while the ontology states it.

With RETRIEVAL_SEMANTIC_PATH_ENABLED, for the classes a question names (matched in its words and not a stop-word,
loose or common-word match; a class of an opt-in source only when the question's scope names that source) a path is
searched in the ontology they belong to. A path has three kinds of step and no other:
  up    from a class to a supertype ("Accident is a TrafficElement.")
  has   from the domain of a relation to its range, in the relation's own direction ("SituationRecord has LocationReference.")
  down  from a class to a subtype ("LocationReference can be a Location.")
Never against a relation's direction. After an up step the path does not go down (that would reach a sibling, which
the ontology does not say), after a down step it does not go up. The shortest path is taken (parameters below).

A path found is one evidence block in plain sentences, one line per step, with the classes named as in the ontology.
If it stays within MAX_BLOCK_CHARS, a line per class of the path whose definition is not already in one of the served
passages follows. Nothing in the block comes from anywhere but the loaded ontology (semantic_graph.DIRECTED_RELATIONS).
The blocks are added after the served passages (they take none of the six places and are not cut by the per-source
limit, the diversity step or the trimming); the prompt builder gives them the numbers after the last passage
(prompt_window).

Off by default: nothing is added. RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES limits the blocks to the listed ontologies.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-23  |  Modified: 2026-11-23
"""

from __future__ import annotations

import heapq
import itertools
import re
from collections.abc import Iterable
from uuid import uuid4

from helpdesk.services import semantic_graph as sg

# Parameters, fixed before the first measurement.
MAX_STEPS = 8  # the longest path searched (the chain of the DATEX II question that asked for this has 8)
MAX_CONCEPTS_PER_ONTOLOGY = 8  # countable class concepts of one ontology used, in sorted order: 28 pairs, 8 searches
MAX_PATH_BLOCKS = 2  # blocks per question: the shortest paths, ties by the path itself
MAX_BLOCK_CHARS = 2400  # definition lines are added, all or none, when the whole block stays within this

STANDARD_ONTOLOGIES_URL = "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards"
ONTOLOGY_PATH = "docs/ontology/standards"
# Display names of the ontologies by concept namespace; a namespace not listed shows as itself.
ONTOLOGY_LABELS = {
    "datex": "DATEX II",
    "netex": "NeTEx",
    "siri": "SIRI",
    "opra": "OpRa",
    "transmodel": "Transmodel",
    "tnits": "TN-ITS",
}

UP, HAS, DOWN = "up", "has", "down"
# The move that may follow the last one: not down after up, not up after down.
_NEXT = {None: (UP, HAS, DOWN), UP: (UP, HAS), DOWN: (DOWN, HAS), HAS: (UP, HAS, DOWN)}


def enabled() -> bool:
    from django.conf import settings

    return bool(getattr(settings, "RETRIEVAL_SEMANTIC_PATH_ENABLED", False))


def allowed_ontologies() -> set[str]:
    """The ontology keys path blocks are produced for (RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES, comma-separated, case
    ignored); empty: no restriction."""
    from django.conf import settings

    raw = str(getattr(settings, "RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES", "") or "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def without_inside_longer_terms(question: str, candidates: Iterable[str], question_concepts: Iterable[str]) -> set[str]:
    """The candidate concepts minus those whose every match in the question lies inside a longer term that another
    concept of the question matches ("vehicle" and "journey" in "vehicle journey"): such a word is no end of a path.
    The same test as for the anchors of relation paths (semantic_graph.concepts_inside_longer_terms), made over all
    the question's concepts. A word joined by a hyphen ("multi-line") is read as it is matched: as the words around it,
    so a longer term must contain the same words."""
    return set(candidates) - sg.concepts_inside_longer_terms(question, set(question_concepts))


# ---------------------------------------------------------------------------------------------------- the ends

_HYPHENS = "-\u2010\u2011"


def _words(question: str) -> tuple[list[str], list[bool], list[bool]]:
    """The question's words as the concept matching reads them (semantic_graph.TOKEN_PATTERN on the lowercased text), and
    for each word i whether it is directly next to word i+1 (only whitespace and/or hyphens between them) and whether it is
    joined to it (only hyphens between them: one hyphenated word)."""
    lowered = (question or "").lower()
    found = [(m.group(), m.start(), m.end()) for m in sg.TOKEN_PATTERN.finditer(lowered)]
    nearby: list[bool] = []
    joined: list[bool] = []
    for (_, _, end), (_, start, _) in zip(found, found[1:]):
        gap = lowered[end:start]
        nearby.append(bool(gap) and all(ch.isspace() or ch in _HYPHENS for ch in gap))
        joined.append(bool(gap) and all(ch in _HYPHENS for ch in gap))
    return [word for word, _, _ in found], nearby, joined


def end_occurrences(question: str, concepts: Iterable[str]) -> dict[str, list[frozenset[int]]]:
    """Where each concept is named in the question, as the matcher records it (question_alias_matches): per concept the
    occurrences, each the set of the question's word indexes it stands on. For a matched alias: its words as a run of
    consecutive question words (each run is one occurrence, so a multi-word name is one occurrence), else its words
    glued into one question word, else (words scattered, or matched only through plural / prefix variants) one occurrence
    of every question word that equals or is a variant of a word of the alias."""
    words, _nearby, _joined = _words(question)
    found: dict[str, list[frozenset[int]]] = {}
    for concept, matches in sg.question_alias_matches(question, concepts).items():
        occurrences: list[frozenset[int]] = []
        for alias, _as_written in matches:
            tokens = list(sg._alias_tokens(alias))
            size = len(tokens)
            hits = [frozenset(range(i, i + size)) for i in range(len(words) - size + 1) if words[i : i + size] == tokens]
            if size > 1:
                glued = "".join(tokens)
                hits += [frozenset({i}) for i, word in enumerate(words) if word == glued]
            if not hits:
                scattered = frozenset(
                    i for i, word in enumerate(words) if any(sg._word_variant_kind(token, word) for token in tokens)
                )
                hits = [scattered] if scattered else []
            occurrences.extend(hit for hit in hits if hit not in occurrences)
        if occurrences:
            found[concept] = occurrences
    return found


def inside_compounds(question: str, candidates: Iterable[str]) -> set[str]:
    """Rule H: the candidates every occurrence of which lies inside a hyphenated compound ("line" in "multi-line").
    A compound is a chain of at least two question words with only hyphens between them; an occurrence is inside one when
    all its words lie in it and it has more words than the occurrence (an occurrence that is the whole compound is not
    inside it). A class that is named anywhere else, as a word of its own, stays."""
    words, _nearby, joined = _words(question)
    chain_of: dict[int, range] = {}
    start = 0
    for index in range(len(words)):
        if index == len(words) - 1 or not joined[index]:
            for member in range(start, index + 1):
                chain_of[member] = range(start, index + 1)
            start = index + 1
    inside: set[str] = set()
    for concept, occurrences in end_occurrences(question, candidates).items():
        if all(
            (chain := chain_of.get(min(occurrence))) is not None
            and len(chain) > len(occurrence)
            and all(member in chain for member in occurrence)
            for occurrence in occurrences
        ):
            inside.add(concept)
    return inside


def path_end_concepts(question: str, candidates: Iterable[str], question_concepts: Iterable[str]) -> set[str]:
    """The concepts a path may end in: the candidates minus those inside a longer term (without_inside_longer_terms)
    and minus those named only by a part of a hyphenated compound (inside_compounds)."""
    ends = without_inside_longer_terms(question, candidates, question_concepts)
    return ends - inside_compounds(question, ends) if ends else ends


def phrase_pairs(question: str, ends: Iterable[str]) -> list[list[str]]:
    """Rule P: the pairs of ends of one ontology that the question names as one phrase, as sorted [a, b] lists. Two words
    are directly next to each other when only whitespace and/or hyphens lie between them (a word between them, a stop word
    too, or any other character, breaks it). Two occurrences are next to each other when they share no word and a word of one
    is directly next to a word of the other; one adjacent combination of occurrences is enough. A path joins two things the
    question names separately, so such a pair gets none."""
    _words_found, nearby, _joined = _words(question)

    def adjacent(first: frozenset[int], second: frozenset[int]) -> bool:
        if first & second:
            return False
        return any((i + 1 in second and nearby[i]) or (i - 1 in second and nearby[i - 1]) for i in first)

    occurrences = end_occurrences(question, ends)
    pairs = []
    for first, second in itertools.combinations(sorted(occurrences), 2):
        if _namespace(first) == _namespace(second) and any(
            adjacent(a, b) for a in occurrences[first] for b in occurrences[second]
        ):
            pairs.append([first, second])
    return pairs


def dropped_pairs(parts: Iterable[tuple[Iterable[str], Iterable[Iterable[str]]]]) -> set[frozenset[str]]:
    """The pairs to leave out when a question was searched as asked and in its English rendering: each part is (the ends
    of one text, the phrase pairs of that text). A pair is dropped when it is a phrase pair in every text in which both
    its ends were found; a pair whose ends were found in different texts is never dropped."""
    parts = [(set(ends), {frozenset(pair) for pair in pairs}) for ends, pairs in parts]
    dropped: set[frozenset[str]] = set()
    for pair in set().union(*(pairs for _ends, pairs in parts)) if parts else ():
        holding = [pairs for ends, pairs in parts if pair <= ends]
        if holding and all(pair in pairs for pairs in holding):
            dropped.add(pair)
    return dropped


def ontology_namespaces(data: dict | None = None) -> set[str]:
    """The ontology keys a path block can be made for: the namespaces of the concepts the loaded ontology holds moves for."""
    data = sg.DIRECTED_RELATIONS if data is None else data
    ids: set[str] = set()
    for table in (data.get("supers") or {}, data.get("subs") or {}):
        for key, values in table.items():
            ids.add(key)
            ids.update(values)
    for key, values in (data.get("out") or {}).items():
        ids.add(key)
        ids.update(target for target, _name in values)
    return {concept.partition(":")[0] for concept in ids if ":" in concept}


def is_path_ontology_url(url: str, data: dict | None = None) -> bool:
    """Whether the URL is the repository link of a path block: the ontology file of an ontology the app has loaded
    (what build_block cites). The policy accepts it for what it is, so the accepted files cannot fall behind the
    ontologies that can produce a block."""
    base = (url or "").split("#", 1)[0].split("?", 1)[0]
    prefix = f"{STANDARD_ONTOLOGIES_URL}/"
    if not base.startswith(prefix) or not base.endswith(".ttl"):
        return False
    name = base[len(prefix) : -len(".ttl")]
    return bool(name) and "/" not in name and name in ontology_namespaces(data)


def _namespace(concept_id: str) -> str:
    return concept_id.partition(":")[0]


def ontology_label(concept_id: str) -> str:
    namespace = _namespace(concept_id)
    return ONTOLOGY_LABELS.get(namespace, namespace)


# ---------------------------------------------------------------------------------------------------- search


def search_from(source: str, data: dict, max_steps: int | None = None) -> dict[str, tuple]:
    """The best path from `source` to every concept it reaches in at most max_steps steps, inside the source's own
    ontology: {target: (steps, inheritance steps, path)}, a path a tuple of (kind, name, concept) per step.

    Best: fewest steps; then fewest up and down steps (a path through relations over one through inheritance);
    then the path that is smaller as a sequence of (kind, name, concept) tuples, compared left to right ("down"
    before "has" before "up", then the relation's name, then the concept). Dijkstra over (concept, last kind);
    each step costs 1."""
    max_steps = MAX_STEPS if max_steps is None else max_steps
    namespace = _namespace(source)
    best: dict[str, tuple] = {}
    done: set[tuple[str, str | None]] = set()
    heap: list[tuple] = [(0, 0, (), source, None)]
    while heap:
        steps, inherited, path, node, last = heapq.heappop(heap)
        if (node, last) in done:
            continue
        done.add((node, last))
        if node != source and node not in best:
            best[node] = (steps, inherited, path)
        if steps >= max_steps:
            continue
        for kind in _NEXT[last]:
            if kind == UP:
                moves = [(UP, "", target) for target in data["supers"].get(node, ())]
            elif kind == DOWN:
                moves = [(DOWN, "", target) for target in data["subs"].get(node, ())]
            else:
                moves = [(HAS, name, target) for target, name in data["out"].get(node, ())]
            for move in moves:
                target = move[2]
                if _namespace(target) != namespace or target == source or (target, kind) in done:
                    continue
                heapq.heappush(
                    heap, (steps + 1, inherited + (kind != HAS), path + (move,), target, kind)
                )
    return best


def find_paths(concepts: Iterable[str], data: dict | None = None, dropped: Iterable[frozenset[str]] = ()) -> list[dict]:
    """The paths between the concepts: at most MAX_PATH_BLOCKS of them, the shortest first.

    Concepts of one ontology are paired (both orders of a pair are searched, the shorter path is kept; on equal
    length the one of the smaller sequence). A concept that is not a class (sg._is_class_concept) is left out; of
    one ontology the first MAX_CONCEPTS_PER_ONTOLOGY in sorted order are used. Returns
    [{"source", "target", "steps", "path"}]; none when fewer than two classes of one ontology are given. A pair in
    `dropped` (phrase_pairs) is not searched: no block and no cover of other pairs."""
    dropped = {frozenset(pair) for pair in dropped}
    data = sg.DIRECTED_RELATIONS if data is None else data
    if not data.get("out") and not data.get("supers") and not data.get("subs"):
        return []
    by_ontology: dict[str, list[str]] = {}
    for concept in sorted(set(concepts)):
        if sg._is_class_concept(concept):
            by_ontology.setdefault(_namespace(concept), []).append(concept)
    found: list[tuple] = []
    for members in by_ontology.values():
        members = members[:MAX_CONCEPTS_PER_ONTOLOGY]
        if len(members) < 2:
            continue
        reached = {member: search_from(member, data) for member in members}
        for index, first in enumerate(members):
            for second in members[index + 1 :]:
                if frozenset((first, second)) in dropped:
                    continue
                options = [
                    (reached[a][b][0], reached[a][b][1], reached[a][b][2], a, b)
                    for a, b in ((first, second), (second, first))
                    if b in reached[a]
                ]
                if options:
                    steps, inherited, path, a, b = min(options, key=lambda option: option[:3] + (option[3],))
                    found.append((steps, inherited, a, b, path))
    # A class the question names that lies inside the path between two others is covered by that path: the pairs
    # that end in it are left out (Accident, Location, Lane: the path Accident to Lane passes through Location).
    inner = {
        index: {move[2] for move in row[4][:-1]} for index, row in enumerate(found)
    }
    kept = [
        row
        for index, row in enumerate(found)
        if not any(
            other != index and (row[2] in nodes or row[3] in nodes) for other, nodes in inner.items()
        )
    ] or found
    kept.sort(key=lambda row: row[:4])
    return [{"source": a, "target": b, "steps": steps, "path": path} for steps, _inherited, a, b, path in kept[:MAX_PATH_BLOCKS]]


# ---------------------------------------------------------------------------------------------------- block


def display_names(nodes: list[str]) -> dict[str, str]:
    """The classes named as in the ontology: the own name, the local name where two classes of the path share one."""
    own = {node: sg.concept_own_name(node) for node in nodes}
    shared = {name for name in own.values() if list(own.values()).count(name) > 1}
    return {node: (node.partition(":")[2] if own[node] in shared else own[node]) for node in nodes}


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def step_line(kind: str, name: str, source: str, target: str, names: dict[str, str]) -> str:
    a, b = names[source], names[target]
    if kind == UP:
        return f"{a} is {_article(b)} {b}."
    if kind == DOWN:
        return f"{a} can be {_article(b)} {b}."
    label = sg.local_own_name(name)
    if not label or label.lower() == sg.concept_own_name(target).lower():
        return f"{a} has {b}."
    return f"{a} has {b} (relation `{label}`)."


def _normal(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _covered(definition: str, passages: list[str]) -> bool:
    """Whether the definition (its first words) is already in a served passage."""
    head = _normal(definition)[:80]
    return bool(head) and any(head in _normal(text) for text in passages)


def build_block(found: dict, passage_texts: list[str], data: dict | None = None) -> dict:
    """One evidence block (a chunk dict) for a path found by find_paths."""
    data = sg.DIRECTED_RELATIONS if data is None else data
    source, target, path = found["source"], found["target"], found["path"]
    nodes = [source] + [move[2] for move in path]
    names = display_names(list(dict.fromkeys(nodes)))
    prefix = _namespace(source)
    label = ontology_label(source)
    heading = f"Semantic path in the {label} ontology: {names[source]} to {names[target]}"
    lines = [heading]
    steps: list[list[str]] = []
    previous = source
    for kind, name, node in path:
        lines.append(step_line(kind, name, previous, node, names))
        steps.append([names[previous], kind, names[node]])
        previous = node
    lines.append(
        f"These steps are from the {label} ontology ({ONTOLOGY_PATH}/{prefix}.ttl): each is a supertype, "
        "a relation in its own direction, or a subtype."
    )
    definitions = [
        (node, data["definitions"][node])
        for node in dict.fromkeys(nodes)
        if node in data["definitions"] and not _covered(data["definitions"][node], passage_texts)
    ]
    defined: list[str] = []
    if definitions:
        extra = [f"{names[node]}: {definition}" for node, definition in definitions]
        if len("\n".join(lines + ["Definitions of classes on the path:"] + extra)) <= MAX_BLOCK_CHARS:
            lines.append("Definitions of classes on the path:")
            lines.extend(extra)
            defined = [names[node] for node, _definition in definitions]
    text = "\n".join(lines)
    local_a, local_b = source.partition(":")[2], target.partition(":")[2]
    chunk_id = f"semantic-path-{prefix}-{local_a}-{local_b}".lower()
    if len(chunk_id) > 120:  # RetrievalEvent.chunk_id holds 128 characters
        chunk_id = f"{chunk_id[:100]}-{abs(hash(chunk_id)) % 10**8:08d}"
    return {
        "id": hash(chunk_id) % (10**8),
        "chunkId": chunk_id,
        "sourcePath": f"{ONTOLOGY_PATH}/{prefix}.ttl#path={local_a}={local_b}",
        "repositoryUrl": f"{STANDARD_ONTOLOGIES_URL}/{prefix}.ttl",
        "commitSha": "main",
        "label": f"Semantic path: {names[source]} to {names[target]}",
        "heading": heading,
        "text": text,
        "docType": "ontology-path",
        "chunkType": "semantic-path",
        "standardsScope": [label],
        "structuredMetadata": {},
        "score": 1.0,
        "retrievalEventId": f"re-{uuid4().hex[:8]}",
        "semanticPath": True,
        "semanticPathSteps": steps,
        "semanticPathNodes": [names[node] for node in dict.fromkeys(nodes)],
        "semanticPathDefined": defined,
    }


def path_blocks(
    concepts: Iterable[str], served: list[dict], data: dict | None = None, dropped: Iterable[frozenset[str]] = ()
) -> list[dict]:
    """The blocks for the concepts a question names, given the passages already served (their texts decide which
    definitions are left out)."""
    allowed = allowed_ontologies()
    if allowed:
        concepts = [concept for concept in concepts if _namespace(concept).lower() in allowed]
    found = find_paths(concepts, data, dropped)
    if not found:
        return []
    texts = [str(chunk.get("text", "")) for chunk in served if not chunk.get("semanticPath")]
    return [build_block(item, texts, data) for item in found]


def citation_title(source_path: str) -> str:
    """"DATEX II ontology: path Accident to Lane" for the source path of a block, else ""."""
    path, _, fragment = (source_path or "").partition("#path=")
    if not fragment or not path.startswith(f"{ONTOLOGY_PATH}/"):
        return ""
    prefix = path.rsplit("/", 1)[-1].removesuffix(".ttl")
    first, _, second = fragment.partition("=")
    own = sg.local_own_name
    return f"{ONTOLOGY_LABELS.get(prefix, prefix)} ontology: path {own(first)} to {own(second)}"


# ---------------------------------------------------------------------------------------------------- evidence list


def is_path_block(chunk: dict) -> bool:
    """An evidence block added after the passages and numbered after them: a path block, or a class card added after
    an ontology definition block (services/class_card.py). A card that took a record's place is a passage."""
    return bool(chunk.get("semanticPath") or chunk.get("classCardAdded"))


def prompt_window(chunks: list[dict], max_chunks: int) -> list[dict]:
    """The evidence the prompt shows: the first max_chunks passages, then every path block. The blocks take no
    place of the passages. Idempotent."""
    passages = [chunk for chunk in chunks if not is_path_block(chunk)]
    blocks = [chunk for chunk in chunks if is_path_block(chunk)]
    return passages[:max_chunks] + blocks


def carry(previous: list[dict], current: list[dict]) -> list[dict]:
    """current with the path blocks of previous that it does not have, after its passages."""
    have = {chunk.get("chunkId") for chunk in current if is_path_block(chunk)}
    return list(current) + [chunk for chunk in previous if is_path_block(chunk) and chunk.get("chunkId") not in have]


# ---------------------------------------------------------------------------------------------------- the sentence check

_NAME = r"`?(?P<{tag}>{names})`?"
_HAS_DETERMINER = r"(?:(?:an?|the)\s+)?(?:(?:direct|immediate)\s+)?"
# "X has the supertype Y" says Y is above X, and "X has the subtype Y" says Y is below X: a claim of the up and the down
# kind. The has reading below must not take those words for a link between the two classes.
_UP_VERB = (
    r"(?:is\s+(?:an?|one)\s+|is\s+an?\s+(?:kind|type|subtype)\s+of\s+|inherits\s+from\s+|extends\s+|specialises\s+|specializes\s+"
    r"|has\s+" + _HAS_DETERMINER + r"supertypes?\s+)(?:the\s+)?"
)
_DOWN_VERB = r"(?:can\s+be\s+(?:an?\s+)?|has\s+" + _HAS_DETERMINER + r"subtypes?\s+)"
_HAS_VERB = (
    r"(?:has|have|holds?|carries|carry|contains?|links?\s+to|is\s+linked\s+to|references?|refers?\s+to|points?\s+to)"
    r"\s+(?!(?:(?:an?|the|one|its|their)\s+)?(?:\w+\s+){0,2}?(?:super|sub)types?\b)"
    r"(?:(?:an?|the|one|its|their)\s+)?(?:\w+\s+){0,2}?"
)
_KINDS = ((UP, _UP_VERB), (DOWN, _DOWN_VERB), (HAS, _HAS_VERB))


def _closure(steps: list[list[str]], kind: str) -> dict[str, set[str]]:
    """For each class, the classes reached from it by consecutive steps of one kind of the path."""
    nxt: dict[str, set[str]] = {}
    for a, k, b in steps:
        if k == kind:
            nxt.setdefault(a, set()).add(b)
    reach: dict[str, set[str]] = {}
    for start in nxt:
        seen, stack = set(), [start]
        while stack:
            for follower in nxt.get(stack.pop(), ()):
                if follower not in seen:
                    seen.add(follower)
                    stack.append(follower)
        reach[start] = seen
    return reach


def _holds(kind: str, first: str, second: str, steps: list[list[str]]) -> bool:
    """Whether the block holds the claim 'first <kind> second'. up: first reaches second by up steps; down: by down
    steps; has: a has step from a class first reaches by up steps (first inherits it) to a class that reaches second
    by down steps (second is a subtype of what the relation leads to), second itself included."""
    up, down = _closure(steps, UP), _closure(steps, DOWN)
    if kind == UP:
        return second in up.get(first, ())
    if kind == DOWN:
        return second in down.get(first, ())
    owners = {first} | up.get(first, set())
    return any(
        a in owners and (b == second or second in down.get(b, ()))
        for a, k, b in steps
        if k == HAS
    )


_ROLE_AFTER = re.compile(r"\s+(?:\w+\s+){0,4}?(?P<role>super|sub)types?\b", re.IGNORECASE)


def _linked_by_is_a(first: str, second: str, steps: list[list[str]]) -> bool:
    """Whether the block links the two classes by supertype or subtype steps, in either direction."""
    reach = {kind: _closure(steps, kind) for kind in (UP, DOWN)}
    return any(second in reach[kind].get(first, ()) or first in reach[kind].get(second, ()) for kind in reach)


def step_claim_error(sentence: str, chunk: dict) -> str | None:
    """Why a sentence that cites a path block claims a step the block does not hold, or None.

    Only a claim in the shape 'X <verb> Y' with X and Y classes of the block is read: 'X is a Y' (up), 'X can be a Y'
    (down), 'X has Y' and its synonyms (has). The claim holds when the block's steps give it (see _holds); a claim
    against a relation's direction or between classes the path does not link fails. A sentence in another shape is
    left to the other checks."""
    nodes = [str(name) for name in chunk.get("semanticPathNodes") or []]
    steps = chunk.get("semanticPathSteps") or []
    if len(nodes) < 2 or not steps:
        return None
    alternatives = "|".join(re.escape(name) for name in sorted(nodes, key=len, reverse=True))
    plain = re.sub(r"\[E\d+\]", " ", sentence)
    for kind, verb in _KINDS:
        pattern = re.compile(
            r"(?<![\w.])" + _NAME.format(tag="a", names=alternatives) + r"\s+" + verb
            + _NAME.format(tag="b", names=alternatives) + r"(?![\w.])"
        )
        for found in pattern.finditer(plain):
            first, second = found.group("a"), found.group("b")
            if first == second:
                continue
            read = kind
            if kind == HAS and _linked_by_is_a(first, second, steps):
                # the block links the two by a supertype or subtype step, so 'has' is not ownership here; where the
                # sentence says which way ("... as its supertype"), that way is judged, else the has reading stays
                role = _ROLE_AFTER.match(plain, found.end())
                if role:
                    read = UP if role.group("role").lower() == "super" else DOWN
            if not _holds(read, first, second, steps):
                wording = {UP: "is a", DOWN: "can be", HAS: "has"}[read]
                return (
                    f"The sentence says '{first} {wording} {second}', a step the cited block does not hold: "
                    f"'{sentence[:150].strip()}'. State only the steps of the path block, in their direction."
                )
    return None


def defines(chunk: dict, element_name: str) -> bool:
    """Whether a path block gives the definition of the class (it holds a definition line for it)."""
    return element_name in (chunk.get("semanticPathDefined") or [])
