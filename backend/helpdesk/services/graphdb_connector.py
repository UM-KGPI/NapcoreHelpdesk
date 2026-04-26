from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Maps IRI domain fragment to human-readable standard name.
# Used by discover_standards_for_core_concept to infer the standard from
# the concept IRI namespace.
_IRI_DOMAIN_TO_STANDARD: dict[str, str] = {
    "netex.org.uk": "NeTEx",
    "opra.org.uk": "OpRa",
    "siri.org.uk": "SIRI",
    "datex.org": "DATEX II",
    "transmodel": "Transmodel",
}


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
SELECT DISTINCT ?stdConcept WHERE {{
  ?stdConcept <http://www.w3.org/2002/07/owl#equivalentClass>|<http://www.w3.org/2000/01/rdf-schema#subClassOf> <{core_concept_iri}> .
  FILTER(!CONTAINS(STR(?stdConcept), "napcore.eu/ontology/nits"))
  FILTER(!CONTAINS(STR(?stdConcept), "www.w3.org"))
  FILTER(!CONTAINS(STR(?stdConcept), "purl.org"))
}}
""".strip()
        rows = self._query_select(sparql)
        standards: list[str] = []
        for row in rows:
            iri = row.get("stdConcept", "")
            for domain, name in _IRI_DOMAIN_TO_STANDARD.items():
                if domain in iri and name not in standards:
                    standards.append(name)
                    break
        return sorted(standards)

    def _query_select(self, sparql: str) -> list[dict[str, str]]:
        if not self.endpoint_url:
            return []

        payload = {"query": sparql}

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
