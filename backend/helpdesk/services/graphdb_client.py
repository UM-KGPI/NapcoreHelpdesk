from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib import parse
from urllib.request import Request, urlopen


SKOS_RELATIONS = [
    "http://www.w3.org/2004/02/skos/core#related",
    "http://www.w3.org/2004/02/skos/core#relatedMatch",
    "http://www.w3.org/2004/02/skos/core#exactMatch",
]

DEFAULT_NAMESPACES = {
    "nits": "https://napcore.eu/ontology/nits#",
    "netex": "https://netex.org.uk/netex/2.0#",
    "opra": "https://transmodel-cen.eu/opra/1.0#",
    "datex": "https://napcore.eu/ontology/datex#",
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
    "datex": (
        "artifact-rules/datex-artifact-rules-v1.0.ttl",
        "https://napcore.eu/graph/artifact-rules/datex/v1.0",
    ),
}

STANDARD_GRAPH_SCOPE = {
    "netex": [
        "https://napcore.eu/graph/standards/netex",
        "https://napcore.eu/graph/alignments/netex",
    ],
    "opra": [
        "https://napcore.eu/graph/standards/opra",
        "https://napcore.eu/graph/alignments/opra",
    ],
    "siri": [
        "https://napcore.eu/graph/standards/siri",
        "https://napcore.eu/graph/alignments/siri",
    ],
    "datex": [
        "https://napcore.eu/graph/standards/datex",
        "https://napcore.eu/graph/alignments/datex",
    ],
    "transmodel": [
        "https://napcore.eu/graph/standards/transmodel",
        "https://napcore.eu/graph/alignments/transmodel",
    ],
}

STANDARD_ALIASES = {
    "netex": "netex",
    "opra": "opra",
    "siri": "siri",
    "datex": "datex",
    "datexii": "datex",
    "datex ii": "datex",
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
        query = (
            "SELECT DISTINCT ?related WHERE { "
            f"VALUES ?seed {{ {values} }} "
            f"VALUES ?g {{ {graph_values} }} "
            "GRAPH ?g { "
            f"?seed (({relation_paths})|^({relation_paths})){quant} ?related . "
            "} "
            "FILTER(isIRI(?related)) "
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

    base_dir = Path(__file__).resolve().parents[3]
    ontology_dir = base_dir / "docs" / "ontology"

    graph_specs = [
        (
            "napcore-its",
            ontology_dir / "napcore-its.ttl",
            "https://napcore.eu/graph/core/napcore-its",
        ),
        (
            "transmodel",
            ontology_dir / "standards" / "transmodel.ttl",
            "https://napcore.eu/graph/standards/transmodel",
        ),
        ("netex", ontology_dir / "standards" / "netex.ttl", "https://napcore.eu/graph/standards/netex"),
        ("opra", ontology_dir / "standards" / "opra.ttl", "https://napcore.eu/graph/standards/opra"),
        ("siri", ontology_dir / "standards" / "siri.ttl", "https://napcore.eu/graph/standards/siri"),
        ("datex", ontology_dir / "standards" / "datex.ttl", "https://napcore.eu/graph/standards/datex"),
        (
            "netex-examples",
            ontology_dir / "examples" / "netex-examples.ttl",
            "https://napcore.eu/graph/examples/netex",
        ),
        (
            "nits-transmodel-align",
            ontology_dir / "alignments" / "nits-transmodel-align.ttl",
            "https://napcore.eu/graph/alignments/transmodel",
        ),
        (
            "nits-netex-align",
            ontology_dir / "alignments" / "nits-netex-align.ttl",
            "https://napcore.eu/graph/alignments/netex",
        ),
        (
            "nits-opra-align",
            ontology_dir / "alignments" / "nits-opra-align.ttl",
            "https://napcore.eu/graph/alignments/opra",
        ),
        (
            "nits-siri-align",
            ontology_dir / "alignments" / "nits-siri-align.ttl",
            "https://napcore.eu/graph/alignments/siri",
        ),
        (
            "nits-datex-align",
            ontology_dir / "alignments" / "nits-datex-align.ttl",
            "https://napcore.eu/graph/alignments/datex",
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

    return results
