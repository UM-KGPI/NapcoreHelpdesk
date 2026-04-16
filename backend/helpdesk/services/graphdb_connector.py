from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class GraphDBConnector:
    """Minimal GraphDB SPARQL connector used for concept anchoring/discovery.

    The connector is intentionally small and replaceable. Callers should treat
    any connector failure as a soft failure and rely on in-memory fallback.
    """

    def __init__(
        self,
        *,
        endpoint_url: str,
        repository: str = "",
        timeout_seconds: int = 5,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.repository = repository.strip()
        self.timeout_seconds = max(1, int(timeout_seconds))

    def anchor_term_to_core_concepts(self, term: str) -> list[str]:
        if not term.strip():
            return []

        escaped_term = term.replace('"', '\\"')
        sparql = f"""
SELECT DISTINCT ?core WHERE {{
  ?standardConcept <http://www.w3.org/2004/02/skos/core#prefLabel>|<http://www.w3.org/2004/02/skos/core#altLabel> \"{escaped_term}\" .
  ?standardConcept <http://www.w3.org/2002/07/owl#equivalentClass>|<http://www.w3.org/2000/01/rdf-schema#subClassOf> ?core .
}}
""".strip()
        rows = self._query_select(sparql)
        return sorted({row.get("core", "") for row in rows if row.get("core")})

    def discover_standards_for_core_concept(self, core_concept_iri: str) -> list[str]:
        if not core_concept_iri.strip():
            return []

        sparql = f"""
SELECT DISTINCT ?standard WHERE {{
  BIND(<{core_concept_iri}> AS ?core)
  ?core <http://www.w3.org/2002/07/owl#equivalentClass>|<http://www.w3.org/2000/01/rdf-schema#subClassOf> ?standardConcept .
  ?standardConcept <http://purl.org/dc/terms/source> ?standard .
}}
""".strip()
        rows = self._query_select(sparql)
        return sorted({row.get("standard", "") for row in rows if row.get("standard")})

    def _query_select(self, sparql: str) -> list[dict[str, str]]:
        if not self.endpoint_url:
            return []

        payload = {"query": sparql}
        if self.repository:
            payload["default-graph-uri"] = self.repository

        request = Request(
            url=self.endpoint_url,
            data=urlencode(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                "Accept": "application/sparql-results+json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            logger.warning("GraphDB SPARQL query failed: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Unexpected GraphDB connector failure: %s", exc)
            return []

        try:
            data = json.loads(raw)
            bindings = data.get("results", {}).get("bindings", [])
            rows: list[dict[str, str]] = []
            for binding in bindings:
                row = {
                    key: value.get("value", "")
                    for key, value in binding.items()
                    if isinstance(value, dict)
                }
                rows.append(row)
            return rows
        except Exception as exc:
            logger.warning("Failed to parse GraphDB SPARQL JSON response: %s", exc)
            return []
