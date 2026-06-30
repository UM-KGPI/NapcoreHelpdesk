# Recent Updates & API Changes

**Last Updated:** June 30, 2026

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
- Qwen3 35B quantized (a3b variant) via litellm.lhrs.si
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

---

## References

- [API OpenAPI Spec](../api/openapi.yaml)
- [Production Deployment Guide](production-deployment.md)
- [LLM Usage](llm-usage.md)
- [Architecture Overview](architecture-overview.md)
