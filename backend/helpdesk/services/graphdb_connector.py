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
    "transmodel-cen.eu/opra": "OpRa",
    "siri.org.uk": "SIRI",
    "www.siri.org.uk": "SIRI",
    "datex.org": "DATEX II",
    "transmodel": "Transmodel",
}

_ALIGNMENT_PATH = (
    "<http://www.w3.org/2002/07/owl#equivalentClass>|"
    "<http://www.w3.org/2000/01/rdf-schema#subClassOf>|"
    "^<http://www.w3.org/2002/07/owl#equivalentClass>|"
    "^<http://www.w3.org/2000/01/rdf-schema#subClassOf>|"
    "<http://www.w3.org/2004/02/skos/core#relatedMatch>|"
    "^<http://www.w3.org/2004/02/skos/core#relatedMatch>|"
    "<http://www.w3.org/2004/02/skos/core#exactMatch>|"
    "^<http://www.w3.org/2004/02/skos/core#exactMatch>|"
    "<http://www.w3.org/2004/02/skos/core#closeMatch>|"
    "^<http://www.w3.org/2004/02/skos/core#closeMatch>"
)


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

        escaped_term = term.replace('"', '\"')
        sparql = f"""
SELECT DISTINCT ?core WHERE {{
  ?standardConcept <http://www.w3.org/2004/02/skos/core#prefLabel>|<http://www.w3.org/2004/02/skos/core#altLabel>|<http://www.w3.org/2000/01/rdf-schema#label> ?label .
  FILTER(LCASE(STR(?label)) = LCASE(\"{escaped_term}\"))
  ?standardConcept {_ALIGNMENT_PATH} ?core .
}}
""".strip()
        rows = self._query_select(sparql)
        return sorted({row.get("core", "") for row in rows if row.get("core")})

    def discover_standards_for_core_concept(self, core_concept_iri: str) -> list[str]:
        if not core_concept_iri.strip():
            return []

        sparql = f"""
SELECT DISTINCT ?stdConcept WHERE {{
    GRAPH ?g {{
        ?stdConcept {_ALIGNMENT_PATH} <{core_concept_iri}> .
    }}
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

    def discover_standards_for_core_concept_slug(self, core_concept_slug: str) -> list[str]:
        """Resolve a slug-style NITS concept id (e.g. line-network) and discover standards."""

        slug = (core_concept_slug or "").strip().lower()
        if not slug:
            return []

        normalized_slug = "".join(ch for ch in slug if ch.isalnum())
        if not normalized_slug:
            return []

        tokens = [token for token in slug.replace("_", "-").split("-") if token]
        token_values = " ".join(f'"{token}"' for token in tokens)

        sparql = f"""
SELECT DISTINCT ?core WHERE {{
  GRAPH ?g {{
    ?core a <http://www.w3.org/2002/07/owl#Class> .
    OPTIONAL {{ ?core <http://www.w3.org/2004/02/skos/core#prefLabel>|<http://www.w3.org/2000/01/rdf-schema#label> ?label . }}
    FILTER(CONTAINS(STR(?core), "napcore.eu/ontology/nits"))
    BIND(LCASE(REPLACE(STRAFTER(STR(?core), "#"), "[^A-Za-z0-9]", "")) AS ?coreLocalNorm)
    BIND(LCASE(REPLACE(STR(COALESCE(?label, "")), "[^A-Za-z0-9]", "")) AS ?labelNorm)
    FILTER(?coreLocalNorm = "{normalized_slug}" || ?labelNorm = "{normalized_slug}")
  }}
}}
""".strip()
        rows = self._query_select(sparql)

        core_iris = [row.get("core", "") for row in rows if row.get("core")]
        if not core_iris and token_values:
            # Fallback: match by individual tokens when full slug has no exact match.
            token_sparql = f"""
SELECT DISTINCT ?core WHERE {{
  GRAPH ?g {{
    ?core a <http://www.w3.org/2002/07/owl#Class> .
    OPTIONAL {{ ?core <http://www.w3.org/2004/02/skos/core#prefLabel>|<http://www.w3.org/2000/01/rdf-schema#label> ?label . }}
    FILTER(CONTAINS(STR(?core), "napcore.eu/ontology/nits"))
    BIND(LCASE(REPLACE(STRAFTER(STR(?core), "#"), "[^A-Za-z0-9]", "")) AS ?coreLocalNorm)
    BIND(LCASE(REPLACE(STR(COALESCE(?label, "")), "[^A-Za-z0-9]", "")) AS ?labelNorm)
    VALUES ?token {{ {token_values} }}
    FILTER(?coreLocalNorm = ?token || ?labelNorm = ?token)
  }}
}}
""".strip()
            token_rows = self._query_select(token_sparql)
            core_iris = [row.get("core", "") for row in token_rows if row.get("core")]

        discovered: list[str] = []
        for core_iri in sorted(set(core_iris)):
            for standard in self.discover_standards_for_core_concept(core_iri):
                if standard not in discovered:
                    discovered.append(standard)
        return discovered

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
