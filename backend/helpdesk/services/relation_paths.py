"""
Relation-path evidence: answer "how is X related to Y" from the ontology graph.

Retrieval otherwise only feeds the answer generator text chunks (definitions,
XSD excerpts), so a relation that exists only as a typed edge in the graph
never reaches it -- e.g. NeTEx models ServiceJourney --LineRef--> Line, but a
question about "line and journey" only ever got the two definitions.

This module finds short typed paths between the concepts a question names and
renders each path as an evidence chunk citing the XSD that declares each step.

Traversal rules:
- owl:ObjectProperty edges (domain/range, either direction), cost 1.
- rdfs:subClassOf only from a named concept down to its subclasses, at the two
  ends of a path (cost 0.5 per step): "a Journey's subtype ServiceJourney
  references a Line". Never upward: every class climbs to framework roots
  such as netex:DataManagedObject.
- skos:related is ignored: in netex.ttl it is a copy of each object property
  with the property name dropped.
- Intermediate nodes pay a hub penalty growing with their degree, so a path
  through a generic class (AccessibilityAssessment, PrivateCode) ranks below
  a specific one.
"""

from __future__ import annotations

import logging
import math
import re
import time
from dataclasses import dataclass, field
from itertools import combinations

from helpdesk.services.graphdb_client import (
    TRANSMODEL_ALIGNED_STANDARDS,
    _iri_to_concept_id,
    execute_sparql_query,
)

logger = logging.getLogger(__name__)

STANDARD_GRAPHS = tuple(f"https://napcore.eu/graph/standards/{standard}" for standard in TRANSMODEL_ALIGNED_STANDARDS)
STANDARD_LABELS = {"netex": "NeTEx", "siri": "SIRI", "opra": "OpRa"}
STANDARD_REPOSITORIES = {"netex": "NeTEx", "siri": "SIRI", "opra": "OpRa"}

MAX_PATH_EDGES = 3
MAX_SPECIALIZATION_DEPTH = 2
SUBCLASS_STEP_COST = 0.5
PROPERTY_STEP_COST = 1.0
CACHE_TTL_SECONDS = 3600

_RELATION_QUESTION = re.compile(
    r"\b(relation|relations|relationship|relationships|related|relate|relates|link|linked|links|"
    r"connect|connected|connection|connects|between|associated|association)\b",
    re.IGNORECASE,
)
_PROVENANCE = re.compile(r"Extracted from:\s*(?P<xsd>\S+)\s*\((?P<mechanism>[^)]+)\)")

_cache: dict[tuple[str, str], tuple[float, "RelationGraph"]] = {}


@dataclass(frozen=True)
class PropertyEdge:
    domain: str
    range: str
    element: str
    iri_local: str
    xsd: str
    mechanism: str

    def other(self, node: str) -> str:
        return self.range if node == self.domain else self.domain


@dataclass
class RelationGraph:
    adjacency: dict[str, list[PropertyEdge]] = field(default_factory=dict)
    narrower: dict[str, set[str]] = field(default_factory=dict)

    def degree(self, node: str) -> int:
        return len({edge.other(node) for edge in self.adjacency.get(node, [])})

    def knows(self, node: str) -> bool:
        return node in self.adjacency or node in self.narrower


@dataclass(frozen=True)
class RelationPath:
    source: str
    target: str
    down_from_source: tuple[tuple[str, str], ...]
    properties: tuple[PropertyEdge, ...]
    down_from_target: tuple[tuple[str, str], ...]
    cost: float

    @property
    def edge_count(self) -> int:
        return len(self.down_from_source) + len(self.properties) + len(self.down_from_target)


def is_relation_question(question: str) -> bool:
    return bool(_RELATION_QUESTION.search(question or ""))


def element_name(iri_local: str, domain_local: str, mechanism: str) -> str:
    """XSD element name of a generated property IRI.

    build_netex_ttl_with_properties.py lowercases the first letter and suffixes
    "_<Domain>" when a name is used by several domains (lineRef_ServiceJourney).
    References and single containments come from capitalised element refs
    (LineRef); containment lists from lower-case wrapper elements (journeys).
    """
    name = iri_local
    suffix = f"_{domain_local}"
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    if mechanism in {"reference", "containment"} and name:
        name = name[0].upper() + name[1:]
    return name


def _local(concept_id: str) -> str:
    return concept_id.split(":", 1)[-1]


def build_relation_graph(property_rows: list[dict], subclass_rows: list[dict]) -> RelationGraph:
    graph = RelationGraph()
    for row in property_rows:
        domain = _iri_to_concept_id(row.get("domain", ""))
        range_ = _iri_to_concept_id(row.get("range", ""))
        prop_iri = row.get("prop", "")
        if not domain or not range_ or domain == range_ or not prop_iri:
            continue
        iri_local = re.split(r"[#/]", prop_iri)[-1]
        match = _PROVENANCE.search(row.get("comment", "") or "")
        xsd = match.group("xsd") if match else ""
        mechanism = match.group("mechanism") if match else ""
        edge = PropertyEdge(
            domain=domain,
            range=range_,
            element=element_name(iri_local, _local(domain), mechanism),
            iri_local=iri_local,
            xsd=xsd,
            mechanism=mechanism,
        )
        graph.adjacency.setdefault(domain, []).append(edge)
        graph.adjacency.setdefault(range_, []).append(edge)
    for row in subclass_rows:
        subclass = _iri_to_concept_id(row.get("sub", ""))
        superclass = _iri_to_concept_id(row.get("super", ""))
        if subclass and superclass and subclass != superclass:
            graph.narrower.setdefault(superclass, set()).add(subclass)
    return graph


def load_relation_graph(
    *,
    endpoint: str,
    repository: str,
    username: str = "",
    password: str = "",
    timeout_seconds: int = 10,
) -> RelationGraph | None:
    """Typed property and subclass edges of the standards graphs, cached per process."""
    key = (endpoint, repository)
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    graph_values = " ".join(f"<{graph}>" for graph in STANDARD_GRAPHS)
    property_query = f"""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?prop ?domain ?range ?comment WHERE {{
      VALUES ?g {{ {graph_values} }}
      GRAPH ?g {{
        ?prop a owl:ObjectProperty ; rdfs:domain ?domain ; rdfs:range ?range .
        OPTIONAL {{ ?prop rdfs:comment ?comment . FILTER(CONTAINS(STR(?comment), "Extracted from")) }}
      }}
    }}
    """
    subclass_query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?sub ?super WHERE {{
      VALUES ?g {{ {graph_values} }}
      GRAPH ?g {{ ?sub rdfs:subClassOf ?super . FILTER(isIRI(?super)) }}
    }}
    """
    rows: list[list[dict]] = []
    for query in (property_query, subclass_query):
        result = execute_sparql_query(
            sparql_query=query,
            endpoint=endpoint,
            repository=repository,
            username=username,
            password=password,
            timeout_seconds=timeout_seconds,
        )
        if result is None:
            return None
        rows.append(
            [
                {name: value.get("value", "") for name, value in binding.items()}
                for binding in result.get("results", {}).get("bindings", [])
            ]
        )
    graph = build_relation_graph(rows[0], rows[1])
    _cache[key] = (time.monotonic(), graph)
    logger.info(
        "Loaded relation graph: %d nodes with properties, %d classes with subclasses",
        len(graph.adjacency),
        len(graph.narrower),
    )
    return graph


def _specializations(graph: RelationGraph, anchors: set[str]) -> dict[str, tuple[str, tuple[tuple[str, str], ...]]]:
    """Each anchor and its subclasses (down to MAX_SPECIALIZATION_DEPTH), with the
    anchor it came from and the chain of (superclass, subclass) steps."""
    reached: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {anchor: (anchor, ()) for anchor in anchors}
    frontier = list(anchors)
    for _ in range(MAX_SPECIALIZATION_DEPTH):
        next_frontier = []
        for node in frontier:
            anchor, chain = reached[node]
            for subclass in sorted(graph.narrower.get(node, ())):
                if subclass not in reached:
                    reached[subclass] = (anchor, chain + ((node, subclass),))
                    next_frontier.append(subclass)
        frontier = next_frontier
    return reached


def _hub_penalty(graph: RelationGraph, node: str) -> float:
    return 0.5 * math.log2(1 + graph.degree(node) / 8)


def find_relation_paths(
    graph: RelationGraph,
    sources: set[str],
    targets: set[str],
    max_paths: int = 3,
) -> list[RelationPath]:
    sources = {node for node in sources if graph.knows(node)}
    targets = {node for node in targets if graph.knows(node)} - sources
    if not sources or not targets:
        return []

    from_source = _specializations(graph, sources)
    from_target = _specializations(graph, targets)
    found: list[RelationPath] = []

    # One concept is a subtype of the other: the hierarchy itself is the relation.
    for target in targets:
        if target in from_source and from_source[target][1]:
            anchor, chain = from_source[target]
            found.append(RelationPath(anchor, target, chain, (), (), SUBCLASS_STEP_COST * len(chain)))
    for source in sources:
        if source in from_target and from_target[source][1]:
            anchor, chain = from_target[source]
            found.append(RelationPath(source, anchor, (), (), chain, SUBCLASS_STEP_COST * len(chain)))

    def walk(start: str, node: str, visited: set[str], steps: tuple[PropertyEdge, ...], budget: int) -> None:
        for edge in graph.adjacency.get(node, []):
            nxt = edge.other(node)
            if nxt in visited:
                continue
            path_steps = steps + (edge,)
            if nxt in from_target:
                target_anchor, target_chain = from_target[nxt]
                source_anchor, source_chain = from_source[start]
                if len(source_chain) + len(path_steps) + len(target_chain) <= MAX_PATH_EDGES:
                    intermediates = [step_node for step_node in _nodes_along(start, path_steps)[1:-1]]
                    cost = (
                        SUBCLASS_STEP_COST * (len(source_chain) + len(target_chain))
                        + PROPERTY_STEP_COST * len(path_steps)
                        + sum(_hub_penalty(graph, step_node) for step_node in intermediates)
                    )
                    found.append(
                        RelationPath(source_anchor, target_anchor, source_chain, path_steps, target_chain, cost)
                    )
                continue
            if len(path_steps) < budget:
                walk(start, nxt, visited | {nxt}, path_steps, budget)

    for start, (_anchor, chain) in from_source.items():
        if start in from_target:
            continue
        budget = MAX_PATH_EDGES - len(chain)
        if budget >= 1:
            walk(start, start, {start}, (), budget)

    found.sort(key=lambda path: (path.cost, path.edge_count, _signature(path)))
    unique: list[RelationPath] = []
    seen: set[tuple] = set()
    for path in found:
        signature = tuple((edge.domain, edge.element, edge.range) for edge in path.properties) or _signature(path)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(path)
        if len(unique) >= max_paths:
            break
    return unique


def _nodes_along(start: str, steps: tuple[PropertyEdge, ...]) -> list[str]:
    nodes = [start]
    for edge in steps:
        nodes.append(edge.other(nodes[-1]))
    return nodes


def _signature(path: RelationPath) -> tuple:
    return (path.down_from_source, tuple(edge.iri_local for edge in path.properties), path.down_from_target)


def anchor_groups(question_concepts: set[str], concept_to_transmodel: dict[str, str], transmodel_to_concepts: dict[str, set[str]]) -> list[set[str]]:
    """Group the question's concepts by the thing they name (netex:Line and
    transmodel:LINE are one anchor), as standard-namespace concept IDs."""
    groups: dict[str, set[str]] = {}
    for concept in sorted(question_concepts):
        if concept.startswith("transmodel:"):
            groups.setdefault(concept, set()).update(transmodel_to_concepts.get(concept, set()))
        else:
            groups.setdefault(concept_to_transmodel.get(concept, concept), set()).add(concept)
    return [members for _key, members in sorted(groups.items()) if members]


def relation_paths_for_question(
    graph: RelationGraph,
    question_concepts: set[str],
    concept_to_transmodel: dict[str, str],
    transmodel_to_concepts: dict[str, set[str]],
    max_pairs: int = 3,
    max_paths_per_pair: int = 2,
) -> list[RelationPath]:
    groups = [group for group in anchor_groups(question_concepts, concept_to_transmodel, transmodel_to_concepts)
              if any(graph.knows(node) for node in group)]
    paths: list[RelationPath] = []
    for source_group, target_group in list(combinations(groups, 2))[:max_pairs]:
        paths.extend(find_relation_paths(graph, source_group, target_group, max_paths=max_paths_per_pair))
    return paths


_VERBS = {"reference": "references", "containment": "contains", "containment-list": "contains a list of"}


def _xsd_path(xsd: str) -> str:
    return xsd if xsd.startswith("xsd/") else f"xsd/{xsd}"


def describe_path(path: RelationPath) -> tuple[str, list[str]]:
    """One-line path notation and one sentence per step."""
    lines: list[str] = []
    notation = [_local(path.source)]
    for superclass, subclass in path.down_from_source:
        lines.append(f"{_local(subclass)} is a subclass of {_local(superclass)} (rdfs:subClassOf, from the XSD type extension).")
        notation.append(f"⊃ {_local(subclass)}")
    current = path.down_from_source[-1][1] if path.down_from_source else path.source
    for edge in path.properties:
        verb = _VERBS.get(edge.mechanism, "is linked to")
        where = f", declared in {_xsd_path(edge.xsd)}" if edge.xsd else ""
        lines.append(f"{_local(edge.domain)} {verb} {_local(edge.range)} through the {edge.element} element ({edge.mechanism or 'property'}{where}).")
        nxt = edge.other(current)
        arrow = f"—{edge.element}→" if edge.domain == current else f"←{edge.element}—"
        notation.append(f"{arrow} {_local(nxt)}")
        current = nxt
    for superclass, subclass in reversed(path.down_from_target):
        lines.append(f"{_local(subclass)} is a subclass of {_local(superclass)} (rdfs:subClassOf, from the XSD type extension).")
        notation.append(f"⊂ {_local(superclass)}")
    return " ".join(notation), lines


def supporting_subclass_chunks(paths: list[RelationPath], limit: int = 2) -> list:
    """Indexed XSD complexType chunks that show a path's subclass step, e.g.
    ServiceJourney_VersionStructure with extension base="Journey_VersionStructure".

    The property steps themselves usually cannot be backed by an indexed chunk:
    NeTEx declares most elements inside xsd:group definitions, which the XSD
    indexer does not chunk, so the path chunk links to the XSD file instead.
    """
    from helpdesk.models import SourceChunk

    found = []
    seen: set[int] = set()
    for path in paths:
        for superclass, subclass in (*path.down_from_source, *path.down_from_target):
            chunk = (
                SourceChunk.objects.filter(
                    doc_type="xsd-definition",
                    label__startswith=f"XSD Definition: {_local(subclass)}_",
                    text__contains=f'base="{_local(superclass)}_',
                )
                .order_by("id")
                .first()
            )
            if chunk is not None and chunk.id not in seen:
                seen.add(chunk.id)
                found.append(chunk)
                if len(found) >= limit:
                    return found
    return found


def format_relation_paths_as_chunks(paths: list[RelationPath], commit_shas: dict[str, str] | None = None) -> list[dict]:
    chunks: list[dict] = []
    for index, path in enumerate(paths):
        prefix = path.source.split(":", 1)[0]
        standard = STANDARD_LABELS.get(prefix, prefix)
        notation, steps = describe_path(path)
        text = "\n".join(
            [
                f"RELATION PATH ({standard}): {_local(path.source)} → {_local(path.target)}",
                f"Path: {notation}",
                "Steps:",
                *(f"{number}. {step}" for number, step in enumerate(steps, start=1)),
                f"Derived from the {standard} ontology (docs/ontology/standards/{prefix}.ttl), generated from the {standard} XSD.",
            ]
        )
        decisive = next((edge for edge in path.properties if edge.xsd), None)
        fragment = decisive.iri_local if decisive else _local(path.target)
        source_path = f"docs/ontology/standards/{prefix}.ttl#{fragment}"
        commit_sha = (commit_shas or {}).get(standard) or "main"
        if decisive:
            repository_url = (
                f"https://github.com/TransmodelEcosystem/{STANDARD_REPOSITORIES.get(prefix, standard)}"
                f"/blob/{commit_sha}/{_xsd_path(decisive.xsd)}"
            )
        else:
            repository_url = f"https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards/{prefix}.ttl"
        chunk_id = f"relation-path-{_local(path.source)}-{_local(path.target)}-{index}".lower()
        chunks.append(
            {
                "id": hash(chunk_id) % (10**8),
                "chunkId": chunk_id,
                "sourcePath": source_path,
                "repositoryUrl": repository_url,
                "commitSha": commit_sha,
                "label": f"Relation path: {_local(path.source)} → {_local(path.target)}",
                "heading": f"{_local(path.source)} – {_local(path.target)} relation ({standard})",
                "text": text,
                "docType": "ontology-relation",
                "standardsScope": [standard],
            }
        )
    return chunks
