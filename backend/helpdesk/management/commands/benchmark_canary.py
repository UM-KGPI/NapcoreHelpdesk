"""
Django management command: benchmark_canary

Run fast canary subset (5 reference questions) for commit-level feedback.
Usage: python manage.py benchmark_canary [--fail-fast]
"""
import json
import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from helpdesk.management.commands.benchmark_utils import (
    load_capability_matrix,
    load_baseline_report,
    get_question_by_id,
    run_benchmark_question,
    compute_percentile,
)


class Command(BaseCommand):
    help = 'Run canary subset benchmark (5 reference questions for commit-level feedback)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='Stop on first failure instead of continuing'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output JSON path (default: docs/testing/benchmark-canary-{timestamp}.json)'
        )

    def handle(self, *args, **options):
        fail_fast = options.get('fail_fast', False)
        output_path = options.get('output')

        # Load capability matrix and baseline
        try:
            matrix = load_capability_matrix()
        except Exception as e:
            raise CommandError(f'Failed to load capability matrix: {e}')

        baseline = load_baseline_report()
        canary_config = matrix.get('canary', {})
        canary_questions = canary_config.get('questions', [])

        if not canary_questions:
            raise CommandError('No canary questions found in capability matrix')

        self.stdout.write(self.style.SUCCESS(
            f'Running canary benchmark: {len(canary_questions)} questions'
        ))

        # Run each question
        results = []
        errors = []
        graph_times = []

        for qdata in canary_questions:
            qid = qdata.get('id')
            intent = qdata.get('intent', 'unknown')

            try:
                # Fetch full question data
                question = get_question_by_id(qid)
                if not question:
                    err_msg = f'{qid}: not found in benchmark questions'
                    errors.append({'id': qid, 'error': err_msg})
                    if fail_fast:
                        raise CommandError(err_msg)
                    continue

                # Run in graph mode
                elapsed_ms, trace, error = run_benchmark_question(question, graph_rag_enabled=True)

                result = {
                    'id': qid,
                    'intent': intent,
                    'elapsed_ms': elapsed_ms,
                    'error': error,
                }

                if error:
                    errors.append({'id': qid, 'error': error})
                    if fail_fast:
                        raise CommandError(f'{qid}: {error}')
                else:
                    graph_times.append(elapsed_ms)
                    result['trace'] = trace
                    result['status'] = 'ok'

                results.append(result)
                status_str = 'ERROR' if error else f'{elapsed_ms} ms'
                self.stdout.write(f'  {qid} ({intent}): {status_str}')

            except Exception as exc:
                if fail_fast:
                    raise
                errors.append({'id': qid, 'error': str(exc)})

        # Compute canary summary
        summary = {
            'tier': 'canary',
            'question_count': len(canary_questions),
            'question_ok': len(results) - len(errors),
            'question_errors': len(errors),
        }

        if graph_times:
            summary.update({
                'graph_avg_ms': round(sum(graph_times) / len(graph_times), 1),
                'graph_p50_ms': compute_percentile(graph_times, 0.5),
                'graph_p95_ms': compute_percentile(graph_times, 0.95),
            })

        # Check pass gates
        passed_gates = self.check_gates(results, baseline, canary_config, summary)
        summary['gates_passed'] = passed_gates['passed']
        summary['gates_failed'] = passed_gates['failed']

        # Output
        if not output_path:
            from datetime import datetime
            ts = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
            repo_root = Path(settings.BASE_DIR).parent
            output_path = repo_root / f'docs/testing/benchmark-canary-{ts}.json'

        output = {
            'summary': summary,
            'results': results,
            'errors': errors,
        }

        output_path = Path(output_path)
        output_path.write_text(json.dumps(output, indent=2), encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f'\nWrote: {output_path}'))
        self.stdout.write(f'Summary: {json.dumps(summary, indent=2)}')

        # Exit code
        if summary['gates_failed']:
            sys.exit(1)

    def check_gates(self, results, baseline, canary_config, summary):
        """Check canary pass/fail gates."""
        passed = []
        failed = []

        # Gate 1: execution
        if summary['question_errors'] == 0:
            passed.append('execution')
        else:
            failed.append(f"execution: {summary['question_errors']} errors")

        # Gate 2: latency_p50
        if baseline and 'graph_p50_ms' in summary:
            baseline_stats = baseline.get('summary', {}).get('global_stats', {})
            baseline_p50 = baseline_stats.get('graph_p50_ms', 0)
            current_p50 = summary['graph_p50_ms']
            if current_p50 <= baseline_p50 * 1.15:
                passed.append('latency_p50')
            else:
                ratio = round(current_p50 / baseline_p50, 2)
                failed.append(f'latency_p50: {current_p50} ms vs baseline {baseline_p50} ms (ratio {ratio})')

        # Gate 3: latency_p95
        if baseline and 'graph_p95_ms' in summary:
            baseline_stats = baseline.get('summary', {}).get('global_stats', {})
            baseline_p95 = baseline_stats.get('graph_p95_ms', 0)
            current_p95 = summary['graph_p95_ms']
            if current_p95 <= baseline_p95 * 1.20:
                passed.append('latency_p95')
            else:
                ratio = round(current_p95 / baseline_p95, 2)
                failed.append(f'latency_p95: {current_p95} ms vs baseline {baseline_p95} ms (ratio {ratio})')

        return {'passed': passed, 'failed': failed}
