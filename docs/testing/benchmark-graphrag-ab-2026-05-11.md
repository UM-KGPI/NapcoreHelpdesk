# GraphRAG A/B Benchmark Report (All 100 Questions)

Generated: 2026-05-11T19:52:40.336202Z
Total questions: 100
Successful runs: 100
Errors: 0
Total runtime: 674.9 s

## Effective Settings
- GRAPHDB_TIMEOUT_SECONDS: 3
- GRAPH_EXPANSION_MAX_CONCEPTS: 8
- GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS: 12
- RETRIEVAL_SCORING_CANDIDATE_CAP: 32
- RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER: 2
- RETRIEVAL_MAX_SAME_SOURCE_PATH: 1

## Global Statistics
- control_avg_ms: 1507.3
- control_p50_ms: 2184.2
- control_p95_ms: 2925.7
- graph_avg_ms: 5241.3
- graph_p50_ms: 4173.3
- graph_p95_ms: 9851.3
- delta_avg_ms: 3734.0
- delta_p50_ms: 2988.4
- delta_p95_ms: 7545.7
- ratio_avg: 5.229
- ratio_p50: 4.7
- ratio_p95: 10.1
- graph_faster_count: 0
- graph_slower_count: 100
- graph_equal_count: 0

## Intent-Level Statistics
- abstention: count=10, control_avg_ms=1677.9, graph_avg_ms=5077.3, delta_avg_ms=3399.5
- disambiguation: count=2, control_avg_ms=1719.5, graph_avg_ms=5816.6, delta_avg_ms=4097.1
- example: count=15, control_avg_ms=863.5, graph_avg_ms=4477.6, delta_avg_ms=3614.0
- explanation: count=57, control_avg_ms=1406.3, graph_avg_ms=5077.8, delta_avg_ms=3671.5
- mapping: count=16, control_avg_ms=2337.2, graph_avg_ms=6570.1, delta_avg_ms=4233.0

## Graph Stage Timing Statistics (ms)
- candidatePreselectMs: avg=0.0, p50=0.0, p95=0.0
- candidateScoringMs: avg=2870.2, p50=2492.4, p95=5048.0
- candidateSelectionMs: avg=0.4, p50=0.4, p95=0.8
- conceptExtractMs: avg=20.1, p50=20.1, p95=22.5
- conceptMetadataMs: avg=0.0, p50=0.0, p95=0.0
- coverageMetricsMs: avg=571.8, p50=513.5, p95=895.1
- graphCandidateQueryMs: avg=695.7, p50=100.0, p95=2670.2
- graphExpandMs: avg=6.4, p50=6.3, p95=7.7
- pathHintMergeMs: avg=1072.9, p50=1930.1, p95=2108.1
- postgresCandidateQueryMs: avg=1.2, p50=1.2, p95=1.5
- queryEmbeddingMs: avg=0.3, p50=0.3, p95=0.4
- seedChunkEnsureMs: avg=1.8, p50=1.6, p95=2.8
- totalMeasuredMs: avg=5240.9, p50=4173.0, p95=9850.9
- trimmedPostprocessMs: avg=0.0, p50=0.0, p95=0.0

## Slowest Graph Top 10
- q080 (mapping): graph=14811.9 ms, control=2348.9 ms, delta=12463.0 ms
- q067 (explanation): graph=14038.8 ms, control=2654.1 ms, delta=11384.7 ms
- q070 (example): graph=13432.4 ms, control=2851.0 ms, delta=10581.4 ms
- q052 (explanation): graph=12279.3 ms, control=2924.4 ms, delta=9354.9 ms
- q060 (explanation): graph=11426.1 ms, control=2480.0 ms, delta=8946.1 ms
- q089 (mapping): graph=9768.4 ms, control=2296.4 ms, delta=7472.0 ms
- q083 (mapping): graph=9389.3 ms, control=2281.0 ms, delta=7108.3 ms
- q061 (explanation): graph=9075.7 ms, control=3025.0 ms, delta=6050.7 ms
- q059 (example): graph=9050.8 ms, control=2849.4 ms, delta=6201.4 ms
- q073 (explanation): graph=9014.8 ms, control=2774.6 ms, delta=6240.2 ms

## Fastest Graph Top 10
- q023 (explanation): graph=1823.3 ms, control=287.7 ms, delta=1535.6 ms
- q014 (explanation): graph=1922.3 ms, control=308.5 ms, delta=1613.8 ms
- q034 (explanation): graph=2025.1 ms, control=272.0 ms, delta=1753.1 ms
- q042 (explanation): graph=2071.4 ms, control=325.2 ms, delta=1746.2 ms
- q031 (explanation): graph=2075.5 ms, control=417.3 ms, delta=1658.2 ms
- q098 (abstention): graph=2084.2 ms, control=285.4 ms, delta=1798.8 ms
- q038 (explanation): graph=2091.9 ms, control=304.5 ms, delta=1787.4 ms
- q044 (explanation): graph=2173.1 ms, control=380.1 ms, delta=1793.0 ms
- q021 (explanation): graph=2174.1 ms, control=403.7 ms, delta=1770.4 ms
- q018 (explanation): graph=2186.0 ms, control=280.6 ms, delta=1905.4 ms

