# Recent Updates & API Changes

**Last Updated:** September 21, 2026

This document covers recent feature additions, API improvements, and deployment changes.

## 1. Deep-Linking to Specific Questions

**Enabled:** Query parameter support for direct question access in the editor.

### URL Format

```
https://kgpi.fgpa.um.si/napcore-helpdesk/editor?questionId=<REQUEST_ID>
```

### Example

```
https://kgpi.fgpa.um.si/napcore-helpdesk/editor?questionId=req-mr0tatgt-bmw50d
```

### Behavior

When a user visits a link with `?questionId=...`:
- The editor automatically loads that question
- Question details and all citations are pre-populated
- The question is auto-selected in the "Asked Questions" list

### Use Case

Share specific Q&A results with colleagues or embed links in documentation.

---

## 2. Multilingual Support

**Enabled:** Automatic language detection and response in user's browser language.

### Browser Language Detection

The frontend detects the user's browser language and sends it to the backend:
- English (en)
- Norwegian (no, nb, nn)
- Slovenian (sl)
- German (de)
- French (fr)
- Spanish (es)
- Italian (it)
- Dutch (nl)
- Polish (pl)
- Portuguese (pt)
- Swedish (sv)
- Danish (da)
- Finnish (fi)
- Czech (cs)
- Slovak (sk)
- Hungarian (hu)
- Romanian (ro)
- Croatian (hr)
- Bulgarian (bg)
- Greek (el)
- Lithuanian (lt)
- Latvian (lv)
- Estonian (et)
- Maltese (mt)
- Irish (ga)

### API Request

```json
POST /questions/answer
{
  "question": "What is a STOP PLACE?",
  "language": "Slovenian"
}
```

### LLM Behavior

- If `language` is set: LLM responds in that language, keeping technical terms in English
- If `language` is "en" or "English": LLM auto-detects question language and responds in kind
- XML tags, class names, and identifiers always stay in English

### Example

**Question in Slovenian:**
```
"Kaj je STOP PLACE v NeTEx?"
```

**Response (in Slovenian):**
```
"STOP PLACE je fizična lokacija ali skupina lokacij v NeTEx standardu.
Ločena je od SCHEDULED STOP POINT, ki predstavlja ...
```

---

## 3. Improved Evidence Citations

**Fixed:** Removed duplicate file paths in evidence display.

### Before

```
[E1] xsd/netex_framework/netex_reusableComponents/netex_spotAffinity_version.xsd · xsd/netex_framework/netex_reusableComponents/netex_spotAffinity_version.xsd
```

### After

```
[E1] netex_spotAffinity_version.xsd
```

### Rules

- If evidence has a meaningful label: show label only
- If no label exists: show filename only (cleaner than full path)
- If label differs from source path: show `label · full/path` for context

---

## 4. Enhanced Answer Generation for Examples

**Improved:** Grounded generator now includes actual XML/code snippets.

### Fallback Behavior

When LLM is unavailable and user asks for examples, the deterministic fallback now includes:

```
[E1] netex_spotAffinity_version.xsd (NeTEx)
```xml
<?xml version="1.0"?>
<Stop>
  ...
</Stop>
```

**Before:** Only listed filenames
**After:** Includes actual code snippets up to 300 chars

---

## 5. Deployment Verification Commands

**New Make Targets:**

### `make deploy-verify`

Comprehensive pre-deployment checks:

```bash
make deploy-verify
```

Verifies:
1. ✓ Working tree clean (no uncommitted changes)
2. ✓ No pending database migrations
3. ✓ Django system checks pass
4. ✓ Frontend builds successfully
5. ✓ Git commit history visible
6. ✓ Pre-commit hooks pass

**Use before every push to ensure code is deployment-ready.**

### `make deploy-build`

Build production Docker images locally:

```bash
make deploy-build
```

Builds: `docker compose -f docker-compose.prod.yml build --pull`

---

## 6. LLM Token Configuration

**Critical for Production:** `LLM_MAX_TOKENS` controls answer length.

### Default Value

```
LLM_MAX_TOKENS=250
```

### Impact on Examples

**At 250 tokens:**
- Explanation fits
- XML snippets get truncated
- Answers may be cut off mid-element

**Recommended for examples:**
```
LLM_MAX_TOKENS=600
```

### Where to Set

In production `.env.prod`:
```bash
# More generous token budget for complete XML examples
LLM_MAX_TOKENS=600
```

### Related Settings

- `LLM_TIMEOUT_SECONDS=20` — Max wait for LLM response (production default)
- `CONTROLLER_LLM_MAX_TOKENS=96` — Token budget for routing decisions
- Local dev uses `LLM_MAX_TOKENS=4000` for testing

---

## 7. CORS Configuration via Environment Variables

**Fixed:** CORS origins now configurable, not hardcoded.

### Before (Broken in Production)

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

**Problem:** Hardcoded values broke production deployment.

### After (Configurable)

```bash
# In .env.prod or setup-env-prod.sh
CORS_ALLOWED_ORIGINS=https://kgpi.fgpa.um.si/napcore-helpdesk
```

### Setup

Run on production server:
```bash
/opt/napcore-helpdesk/scripts/setup-env-prod.sh
# Prompts for: Frontend URL for CORS
```

---

## 8. Deployment Workflow (GitHub → Server)

**Established:** All changes flow through GitHub. No direct server edits.

### Pipeline

```
Local Development
    ↓ (make deploy-verify)
GitHub main branch
    ↓ (git push origin main)
Production server (git pull origin main)
    ↓ (docker compose up -d)
Running container
```

### Key Rule

**Never edit files directly on production server** (except `.env.prod`).

All code changes:
1. Commit locally
2. Run `make deploy-verify`
3. Push to GitHub
4. Pull on server

---

## 9. Semantic Question Parsing

**New Service:** `QuestionParsingService` extracts structured intent from natural language.

### Available Intents

- `normative_status` — Questions about SHALL/MUST/SHOULD/MAY requirements
- `definition` — "What is X?" questions
- `location` — "Where is X?" questions
- `cross_standard_relation` — Comparisons between standards
- `comparison` — How standards differ
- `unknown` — Default fallback

### Normativity Detection

- `mandatory` — Contains "shall", "must", "required"
- `recommended` — Contains "should"
- `optional` — Contains "may"
- `unspecified` — Default

### Use in Backend

Automatically applied in answer orchestration; no frontend changes needed.

---

## 10. LLM Model Alias Fix (litellm gateway)

**Root cause:** the shared litellm gateway (`https://litellm.lhrs.si/v1`) renamed/rescoped the
model alias this deployment used. The API key is now only authorized for
`nvidia/Qwen3.6-35B-A3B-NVFP4`; requests for the old alias `qwen36-35b-a3b` returned
`403 key_model_access_denied`.

### Symptom

The failure was silent from a user's perspective: `llm_generator.py` catches the LLM error and
falls back to the deterministic `grounded_generator` template, so every answer looked like
generic boilerplate ("Based on retrieved approved-source evidence [E1] [E2], follow the relevant
profile specification...") regardless of the question, with no visible error in the UI. Only
`docker logs` showed the real cause:

```
LLM HTTP error: 403 - {"error":{"message":"key not allowed to access model.
This key can only access models=['nvidia/Qwen3.6-35B-A3B-NVFP4']. ...
```

### Fix

```bash
LLM_MODEL=nvidia/Qwen3.6-35B-A3B-NVFP4
CONTROLLER_LLM_API_MODEL=nvidia/Qwen3.6-35B-A3B-NVFP4
```

Applied to local `backend/.env` (gitignored, not tracked) and to the `backend/.env.prod.example`
template so new deployments don't inherit the stale alias. Verified end-to-end after the fix: a
real question through the frontend now returns a genuine LLM-composed, cited answer instead of
the fallback template, with no errors in `docker logs` or the browser console.

### Related Settings

- `LLM_ENABLED` / `CONTROLLER_LLM_ENABLED` must both be `True` for this path to be exercised at
  all; when either is `False`, the same fallback template is used by design, not by failure.
- If this alias changes again, `docker logs <backend-container> | grep "403\|fallback"` is the
  fastest way to confirm it's the same failure mode.

**Follow-up (same day):** the identical break recurred independently in **production**, because
`/opt/napcore-helpdesk/backend/.env.prod` is a file that exists only on the deploy VM -- fixing
`backend/.env.prod.example` (a template used only when setting up a *new* deployment) never
touches it. Production and dev share the same litellm key, so the same fix value applied, but it
had to be made by hand over SSH. See §11 for the mechanism added so a third recurrence -- on
either dev or production -- doesn't require this again.

---

## 11. Self-Healing LLM Model Recovery

**Problem this closes:** §10 happened twice (dev, then production) from the same underlying
cause -- the litellm gateway renaming/rescoping the authorized model alias without notice -- and
each time required a human to notice a degraded answer, read `docker logs`, and hand-edit an env
file. Nothing detected the drift automatically, and a config fix pushed to git doesn't reach an
already-running deployment's `.env`/`.env.prod` on its own.

### How it works

The gateway's own `403 key_model_access_denied` response body already names the model the key
*is* authorized for:

```
{"error":{"message":"key not allowed to access model. This key can only
access models=['nvidia/Qwen3.6-35B-A3B-NVFP4']. Tried to access ...
```

`backend/helpdesk/services/llm_model_recovery.py` parses that name out, retries the same request
once with the corrected model, and caches the correction in-process so subsequent calls skip
straight to it instead of paying the 403 round trip every time. Wired into all three places that
call the gateway: streaming answer generation (the live frontend path), non-streaming answer
generation, and the routing controller.

It always logs loudly -- `WARNING` the first time, tagged `LLM_MODEL_AUTO_CORRECTED` so it's easy
to `grep`/alert on:

```
docker logs <backend-container> | grep LLM_MODEL_AUTO_CORRECTED
```

### What this is, and isn't

This is a live workaround that keeps the app answering through a gateway rename, **not** a
substitute for fixing `LLM_MODEL` / `CONTROLLER_LLM_API_MODEL` in the environment -- every request
before the correction is cached pays an extra round trip, and the cache is per-process (per
worker), so a multi-worker production deployment rediscovers it once per worker rather than once
globally. It also doesn't help if the gateway is down entirely, or if the 403 body format changes
in a way the parser doesn't recognize -- in either case behavior falls back to §10's original
failure mode (silent fallback to the deterministic template), not a new failure.

**Verified two ways:** 6 new unit tests (parser, cache, and each of the three call sites), plus a
live end-to-end reproduction -- the old broken model alias was put back into the running dev
backend, the container recreated, and a real question asked through the frontend. It answered
correctly with proper citations despite the wrong configured model, and the logs showed
`LLM_MODEL_AUTO_CORRECTED` firing on the live streaming path.

---

## 12. LLM Status Endpoint + Proactive Self-Heal

**Problem this closes:** §11's self-heal was purely *reactive* — it only discovered a drifted
model alias after a real answer-generation or routing call had already failed with a 403, and
there was no way to check "is the LLM actually healthy right now" without asking a real question
and reading logs. Both gaps came up directly: "Do we have any API endpoint that checks status of
the LLM and its model?" (there wasn't one), and "now the self-healing fix can use the new api to
maintain the microservice based logic" (it wasn't using its own status check).

### New endpoint: `GET /api/v1/health/llm`

Diagnostic endpoint (not a traffic-gating readiness probe — always returns `200`, with health
conveyed only via the body's `status` field). No authentication required, same as `/health/live`
and `/health/ready` — directly viewable by navigating to it in a browser. For both
`answer_generation` and `controller_routing`, reports:

- configured model vs. the model actually in use (`activeModel`)
- whether the gateway is live-reachable right now, and its current authorized-model list
  (`GET {api_base_url}/models` — a free, read-only OpenAI-compatible call, no completion tokens
  billed)
- whether the self-heal has already corrected drift this process

`?live=false` skips the live gateway call and reports cached state only.

### Self-heal now uses that same probe proactively

`backend/helpdesk/services/llm_model_recovery.py` gained `resolve_effective_model()`, which all
three call sites (streaming answer generation, non-streaming answer generation, controller
routing) now use in place of the old "cached correction or configured model" lookup. Before the
first LLM call in a process, it checks the gateway's live model list:

- configured model is in the list → cached as verified, no further probing this process
- exactly one authorized model, and it differs → treated as the correction (same as the reactive
  403 path, same `LLM_MODEL_AUTO_CORRECTED` log line, tagged `..._preflight`)
- ambiguous (zero or multiple candidates) or the probe itself fails → falls through unchanged to
  §11's existing reactive 403 handler, which still has the last word

Net effect: a fresh deploy with a drifted alias now self-heals **before** the first real user
request, not after one fails and falls back to the deterministic boilerplate template.

**Verified two ways:** the probe resolved a deliberately stale model name against the real litellm
gateway with zero prior 403s (confirmed via `get_cached_correction`), and the full test suite
(24 tests across `test_llm_generator.py`, `test_llm_model_recovery.py`, `test_controller_llm.py`)
passes with the live network call properly mocked everywhere — 6 pre-existing tests needed a new
mock added, since without it they'd have started making real HTTP calls during test runs.

---

## 13. LLM Status Page — Added, Then Removed (Superseded by §12)

A dedicated "LLM status" page (`/napcore-helpdesk/llm-status`) was briefly added to render
`GET /health/llm`'s result more readably than raw JSON. Once §12's endpoint was made public (no
auth, same as `/health/live`/`/health/ready`), the page became redundant — the endpoint itself is
now directly viewable in any browser, so the extra route, nav link, API client method, and CSS
were removed rather than kept as unused surface. Check LLM status via `GET /health/llm` directly.

---

## 14. API Documentation Drift Fix

**Found while adding §12's endpoint:** `docs/api-description.md` and `api/openapi.yaml` (the
"authoritative contract" the description doc points to) were both already missing several
endpoints that existed in `urls.py` before this session touched anything — `POST /auth/dev-token`,
`GET /questions/trending`, and the `GET`/`DELETE` detail routes on `/questions/events/{id}`.

Added those plus `GET /health/llm`, with full OpenAPI request/response schemas
(`LlmStatusResponse`, `LlmProviderStatus`, `DevTokenResponse`, `TrendingQuestionsResponse`,
`QuestionEventDetailResponse`). Validated with `npx @redocly/cli lint api/openapi.yaml` — 0
errors; the 2 remaining warnings (missing `info.license`, a `localhost` server entry) predate this
fix and are unrelated.

---

## 15. C4 Diagrams Updated for LLM Model Recovery

The Level 2 container diagram and Level 3 orchestrator-components diagram
([docs/diagrams/c4-container.svg](diagrams/c4-container.svg),
[docs/diagrams/c4-orchestrator-components.svg](diagrams/c4-orchestrator-components.svg)) now
reflect §12: a new **LLM Model Recovery** domain component (`llm_model_recovery.py`) sitting
between the Controller/Narration components and their respective model runtimes, and a new
**LLM Health Check** REST controller for `GET /health/llm`, explicitly noted as public,
unauthenticated, and outside the question-answering pipeline. The container-level relationships to
both model runtimes are annotated "(self-heals model-alias drift)", with a note pointing to the
Level 3 diagram for detail. The Level 1 system-context diagram is unchanged — this is an internal
implementation detail below that level of abstraction.

---

## Configuration Reference

### Production Environment Variables (`.env.prod`)

```bash
# Deployment essentials
DJANGO_ALLOWED_HOSTS=kgpi.fgpa.um.si
CORS_ALLOWED_ORIGINS=https://kgpi.fgpa.um.si/napcore-helpdesk

# LLM settings
LLM_ENABLED=True
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=600              # For better example responses
LLM_TIMEOUT_SECONDS=20

# Controller LLM (routing)
CONTROLLER_LLM_ENABLED=True
CONTROLLER_LLM_API_BASE_URL=https://api.openai.com/v1
CONTROLLER_LLM_API_KEY=sk-...
CONTROLLER_LLM_API_MODEL=gpt-4o-mini
CONTROLLER_LLM_MAX_TOKENS=96
```

### Local Development (`.env`)

Already configured; uses:
- `nvidia/Qwen3.6-35B-A3B-NVFP4` (Qwen3.6, 35B total / 3B active MoE, NVFP4 quantization) via litellm.lhrs.si — see [§10](#10-llm-model-alias-fix-litellm-gateway) for why the exact model string matters
- `LLM_MAX_TOKENS=4000` (generous for testing)
- CORS allows `localhost:5173`

---

## Testing New Features

### Test Deep-Linking

```bash
# Local
http://localhost:5173/napcore-helpdesk/editor?questionId=req-mr0tatgt-bmw50d

# Production
https://kgpi.fgpa.um.si/napcore-helpdesk/editor?questionId=req-mr0tatgt-bmw50d
```

### Test Multilingual Response

Ask in your browser's language:
```
"¿Qué es un STOP PLACE?"  // Spanish
"Qu'est-ce qu'une STOP PLACE?"  // French
"Kaj je STOP PLACE?"  // Slovenian
```

### Test Example Snippets

```
"Show me an example of a ScheduledStopPoint in NeTEx XML"
```

Should return actual XML code blocks (with `LLM_MAX_TOKENS ≥ 600`).

---

## Troubleshooting

### Examples not showing XML snippets

**Cause:** `LLM_MAX_TOKENS` too low (production default 250)
**Fix:** Increase to 600+

```bash
# Update .env.prod
LLM_MAX_TOKENS=600
# Redeploy
docker compose -f docker-compose.prod.yml up -d
```

### CORS errors in browser console

**Cause:** `CORS_ALLOWED_ORIGINS` doesn't match frontend URL
**Fix:** Run setup script or verify `.env.prod`

```bash
/opt/napcore-helpdesk/scripts/setup-env-prod.sh
# Re-enter frontend URL when prompted
```

### Deep-link doesn't load question

**Cause:** Question ID doesn't exist or was deleted
**Fix:** Navigate through "Asked Questions" list to find valid IDs

### Answers look like generic boilerplate regardless of the question

**As of §11–§12, this should now be rare** — a wrong `LLM_MODEL`/`CONTROLLER_LLM_API_MODEL` alias
self-corrects at runtime (proactively as of §12, not just reactively after a failed call) instead
of falling back silently. **First check** `GET /health/llm` (§12) — public, no auth needed, so you
can just visit `http://localhost:8000/api/v1/health/llm` in a browser — it shows the configured vs.
active model and whether the gateway currently authorizes the configured one, without needing to
ask a real question first. If it reports `error` or `degraded`, or the boilerplate persists despite
an `ok` status:
**Cause:** either the self-heal's parser didn't recognize the gateway's error format, or the
gateway is down/erroring for a different reason entirely (see [§10](#10-llm-model-alias-fix-litellm-gateway),
[§11](#11-self-healing-llm-model-recovery), [§12](#12-llm-status-endpoint--proactive-self-heal)).
**Fix:** `docker logs <backend-container> | grep "403\|fallback\|LLM_MODEL_AUTO_CORRECTED"` — if
`LLM_MODEL_AUTO_CORRECTED` is present, the alias was already fixed automatically and the boilerplate
answer predates that; if a `403` appears with no `LLM_MODEL_AUTO_CORRECTED` line, the gateway's error
body changed shape and the parser in `llm_model_recovery.py` needs updating.

---

## References

- [API OpenAPI Spec](../api/openapi.yaml)
- [Production Deployment Guide](production-deployment.md)
- [LLM Usage](llm-usage.md)
- [Architecture Overview](architecture-overview.md)
