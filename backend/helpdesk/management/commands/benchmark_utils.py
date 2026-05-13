"""
Shared utilities for benchmark management commands.
"""
import json
import time
from pathlib import Path
from django.conf import settings


def load_capability_matrix():
    """Load capability-matrix.yaml into a Python dict."""
    import yaml
    matrix_path = Path(settings.BASE_DIR).parent / 'docs/testing/capability-matrix.yaml'
    with matrix_path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_baseline_report(report_path=None):
    """Load baseline benchmark JSON report."""
    if not report_path:
        repo_root = Path(settings.BASE_DIR).parent
        report_path = repo_root / 'docs/testing/benchmark-graphrag-ab-2026-05-11.json'
    
    if not report_path.exists():
        return None
    
    with report_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_benchmark_questions():
    """Load benchmark questions from YAML."""
    import yaml
    repo_root = Path(settings.BASE_DIR).parent
    questions_path = repo_root / 'docs/testing/benchmark-questions.yaml'
    
    with questions_path.open('r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    
    return raw.get('questions', []) if isinstance(raw, dict) else []


def get_question_by_id(qid, all_questions=None):
    """Retrieve a single question by ID."""
    if not all_questions:
        all_questions = load_benchmark_questions()
    
    for q in all_questions:
        if str(q.get('id', '')).lower() == str(qid).lower():
            return q
    return None


def infer_scope_from_question(question):
    """Infer standards scope from question tags."""
    scope = question.get('scope')
    if isinstance(scope, list) and scope:
        return scope
    
    tags = question.get('tags', []) if isinstance(question.get('tags', []), list) else []
    inferred = []
    for t in tags:
        tl = str(t).lower()
        if tl == 'netex':
            inferred.append('NeTEx')
        elif tl == 'opra':
            inferred.append('OpRa')
        elif tl == 'siri':
            inferred.append('SIRI')
        elif tl in {'datex', 'datexii', 'datex ii'}:
            inferred.append('DATEX II')
    return sorted(set(inferred)) if inferred else None


def run_benchmark_question(question, graph_rag_enabled=True, timeout_ms=15000):
    """
    Run a single benchmark question and return timing + trace.
    Returns: (elapsed_ms, trace, error_str or None)
    """
    from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace
    
    q_text = str(question.get('question', '')).strip()
    scope = infer_scope_from_question(question)
    
    start = time.time()
    try:
        chunks, trace = retrieve_chunks_with_trace(
            question=q_text,
            top_k=6,
            min_score=0.62,
            scope=scope,
            graph_rag_enabled=graph_rag_enabled,
        )
        elapsed_ms = round((time.time() - start) * 1000, 1)
        return elapsed_ms, trace, None
    except Exception as exc:
        elapsed_ms = round((time.time() - start) * 1000, 1)
        return elapsed_ms, {}, str(exc)


def compute_percentile(values, q):
    """Compute percentile q (0.0–1.0) from a list of values."""
    if not values:
        return None
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * q
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    if f == c:
        return vals[f]
    return round(vals[f] + (vals[c] - vals[f]) * (k - f), 1)
