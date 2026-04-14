from __future__ import annotations

import base64
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _parse_identifier(identifier: str, expected_prefix: str) -> str:
    prefix = f"{expected_prefix}:"
    if not identifier.startswith(prefix):
        raise ValueError(f"Invalid identifier format: {identifier}")
    return identifier[len(prefix) :]


def build_neo4j_statements(snapshot: dict) -> list[dict]:
    nodes = snapshot.get("nodes", [])
    edges = snapshot.get("edges", [])

    concept_rows = []
    chunk_rows = []
    for node in nodes:
        node_type = node.get("type")
        if node_type == "Concept":
            concept_rows.append(
                {
                    "conceptId": node.get("conceptId"),
                    "namespace": node.get("namespace", "nch"),
                }
            )
        elif node_type == "Chunk":
            chunk_rows.append(
                {
                    "chunkId": node.get("chunkId"),
                    "repositoryUrl": node.get("repositoryUrl", ""),
                    "sourcePath": node.get("sourcePath", ""),
                    "commitSha": node.get("commitSha", ""),
                    "qualityScore": float(node.get("qualityScore") or 0.0),
                    "docType": node.get("docType", ""),
                }
            )

    mention_rows = []
    related_rows = []
    for edge in edges:
        edge_type = edge.get("type")
        if edge_type == "MENTIONS_CONCEPT":
            mention_rows.append(
                {
                    "chunkId": _parse_identifier(edge.get("from", ""), "chunk"),
                    "conceptId": _parse_identifier(edge.get("to", ""), "concept"),
                    "sourceUrl": edge.get("sourceUrl", ""),
                    "sourcePath": edge.get("sourcePath", ""),
                    "commitSha": edge.get("commitSha", ""),
                }
            )
        elif edge_type == "RELATED_TO":
            related_rows.append(
                {
                    "fromConceptId": _parse_identifier(edge.get("from", ""), "concept"),
                    "toConceptId": _parse_identifier(edge.get("to", ""), "concept"),
                    "relationType": edge.get("relationType", "semantic-proximity"),
                }
            )

    return [
        {
            "statement": (
                "UNWIND $rows AS row "
                "MERGE (c:Concept {conceptId: row.conceptId}) "
                "SET c.namespace = row.namespace, c.updatedAt = datetime()"
            ),
            "parameters": {"rows": concept_rows},
        },
        {
            "statement": (
                "UNWIND $rows AS row "
                "MERGE (ch:Chunk {chunkId: row.chunkId}) "
                "SET ch.repositoryUrl = row.repositoryUrl, "
                "    ch.sourcePath = row.sourcePath, "
                "    ch.commitSha = row.commitSha, "
                "    ch.qualityScore = row.qualityScore, "
                "    ch.docType = row.docType, "
                "    ch.updatedAt = datetime()"
            ),
            "parameters": {"rows": chunk_rows},
        },
        {
            "statement": (
                "UNWIND $rows AS row "
                "MATCH (ch:Chunk {chunkId: row.chunkId}) "
                "MATCH (c:Concept {conceptId: row.conceptId}) "
                "MERGE (ch)-[r:MENTIONS_CONCEPT]->(c) "
                "SET r.sourceUrl = row.sourceUrl, "
                "    r.sourcePath = row.sourcePath, "
                "    r.commitSha = row.commitSha, "
                "    r.updatedAt = datetime()"
            ),
            "parameters": {"rows": mention_rows},
        },
        {
            "statement": (
                "UNWIND $rows AS row "
                "MATCH (a:Concept {conceptId: row.fromConceptId}) "
                "MATCH (b:Concept {conceptId: row.toConceptId}) "
                "MERGE (a)-[r:RELATED_TO]->(b) "
                "SET r.relationType = row.relationType, r.updatedAt = datetime()"
            ),
            "parameters": {"rows": related_rows},
        },
    ]


def _neo4j_http_endpoint(uri: str, database: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme in {"http", "https"}:
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        return f"{base}/db/{database}/tx/commit"

    if parsed.scheme in {"neo4j", "neo4j+s", "bolt", "bolt+s"}:
        secure = parsed.scheme.endswith("+s")
        scheme = "https" if secure else "http"
        host = parsed.hostname or "localhost"
        port = parsed.port
        if port in (None, 7687):
            port = 7474
        return f"{scheme}://{host}:{port}/db/{database}/tx/commit"

    raise ValueError(f"Unsupported Neo4j URI scheme: {parsed.scheme}")


def submit_neo4j_statements(
    *,
    uri: str,
    username: str,
    password: str,
    database: str,
    statements: list[dict],
    timeout_seconds: int = 20,
) -> dict:
    endpoint = _neo4j_http_endpoint(uri=uri, database=database)

    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    payload = json.dumps({"statements": statements}).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {token}",
        },
        method="POST",
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")

    parsed = json.loads(body)
    errors = parsed.get("errors", [])
    if errors:
        joined = "; ".join(error.get("message", "Unknown Neo4j error") for error in errors)
        raise RuntimeError(f"Neo4j import failed: {joined}")

    return {
        "endpoint": endpoint,
        "statementCount": len(statements),
    }
