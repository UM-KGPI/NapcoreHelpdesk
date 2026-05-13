"""
Django management command: benchmark_full

Run full 100-question benchmark for release-gate validation.
Usage: python manage.py benchmark_full [--exit-code-on-fail]
"""
import json
import sys
import time
import statistics
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from helpdesk.management.commands.benchmark_utils import (
    load_baseline_report,
    load_benchmark_questions,
    infer_scope_from_question,
    run_benchmark_question,
    compute_percentile,
)


class Command(BaseCommand):
    help = 'Run full 100-question benchmark for release-gate validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--exit-code-on-fail',
            action='store_true',
            help='Exit with code 1 on gate failure'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output JSON path (default: docs/testing/benchmark-full-{timestamp}.json)'
        )
        parser.add_argument(
            '--baseline-file',
            type=str,
            default=None,
            help='Baseline report path for comparison'
        )

    def handle(self, *args, **options):
        exit_on_fail = options.get('exit_code_on_fail', False)
        output_path = options.get('output')
        baseline_file = options.get('baseline_file')

        # Load baseline
        baseline = None
        if baseline_file:
            try:
                baseline = load_baseline_report(baseline_file)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not load baseline: {e}'))
        else:
            baseline = load_baseline_report()

        # Load all questions
        try:
            questions = load_benchmark_questions()
        except Exception as e:
            raise CommandError(f'Failed to load benchmark questions: {e}')

        if not questions:
            raise CommandError('No benchmark questions found')

        self.stdout.write(self.style.SUCCESS(f'Running full benchmark: {len(questions)} questions'))

        # Run each question with both control and graph modes
        results = []
        errors = []
        control_times = []
        graph_times = []
        stage_keys = set()
        intent_buckets = defaultdict(list)

        start_all = time.time()

        for idx, question in enumerate(questions, start=1):
            qid = str(question.get('id', f'q{idx:03d}'))
            intent = question.get('intent', 'unknown')

            row = {'id': qid, 'intent': intent}

            # Run control mode
            try:
                c_time, c_trace, c_error = run_benchmark_question(question, graph_rag_enabled=False)
                if c_error:
                    row['control'] = {'time_ms': c_time, 'error': c_error}
                else:
                    row['control'] = {'time_ms': c_time, 'trace': c_trace}
                    control_times.append(c_time)
            except Exception as exc:
                row['control'] = {'error': str(exc)}

            # Run graph mode
            try:
                g_time, g_trace, g_error = run_benchmark_question(question, graph_rag_enabled=True)
                if g_error:
                    row['graph'] = {'time_ms': g_time, 'error': g_error}
                else:
                    row['graph'] = {'time_ms': g_time, 'trace': g_trace}
                    graph_times.append(g_time)
                    if g_trace:
                        stage = g_trace.get('retrievalStageTimingsMs', {}) or {}
                        stage_keys.update(stage.keys())
            except Exception as exc:
                row['graph'] = {'error': str(exc)}

            # Compute delta
            if 'control' in row and 'graph' in row:
                c_ms = row['control'].get('time_ms')
                g_ms = row['graph'].get('time_ms')
                if c_ms and g_ms and 'error' not in row['control'] and 'error' not in row['graph']:
                    row['delta_ms'] = round(g_ms - c_ms, 1)
                    row['ratio_graph_over_control'] = round((g_ms / c_ms), 3) if c_ms > 0 else None
                    intent_buckets[intent].append(row)

            results.append(row)

            if idx % 10 == 0:
                self.stdout.write(f'progress: {idx}/{len(questions)}')

        elapsed_all = round(time.time() - start_all, 1)

        # Compute stage aggregates
        stage_aggr = {}
        for k in sorted(stage_keys):
            vals = []
            for r in results:
                g_trace = r.get('graph', {}).get('trace', {}) or {}
                st = g_trace.get('retrievalStageTimingsMs', {}) or {}
                if k in st:
                    vals.append(float(st[k]))
            if vals:
                stage_aggr[k] = {
                    'avg_ms': round(statistics.mean(vals), 1),
                    'p50_ms': compute_percentile(vals, 0.5),
                    'p95_ms': compute_percentile(vals, 0.95),
                }

        # Intent-level summary
        intent_stats = {}
        for intent, rows in intent_buckets.items():
            c_vals = [r['control']['time_ms'] for r in rows if 'time_ms' in r.get('control', {})]
            g_vals = [r['graph']['time_ms'] for r in rows if 'time_ms' in r.get('graph', {})]
            intent_stats[intent] = {
                'count': len(rows),
                'control_avg_ms': round(statistics.mean(c_vals), 1) if c_vals else None,
                'graph_avg_ms': round(statistics.mean(g_vals), 1) if g_vals else None,
            }

        # Global summary
        summary = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'question_count_total': len(questions),
            'question_count_ok': len([r for r in results if 'delta_ms' in r]),
            'question_count_errors': len([r for r in results if 'delta_ms' not in r]),
            'elapsed_total_seconds': elapsed_all,
            'global_stats': {
                'control_avg_ms': round(statistics.mean(control_times), 1) if control_times else None,
                'control_p50_ms': compute_percentile(control_times, 0.5),
                'control_p95_ms': compute_percentile(control_times, 0.95),
                'graph_avg_ms': round(statistics.mean(graph_times), 1) if graph_times else None,
                'graph_p50_ms': compute_percentile(graph_times, 0.5),
                'graph_p95_ms': compute_percentile(graph_times, 0.95),
            },
            'intent_stats': intent_stats,
            'graph_stage_stats_ms': stage_aggr,
        }

        # Check pass gates
        passed_gates, failed_gates = self.check_gates(summary, baseline)
        summary['gates_passed'] = passed_gates
        summary['gates_failed'] = failed_gates

        # Output
        if not output_path:
            ts = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
            repo_root = Path(settings.BASE_DIR).parent
            output_path = repo_root / f'docs/testing/benchmark-full-{ts}.json'

        output = {
            'summary': summary,
            'results': results,
        }

        output_path = Path(output_path)
        output_path.write_text(json.dumps(output, indent=2), encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f'\nWrote: {output_path}'))
        self.stdout.write(f'Summary: {json.dumps(summary, indent=2)}')

        # Exit code
        if failed_gates and exit_on_fail:
            self.stdout.write(self.style.ERROR(f'Failed gates: {", ".join(failed_gates)}'))
            sys.exit(1)

    def check_gates(self, summary, baseline):
        """Check full benchmark pass/fail gates."""
        passed = []
        failed = []

        # Gate 1: execution
        if summary['question_count_errors'] == 0:
            passed.append('execution')
        else:
            failed.append(f"execution: {summary['question_count_errors']} errors")

        if not baseline:
            return passed, failed

        baseline_stats = baseline.get('summary', {}).get('global_stats', {})

        # Gate 2: latency_avg_change
        baseline_avg = baseline_stats.get('graph_avg_ms', 0)
        current_avg = summary['global_stats']['graph_avg_ms']
        if baseline_avg and current_avg:
            change_pct = ((current_avg - baseline_avg) / baseline_avg * 100)
            if change_pct <= 8:
                passed.append('latency_avg_change')
            else:
                failed.append(f'latency_avg_change: +{change_pct:.1f}% (max +8%)')

        # Gate 3: latency_p50_change
        baseline_p50 = baseline_stats.get('graph_p50_ms', 0)
        current_p50 = summary['global_stats']['graph_p50_ms']
        if baseline_p50 and current_p50:
            change_pct = ((current_p50 - baseline_p50) / baseline_p50 * 100)
            if change_pct <= 12:
                passed.append('latency_p50_change')
            else:
                failed.append(f'latency_p50_change: +{change_pct:.1f}% (max +12%)')

        # Gate 4: latency_p95_change
        baseline_p95 = baseline_stats.get('graph_p95_ms', 0)
        current_p95 = summary['global_stats']['graph_p95_ms']
        if baseline_p95 and current_p95:
            change_pct = ((current_p95 - baseline_p95) / baseline_p95 * 100)
            if change_pct <= 15:
                passed.append('latency_p95_change')
            else:
                failed.append(f'latency_p95_change: +{change_pct:.1f}% (max +15%)')

        # Gate 5: intent_coverage
        intent_stats = summary.get('intent_stats', {})
        if len(intent_stats) == 5:  # All 5 intents present
            passed.append('intent_coverage')
        else:
            failed.append(f'intent_coverage: {len(intent_stats)}/5 intents present')

        return passed, failed
