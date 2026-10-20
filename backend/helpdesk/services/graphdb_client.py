"""
Low-level HTTP client for the GraphDB REST API.

Handles authentication, SPARQL query submission over the repositories
endpoint, and response parsing. Higher-level semantic operations should
use graphdb_connector.py rather than calling this client directly.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-16  |  Modified: 2026-06-28
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib import parse
from urllib.request import Request, urlopen


# Despite the name, this is the full set of relations the live concept-expansion
# query (query_graphdb_concept_expansion, below) traverses -- not just SKOS ones.
# Every nits-<standard>-align.ttl file uses owl:equivalentClass, rdfs:subClassOf,
# and/or skos:closeMatch to link standard concepts to the nits: core ontology;
# until 2026-09-21 this list only had the three plain SKOS relations below, so
# none of the alignment files' content was ever reachable through this path
# (confirmed empirically: the old list returned 0 related concepts for seeds
# that have real alignment entries; this list returns the expected results).
SKOS_RELATIONS = [
    "http://www.w3.org/2004/02/skos/core#related",
    "http://www.w3.org/2004/02/skos/core#relatedMatch",
    "http://www.w3.org/2004/02/skos/core#exactMatch",
    "http://www.w3.org/2004/02/skos/core#closeMatch",
    "http://www.w3.org/2002/07/owl#equivalentClass",
    "http://www.w3.org/2000/01/rdf-schema#subClassOf",
]

DEFAULT_NAMESPACES = {
    "netex": "https://netex.org.uk/netex/2.0#",
    "opra": "https://transmodel-cen.eu/opra/1.0#",
    # Matches standards/siri.ttl's actual @prefix (confirmed against what's
    # really loaded in GraphDB: https://siri.org.uk/siri/2.1# has zero
    # declared classes anywhere -- that was this module's prior value here,
    # and nits-siri-align.ttl's own prefix, both wrong).
    "siri": "https://siri.org.uk/siri/1.3#",
    "transmodel": "https://transmodel-cen.eu/6.2/",
    "nch": "https://napcore.eu/ontology/helpdesk#",
}

_NETEX_IRI_PREFIXES = (
    "https://netex.org.uk/netex/2.0#",
    "https://netex.org.uk/netex/2.0/",
    "https://napcore.eu/ontology/netex#",
    "http://napcore.eu/ontology/netex#",
    "http://napcore.example.org/ontology/netex#",
)

_OPRA_IRI_PREFIXES = (
    "https://transmodel-cen.eu/opra/1.0#",
    "https://transmodel-cen.eu/opra/1.0/",
    "https://napcore.eu/ontology/opra#",
    "http://napcore.eu/ontology/opra#",
    "http://napcore.example.org/ontology/opra#",
)

_OPRA_IRI_PREFIXES = (
    "https://transmodel-cen.eu/opra/1.0#",
    "https://transmodel-cen.eu/opra/1.0/",
    "https://napcore.eu/ontology/opra#",
    "http://napcore.eu/ontology/opra#",
    "http://napcore.example.org/ontology/opra#",
)

STANDARD_ARTIFACT_RULE_SPECS = {
    "netex": (
        "artifact-rules/netex-artifact-rules-v1.0.ttl",
        "https://napcore.eu/graph/artifact-rules/netex/v1.0",
    ),
    "opra": (
        "artifact-rules/opra-artifact-rules-v1.0.ttl",
        "https://napcore.eu/graph/artifact-rules/opra/v1.0",
    ),
    "siri": (
        "artifact-rules/siri-artifact-rules-v1.0.ttl",
        "https://napcore.eu/graph/artifact-rules/siri/v1.0",
    ),
}

# The per-standard alignments/{netex,opra,siri} graphs used to be listed here
# too; they are populated exclusively by the nits-{netex,opra,siri}-align.ttl
# files (confirmed in NITS-REMOVAL-PLAN.md section 2 group A). Since the live
# concept-expansion pivot (query_graphdb_concept_expansion, above) now pivots
# through Transmodel only, those graphs no longer contribute to this scope --
# the Transmodel-alignment equivalent (alignments/transmodel-{standard}) is
# already added unconditionally by TRANSMODEL_REFERENCE_GRAPHS below.
STANDARD_GRAPH_SCOPE = {
    "netex": [
        "https://napcore.eu/graph/standards/netex",
    ],
    "opra": [
        "https://napcore.eu/graph/standards/opra",
    ],
    "siri": [
        "https://napcore.eu/graph/standards/siri",
    ],
    "transmodel": [
        "https://napcore.eu/graph/standards/transmodel",
    ],
}

# Named graphs whose source file was removed. A replace load deletes them so
# that stale content does not stay live in GraphDB after the file is gone.
# - alignments/transmodel (nits-transmodel-align.ttl): hand-written definitions
#   on NeTEx classes; superseded by the generated transmodel-*-align.ttl.
# - core/napcore-its and alignments/{netex,opra,siri}: the NITS upper
#   ontology and its per-standard alignment files (NITS-REMOVAL-PLAN.md
#   Phase 3) -- superseded by the Transmodel pivot (see STANDARD_GRAPH_SCOPE
#   and query_graphdb_concept_expansion above).
RETIRED_GRAPH_URIS = [
    "https://napcore.eu/graph/alignments/transmodel",
    "https://napcore.eu/graph/core/napcore-its",
    "https://napcore.eu/graph/alignments/netex",
    "https://napcore.eu/graph/alignments/opra",
    "https://napcore.eu/graph/alignments/siri",
]

# Transmodel is the conceptual reference for NeTEx, SIRI and OpRa, so its
# standard graph and the direct Transmodel<->standard alignment graphs are added
# to every standard-scoped query, not only when Transmodel itself is named.
# Without this, a NeTEx question can never reach e.g. tm:STOP_PLACE.
TRANSMODEL_ALIGNED_STANDARDS = ("netex", "siri", "opra")

TRANSMODEL_REFERENCE_GRAPHS = [
    "https://napcore.eu/graph/standards/transmodel",
    *(f"https://napcore.eu/graph/alignments/transmodel-{standard}" for standard in TRANSMODEL_ALIGNED_STANDARDS),
]

TRANSMODEL_NAMESPACE = "https://transmodel-cen.eu/6.2/"

STANDARD_ALIASES = {
    "netex": "netex",
    "opra": "opra",
    "siri": "siri",
    "transmodel": "transmodel",
}


def build_graph_scope_for_standards(
    standards: set[str],
    *,
    include_artifact_rules: bool,
) -> list[str]:
    """Build an ordered named-graph scope for GraphDB queries.

    Graph scope is standard-specific and can optionally include
    artifact-derived rules for normative queries.
    """

    normalized: list[str] = []
    for standard in sorted(standards):
        alias = STANDARD_ALIASES.get(standard.strip().lower())
        if alias and alias not in normalized:
            normalized.append(alias)

    graph_uris: list[str] = []
    for standard in normalized:
        graph_uris.extend(STANDARD_GRAPH_SCOPE.get(standard, []))
        if include_artifact_rules and standard in STANDARD_ARTIFACT_RULE_SPECS:
            _file_rel_path, artifact_graph_uri = STANDARD_ARTIFACT_RULE_SPECS[standard]
            graph_uris.append(artifact_graph_uri)

    if graph_uris:
        graph_uris.extend(TRANSMODEL_REFERENCE_GRAPHS)

    # Keep stable order while removing duplicates.
    return list(dict.fromkeys(graph_uris))


def _build_auth_header(username: str | None, password: str | None) -> str | None:
    user = (username or "").strip()
    pwd = (password or "").strip()
    if not user:
        return None
    token = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _normalize_repository_endpoint(endpoint: str, repository: str) -> str:
    base = (endpoint or "").strip().rstrip("/")
    repo = (repository or "").strip()
    if not base:
        raise ValueError("GraphDB endpoint is required")
    if "/repositories/" in base:
        return base
    if repo and base.endswith("/repositories"):
        return f"{base}/{repo}"
    if repo:
        return f"{base}/repositories/{repo}"
    return base


def _to_iri(concept_id: str) -> str | None:
    if ":" not in concept_id:
        return None
    prefix, local = concept_id.split(":", 1)
    namespace = DEFAULT_NAMESPACES.get(prefix.lower())
    if not namespace or not local:
        return None
    return f"{namespace}{local}"


def _iri_to_concept_id(iri: str) -> str | None:
    for prefix, namespace in DEFAULT_NAMESPACES.items():
        if iri.startswith(namespace):
            return f"{prefix}:{iri[len(namespace):]}"
    for namespace in _NETEX_IRI_PREFIXES:
        if iri.startswith(namespace):
            return f"netex:{iri[len(namespace):]}"
    for namespace in _OPRA_IRI_PREFIXES:
        if iri.startswith(namespace):
            return f"opra:{iri[len(namespace):]}"
    return None


def execute_sparql_query(
    *,
    sparql_query: str,
    endpoint: str,
    repository: str = "",
    username: str = "",
    password: str = "",
    timeout_seconds: int = 10,
) -> dict | None:
    """Execute a SPARQL query and return raw results dict with 'bindings' key."""

    if not sparql_query or not sparql_query.strip():
        return None

    query_endpoint = _normalize_repository_endpoint(endpoint=endpoint, repository=repository)
    auth_header = _build_auth_header(username=username, password=password)
    headers = {
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/sparql-query; charset=utf-8",
    }
    if auth_header:
        headers["Authorization"] = auth_header

    request = Request(
        query_endpoint,
        data=sparql_query.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
        return json.loads(body)
    except Exception:
        return None


def query_graphdb_concept_expansion(
    *,
    concept_ids: set[str],
    hops: int = 1,
    endpoint: str,
    repository: str = "",
    username: str = "",
    password: str = "",
    timeout_seconds: int = 10,
    graph_uris: list[str] | None = None,
) -> set[str]:
    """Query GraphDB for SKOS-based concept expansion and return expanded concept IDs."""

    if not concept_ids:
        return set()

    seed_iris = sorted({iri for cid in concept_ids if (iri := _to_iri(cid))})
    if not seed_iris:
        return set(concept_ids)

    safe_hops = max(1, int(hops))
    relation_paths = "|".join(f"<{rel}>" for rel in SKOS_RELATIONS)
    values = " ".join(f"<{iri}>" for iri in seed_iris)
    # SPARQL 1.1 property paths do not support {n,m} quantifiers.
    # Use a plain path for 1 hop, or + for multi-hop traversal.
    quant = "" if safe_hops == 1 else "+"
    if graph_uris:
        graph_values = " ".join(f"<{iri}>" for iri in graph_uris)
        # A property path inside `GRAPH ?g { ?seed path ?related }` must resolve
        # entirely within one graph per solution -- it cannot hop from an edge in
        # e.g. alignments/transmodel-opra to an edge in alignments/transmodel-netex,
        # even though both are in `graph_uris`. That breaks the one thing the
        # shared hub exists for: a seed in one standard's alignment graph reaching
        # a sibling concept declared in a different standard's alignment graph.
        # Second UNION branch below handles that case explicitly as two single-
        # graph hops: seed -> pivot (in the seed's own graph), then
        # pivot <- sibling concepts (searched across all scoped graphs). Pivots
        # are Transmodel concepts (the reference hub).
        query = (
            "SELECT DISTINCT ?related WHERE { "
            "{ "
            f"VALUES ?seed {{ {values} }} "
            f"VALUES ?g {{ {graph_values} }} "
            "GRAPH ?g { "
            f"?seed (({relation_paths})|^({relation_paths})){quant} ?related . "
            "} "
            "FILTER(isIRI(?related)) "
            "} UNION { "
            f"VALUES ?seed {{ {values} }} "
            f"VALUES ?gPivot {{ {graph_values} }} "
            "GRAPH ?gPivot { "
            f"?seed ({relation_paths}) ?pivot . "
            "} "
            f"FILTER(STRSTARTS(STR(?pivot), '{TRANSMODEL_NAMESPACE}')) "
            f"VALUES ?gSibling {{ {graph_values} }} "
            "GRAPH ?gSibling { "
            f"?related ({relation_paths}) ?pivot . "
            "} "
            "FILTER(isIRI(?related)) "
            "} "
            "}"
        )
    else:
        query = (
            "SELECT DISTINCT ?related WHERE { "
            f"VALUES ?seed {{ {values} }} "
            f"?seed (({relation_paths})|^({relation_paths})){quant} ?related . "
            "FILTER(isIRI(?related)) "
            "}"
        )

    query_endpoint = _normalize_repository_endpoint(endpoint=endpoint, repository=repository)
    auth_header = _build_auth_header(username=username, password=password)
    headers = {
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/sparql-query; charset=utf-8",
    }
    if auth_header:
        headers["Authorization"] = auth_header

    request = Request(
        query_endpoint,
        data=query.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")

    payload = json.loads(body)
    bindings = payload.get("results", {}).get("bindings", [])

    expanded = set(concept_ids)
    for binding in bindings:
        iri = str(binding.get("related", {}).get("value") or "").strip()
        if not iri:
            continue
        concept_id = _iri_to_concept_id(iri)
        if concept_id:
            expanded.add(concept_id)

    return expanded


def upload_named_graph_turtle(
    *,
    endpoint: str,
    repository: str,
    graph_uri: str,
    turtle_content: str,
    username: str = "",
    password: str = "",
    timeout_seconds: int = 20,
    replace: bool = True,
) -> dict:
    """Upload Turtle content into a GraphDB named graph using the statements endpoint."""

    if not graph_uri.strip():
        raise ValueError("graph_uri is required")

    repo_endpoint = _normalize_repository_endpoint(endpoint=endpoint, repository=repository)
    statements_endpoint = f"{repo_endpoint.rstrip('/')}/statements"
    auth_header = _build_auth_header(username=username, password=password)

    context_param = f"<{graph_uri.strip()}>"
    query = parse.urlencode({"context": context_param})
    target_url = f"{statements_endpoint}?{query}"

    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Accept": "application/json",
    }
    if auth_header:
        headers["Authorization"] = auth_header

    if replace:
        clear_request = Request(
            target_url,
            headers=headers,
            method="DELETE",
        )
        with urlopen(clear_request, timeout=timeout_seconds):
            pass

    upload_request = Request(
        target_url,
        data=turtle_content.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(upload_request, timeout=timeout_seconds):
        pass

    return {
        "graphUri": graph_uri,
        "statementEndpoint": statements_endpoint,
        "replaced": replace,
    }


def load_default_ontology_graphs(
    *,
    endpoint: str,
    repository: str,
    timeout_seconds: int = 20,
    username: str = "",
    password: str = "",
    replace: bool = True,
    include_artifact_rules: bool = False,
    artifact_rule_standards: set[str] | None = None,
) -> list[dict]:
    """Load core + standards + alignment ontologies into named graphs in GraphDB.

    Artifact-derived rules are intentionally opt-in because they should only be
    active for standard-specific, normative constraint reasoning.
    """

    import os as _os
    _override = _os.environ.get("NAPCORE_ONTOLOGY_DIR")
    ontology_dir = Path(_override) if _override else Path(__file__).resolve().parents[3] / "docs" / "ontology"

    graph_specs = [
        (
            "transmodel",
            ontology_dir / "standards" / "transmodel.ttl",
            "https://napcore.eu/graph/standards/transmodel",
        ),
        ("netex", ontology_dir / "standards" / "netex.ttl", "https://napcore.eu/graph/standards/netex"),
        ("opra", ontology_dir / "standards" / "opra.ttl", "https://napcore.eu/graph/standards/opra"),
        ("siri", ontology_dir / "standards" / "siri.ttl", "https://napcore.eu/graph/standards/siri"),
        (
            "examples-catalog",
            ontology_dir / "standards" / "examples.ttl",
            "https://napcore.eu/graph/examples/catalog",
        ),
        # Generated by build_transmodel_alignment
        *(
            (
                f"transmodel-{standard}-align",
                ontology_dir / "alignments" / f"transmodel-{standard}-align.ttl",
                f"https://napcore.eu/graph/alignments/transmodel-{standard}",
            )
            for standard in TRANSMODEL_ALIGNED_STANDARDS
        ),
    ]

    if include_artifact_rules:
        requested = (
            sorted(STANDARD_ARTIFACT_RULE_SPECS.keys())
            if artifact_rule_standards is None
            else sorted({item.strip().lower() for item in artifact_rule_standards if item.strip()})
        )
        unsupported = [name for name in requested if name not in STANDARD_ARTIFACT_RULE_SPECS]
        if unsupported:
            supported = ", ".join(sorted(STANDARD_ARTIFACT_RULE_SPECS.keys()))
            unsupported_joined = ", ".join(unsupported)
            raise ValueError(
                f"Unsupported artifact-rule standards: {unsupported_joined}. Supported: {supported}"
            )

        for standard in requested:
            file_rel_path, graph_uri = STANDARD_ARTIFACT_RULE_SPECS[standard]
            graph_specs.append((f"{standard}-artifact-rules-v1.0", ontology_dir / file_rel_path, graph_uri))

    results: list[dict] = []
    for ontology_key, file_path, graph_uri in graph_specs:
        if not file_path.exists():
            raise FileNotFoundError(f"Ontology file not found: {file_path}")
        content = file_path.read_text(encoding="utf-8")
        result = upload_named_graph_turtle(
            endpoint=endpoint,
            repository=repository,
            graph_uri=graph_uri,
            turtle_content=content,
            username=username,
            password=password,
            timeout_seconds=timeout_seconds,
            replace=replace,
        )
        result["filePath"] = str(file_path)
        result["ontologyKey"] = ontology_key
        results.append(result)

    if replace:
        for graph_uri in RETIRED_GRAPH_URIS:
            delete_named_graph(
                endpoint=endpoint,
                repository=repository,
                graph_uri=graph_uri,
                username=username,
                password=password,
                timeout_seconds=timeout_seconds,
            )
            results.append({"graphUri": graph_uri, "retired": True})

    return results


def delete_named_graph(
    *,
    endpoint: str,
    repository: str,
    graph_uri: str,
    username: str = "",
    password: str = "",
    timeout_seconds: int = 20,
) -> None:
    """Delete all statements in a named graph (no-op if the graph is absent)."""

    repo_endpoint = _normalize_repository_endpoint(endpoint=endpoint, repository=repository)
    query = parse.urlencode({"context": f"<{graph_uri.strip()}>"})
    headers = {"Accept": "application/json"}
    auth_header = _build_auth_header(username=username, password=password)
    if auth_header:
        headers["Authorization"] = auth_header
    request = Request(f"{repo_endpoint.rstrip('/')}/statements?{query}", headers=headers, method="DELETE")
    with urlopen(request, timeout=timeout_seconds):
        pass
