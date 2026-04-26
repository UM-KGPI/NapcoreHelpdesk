#!/usr/bin/env bash

set -euo pipefail

GRAPHDB_ENDPOINT="${GRAPHDB_SPARQL_ENDPOINT:-http://localhost:7200}"
GRAPHDB_REPOSITORY="${GRAPHDB_REPOSITORY:-napcore-helpdesk}"
GRAPHDB_QUERY_ENDPOINT="${GRAPHDB_ENDPOINT%/}/repositories/${GRAPHDB_REPOSITORY}"

expected_graphs=(
  "https://napcore.eu/graph/alignments/datex"
  "https://napcore.eu/graph/alignments/netex"
  "https://napcore.eu/graph/alignments/opra"
  "https://napcore.eu/graph/alignments/siri"
  "https://napcore.eu/graph/artifact-rules/datex/v1.0"
  "https://napcore.eu/graph/artifact-rules/netex/v1.0"
  "https://napcore.eu/graph/artifact-rules/opra/v1.0"
  "https://napcore.eu/graph/artifact-rules/siri/v1.0"
  "https://napcore.eu/graph/core/napcore-its"
    "https://napcore.eu/graph/examples/netex"
  "https://napcore.eu/graph/standards/datex"
  "https://napcore.eu/graph/standards/netex"
  "https://napcore.eu/graph/standards/opra"
  "https://napcore.eu/graph/standards/siri"
)

if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to verify the GraphDB ontology state." >&2
    exit 1
fi

query='SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g'
actual_output="$(curl -fsS -G "${GRAPHDB_QUERY_ENDPOINT}" --data-urlencode "query=${query}")"

actual_graphs=()
while IFS= read -r line; do
    actual_graphs+=("${line//$'\r'/}")
done < <(printf '%s\n' "${actual_output}" | tail -n +2 | sed '/^$/d')

expected_count="${#expected_graphs[@]}"
actual_count="${#actual_graphs[@]}"

if [[ "${actual_count}" -ne "${expected_count}" ]]; then
    echo "Expected ${expected_count} ontology named graphs but found ${actual_count}." >&2
    printf 'Actual graphs:\n' >&2
    printf '  %s\n' "${actual_graphs[@]}" >&2
    exit 1
fi

for i in "${!expected_graphs[@]}"; do
    if [[ "${actual_graphs[$i]}" != "${expected_graphs[$i]}" ]]; then
        echo "Named graph mismatch at position $((i + 1))." >&2
        echo "Expected: ${expected_graphs[$i]}" >&2
        echo "Actual:   ${actual_graphs[$i]}" >&2
        exit 1
    fi
done

echo "GraphDB ontology state verified: ${actual_count} named graphs present in ${GRAPHDB_REPOSITORY}."
