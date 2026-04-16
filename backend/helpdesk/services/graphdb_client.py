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
    "http://www.w3.org/2004/02/skos/core#closeMatch",
]

DEFAULT_NAMESPACES = {
    "nits": "https://napcore.eu/ontology/nits#",
    "netex": "https://napcore.eu/ontology/netex#",
    "opra": "https://napcore.eu/ontology/opra#",
    "datex": "https://napcore.eu/ontology/datex#",
    "transmodel": "https://napcore.eu/ontology/transmodel#",
    "nch": "https://napcore.eu/ontology/helpdesk#",
}


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
) -> list[dict]:
    """Load core + standards + alignment ontologies into named graphs in GraphDB."""

    base_dir = Path(__file__).resolve().parents[3]
    ontology_dir = base_dir / "docs" / "ontology"

    graph_specs = [
        (ontology_dir / "napcore-its.ttl", "https://napcore.eu/graph/core/napcore-its"),
        (ontology_dir / "netex-federated.ttl", "https://napcore.eu/graph/standards/netex"),
        (ontology_dir / "opra-federated.ttl", "https://napcore.eu/graph/standards/opra"),
        (ontology_dir / "siri-federated.ttl", "https://napcore.eu/graph/standards/siri"),
        (ontology_dir / "datex-federated.ttl", "https://napcore.eu/graph/standards/datex"),
        (ontology_dir / "standards-alignment.ttl", "https://napcore.eu/graph/alignments/standards"),
    ]

    results: list[dict] = []
    for file_path, graph_uri in graph_specs:
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
        results.append(result)

    return results