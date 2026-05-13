# Local Model Benchmark Report

Date: 2026-05-06
Scope: Local coding-oriented model benchmarks run for helpdesk controller/narration decision support.

## 1. Environment
- Host: macOS (Intel), 32 GB RAM
- Inference engine: llama.cpp
- Runtime mode: CPU-only
- Required stability flag on this host: `--device none`

Note:
GPU Metal path on this machine produced token corruption in prior tests, so all final comparative runs were CPU-only.

## 2. Method
- Prompt style: coding task (factorial function with validation and usage example)
- Context length used in runs: typically 2048
- Threads: 8
- Metrics captured:
  - Prompt throughput (tokens/s)
  - Generation throughput (tokens/s)
- Sampling: low-temperature coding profile

## 3. Results Table

| Model | Quant | Size | Prompt t/s | Gen t/s | Quality Observation |
|---|---|---:|---:|---:|---|
| Qwen2.5-Coder-1.5B | Q4_K_M | 0.94 GB | 130.0 | 22.8 | Very fast drafts, lower depth |
| Qwen2.5-Coder-7B | Q4_K_M | 4.4 GB | 29.0 | 5.3 | Good quality baseline |
| DeepSeek-Coder-6.7B | Q4_K_M | 4.1 GB | 31.1 | 5.8 | Similar tier, complete structured output |
| Qwen3-8B | Q4_K_M | 5.0 GB | 41.0 | 5.8 | Best balance for this host |
| Qwen2.5-Coder-14B | Q4_K_M | 9.0 GB | 15.0 | 2.7 | Better depth, slower interaction |
| DeepSeek-Coder-V2-Lite | Q5_K_M | 11.0 GB | 30.4 | 13.8 | Prior run with different setup; treat separately |

## 4. Practical Findings
1. Best dev baseline now: Qwen3-8B Q4_K_M.
2. Best controller candidate: Qwen3-8B (fast enough and reliable instruction following).
3. Narration quality upgrade path: Qwen2.5-Coder-14B, with clear latency tradeoff.
4. For 32 GB hosts, dual-model concurrent loading is riskier than sequential orchestration.

## 5. Deployment Guidance by Mode
- Development:
  - Single model for both roles: Qwen3-8B.
- Pilot:
  - Controller: Qwen3-8B.
  - Narration: DeepSeek-Coder-6.7B or Qwen2.5-Coder-7B (sequential load preferred).
- Higher-quality narration mode:
  - Controller: Qwen3-8B.
  - Narration: Qwen2.5-Coder-14B (accept slower responses).

## 6. Repro Command Pattern
Example pattern used in these tests:

```bash
/Users/andrejt/Research/repositories/git/llama.cpp/build/bin/llama-cli \
  --device none \
  -m /path/to/model.gguf \
  -c 2048 -n 256 -t 8 --temp 0.2 -cnv -st \
  -p "Write a Python function factorial(n) with input validation and a short usage example."
```

## 7. Decision Link
See architecture decision record with accepted baseline and rollout plan:
- `docs/architecture/decision-record-local-llm-controller-narration.md`
