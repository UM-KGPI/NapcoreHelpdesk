# Decision Record: Local LLM Strategy for Controller and Narration

Date: 2026-05-06
Status: Accepted (Dev Baseline), Proposed (Pilot/Production Variants)
Owners: Helpdesk architecture and backend team

## 1. Context
The helpdesk now separates LLM responsibilities into:
- Controller LLM: intent classification, route selection, constrained SPARQL/query planning.
- Narration LLM: final grounded answer composition from an evidence pack.

The local runtime target is an Intel macOS machine with 32 GB RAM, CPU-only inference. During prior testing, Metal on AMD GPU produced corrupted output; CPU-only (`--device none`) is required on this machine.

## 2. Decision
- Adopt Option 1 as the development baseline now:
  - Controller: Qwen3-8B Q4_K_M
  - Narration: Qwen3-8B Q4_K_M
- Keep Option 3 as near-term production candidate when improved quality is needed without severe memory pressure:
  - Controller: Qwen3-8B Q4_K_M
  - Narration: DeepSeek-Coder-6.7B Q4_K_M or Qwen2.5-Coder-7B Q4_K_M
- Defer Option 2 on current hardware due memory/latency risk:
  - Controller: Qwen3-8B Q4_K_M
  - Narration: Qwen2.5-Coder-14B Q4_K_M (higher quality, slower)

## 3. Benchmark Evidence
Measured locally with llama.cpp, CPU-only (`--device none`), coding prompt workload.

| Model | Quant | Size | Prompt t/s | Gen t/s | Summary |
|---|---|---:|---:|---:|---|
| Qwen2.5-Coder-1.5B | Q4_K_M | 0.94 GB | 130.0 | 22.8 | Fastest, lowest quality ceiling |
| Qwen2.5-Coder-7B | Q4_K_M | 4.4 GB | 29.0 | 5.3 | Strong baseline |
| DeepSeek-Coder-6.7B | Q4_K_M | 4.1 GB | 31.1 | 5.8 | Good quality, similar latency tier |
| Qwen3-8B | Q4_K_M | 5.0 GB | 41.0 | 5.8 | Best practical speed/quality balance |
| Qwen2.5-Coder-14B | Q4_K_M | 9.0 GB | 15.0 | 2.7 | Better depth, noticeably slower |
| DeepSeek-Coder-V2-Lite | Q5_K_M | 11.0 GB | 30.4 | 13.8 | Prior run, not fully apples-to-apples setup |

Interpretation:
- Qwen3-8B is the current sweet spot for local development and controller tasks.
- 14B can improve narration depth but doubles perceived response latency on this host.
- Two-model concurrent loading raises memory pressure; sequential orchestration is safer on 32 GB.

## 4. Consequences
Positive:
- Deterministic controller behavior can be enforced with strict JSON outputs and low temperature.
- A single-model dev baseline simplifies operations and debugging.
- Split architecture keeps policy enforcement explicit (SPARQL allowlist, citation checks, abstention).

Tradeoffs:
- CPU-only generation throughput limits interactive experience for larger narration models.
- Higher-quality narration variants increase tail latency.
- Model switching policy and fallback handling must be explicit in orchestration.

## 5. Guardrails Required
- Controller output must be schema-constrained JSON.
- SPARQL plans must pass allowlist and complexity limits before execution.
- Narration input must be evidence-pack-only.
- If citation/support checks fail, abstain and/or route to editorial workflow.

## 6. Rollout Plan
1. Implement and run with Option 1 in dev.
2. Add feature flags for split deployment mode (single-model vs dual-model sequential).
3. Pilot Option 3 for higher-quality narration where latency budget permits.
4. Re-evaluate Option 2 only after hardware upgrade or remote narration inference.

## 7. Related Documents
- C4 diagrams updated for Controller/Narration split in `docs/architecture/`.
- Detailed benchmark appendix: `docs/testing/local-model-benchmark-report.md`.

## 8. Latest Narration Hardening (2026-05-13)
Recent backend updates tightened narration behavior for evidence-grounded answers.

- Prompt shaping for implementation-example questions now explicitly asks for one short fenced snippet (6-20 lines) copied from a single evidence block when available.
- Example safety remains strict: generated XML/JSON/YAML code blocks are validated against retrieved evidence lines, and fabricated blocks are rejected.
- When evidence does not contain a safely reusable snippet, narration is instructed to say so explicitly and point to cited source files instead of inventing a sample.
- Citation URL generation now avoids `blob/unknown` links by resolving stable refs first (indexed repository branch/tag), then using repository-specific fallback refs where configured (for example OpRa `1.0rc`).
- LLM provider wiring now uses a single-token strategy by default (`GITHUB_API_TOKEN -> LLM_API_KEY -> CONTROLLER_LLM_API_KEY`) unless keys are explicitly overridden.
