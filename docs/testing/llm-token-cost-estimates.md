# LLM token and cost estimates (gpt-4o-mini)

Last updated: 2026-05-16

## Scope

This page documents observed token usage and estimated API cost for narration calls on the RAG path.

## Data source

Metrics are computed from production telemetry stored in Django models:

- `QuestionEvent` (question, answer, mode, timestamps)
- `RetrievalEvent` (retrieved chunk links per question)
- `SourceChunk` (retrieved text payload)

RAG prompts are reconstructed with the same code path used by narration prompt assembly (`_build_messages`).

## Pricing assumptions

Model: gpt-4o-mini

- Input price: $0.15 per 1M tokens
- Output price: $0.60 per 1M tokens

Token conversion used in this estimate:

- tokens ~= characters / 4

This is an estimate and can differ from provider-side tokenizer billing.

## Measured token profile

Sample size:

- RAG events with reconstructed prompt: 109

Prompt configuration at measurement time:

- `LLM_MAX_EVIDENCE_CHUNKS = 4`
- `LLM_MAX_EVIDENCE_CHARS_PER_CHUNK = 1200`

Measured values:

- Average input tokens: 1160.578
- P50 input tokens: 1120.5
- P95 input tokens: 1747.0
- Average output tokens: 138.333

Interpretation:

- P50 is the median request size.
- P95 is the upper-tail request size (95 percent of requests are at or below this value).

## Cost formulas

Per question:

- `cost_in = (input_tokens / 1,000,000) * 0.15`
- `cost_out = (output_tokens / 1,000,000) * 0.60`
- `cost_total = cost_in + cost_out`

Monthly:

- `monthly_cost = questions_per_day * 30 * cost_total`

## Cost per question (avg vs percentiles)

Using average output tokens (138.333):

- Average input case: $0.000257086 per question
- P50 input case: $0.000251075 per question
- P95 input case: $0.000345050 per question

## Observed traffic baseline

Recent observed volume:

- Last 7 days: 100 questions (14.286 questions/day)
- Last 30 days: 127 questions (4.233 questions/day)

Estimated monthly cost at observed pace:

- 7-day pace, average input: $0.110180 per month
- 7-day pace, P50 input: $0.107603 per month
- 7-day pace, P95 input: $0.147878 per month
- 30-day pace, average input: $0.032650 per month
- 30-day pace, P50 input: $0.031886 per month
- 30-day pace, P95 input: $0.043821 per month

## Scale scenarios

Monthly cost at larger daily volumes (30-day month):

- 100 questions/day: average $0.771, P95 $1.035
- 1,000 questions/day: average $7.713, P95 $10.351
- 10,000 questions/day: average $77.126, P95 $103.515

## Recompute command

Run from repository root:

```bash
cd backend && ../.venv/bin/python manage.py shell -c "from helpdesk.models import QuestionEvent, RetrievalEvent, SourceChunk; from helpdesk.services.llm_generator import _build_messages; from django.conf import settings; from django.utils import timezone; from datetime import timedelta; import statistics
PRICE_IN=0.15; PRICE_OUT=0.60
rag_events=list(QuestionEvent.objects.filter(mode='rag').order_by('created_at'))
input_chars=[]; output_chars=[]
for ev in rag_events:
    rets=list(RetrievalEvent.objects.filter(question_event=ev).order_by('-score')[:max(1,int(getattr(settings,'LLM_MAX_EVIDENCE_CHUNKS',4)))])
    if not rets: continue
    chunks_by_id={c.chunk_id:c for c in SourceChunk.objects.filter(chunk_id__in=[r.chunk_id for r in rets])}
    chunks=[]
    for r in rets:
        c=chunks_by_id.get(r.chunk_id)
        if c: chunks.append({'repositoryUrl':c.repository_url,'commitSha':c.commit_sha,'sourcePath':c.source_path,'chunkId':c.chunk_id,'text':c.text,'score':r.score})
    if not chunks: continue
    msgs=_build_messages(question=ev.question,chunks=chunks,scope=ev.standards_scope,max_chunks=max(1,int(getattr(settings,'LLM_MAX_EVIDENCE_CHUNKS',4))),max_chars_per_chunk=max(200,int(getattr(settings,'LLM_MAX_EVIDENCE_CHARS_PER_CHUNK',1200))))
    input_chars.append(sum(len(m.get('content','')) for m in msgs)); output_chars.append(len(ev.answer or ''))

t=lambda c: c/4.0
avg_in=t(statistics.mean(input_chars)); p50_in=t(statistics.median(input_chars)); p95_in=t(sorted(input_chars)[int(0.95*(len(input_chars)-1))]); avg_out=t(statistics.mean(output_chars))
per=lambda i,o: (i/1_000_000.0)*PRICE_IN + (o/1_000_000.0)*PRICE_OUT
print({'avg_in':avg_in,'p50_in':p50_in,'p95_in':p95_in,'avg_out':avg_out,'per_q_avg':per(avg_in,avg_out),'per_q_p50':per(p50_in,avg_out),'per_q_p95':per(p95_in,avg_out),'q7':QuestionEvent.objects.filter(created_at__gte=timezone.now()-timedelta(days=7)).count(),'q30':QuestionEvent.objects.filter(created_at__gte=timezone.now()-timedelta(days=30)).count()})"
```

## Notes

- These estimates include narration prompt and answer body size, not non-LLM retrieval/database compute cost.
- If provider pricing changes, update prices first, then recompute derived costs.
- For finance-grade reporting, replace chars/4 with model-tokenizer counted tokens from API usage metadata.
