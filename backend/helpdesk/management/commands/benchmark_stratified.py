"""
Django management command: benchmark_stratified

Run stratified subset (25 representative questions) for pre-merge validation.
Usage: python manage.py benchmark_stratified [--fail-on-regression <pct>]
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
    help = 'Run stratified subset benchmark (25 representative questions for pre-merge validation)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on-regression',
            type=float,
            default=10.0,
            help='Fail if latency avg change exceeds this percent (default: 10%)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output JSON path (default: docs/testing/benchmark-stratified-{timestamp}.json)'
        )

    def handle(self, *args, **options):
        fail_on_regression = options.get('fail_on_regression', 10.0)
        output_path = options.get('output')

        # Load capability matrix and baseline
        try:
            matrix = load_capability_matrix()
        except Exception as e:
            raise CommandError(f'Failed to load capability matrix: {e}')

        baseline = load_baseline_report()
        if not baseline:
            self.stdout.write(self.style.WARNING('Warning: no baseline report found; gates will be skipped'))

        stratified_config = matrix.get('stratified', {})
        question_groups = stratified_config.get('question_groups', {})

        if not question_groups:
            raise CommandError('No stratified question groups found in capability matrix')

        # Flatten question list
        all_stratified_ids = []
        for intent, group in question_groups.items():
            for q in group.get('questions', []):
                all_stratified_ids.append(q.get('id'))

        self.stdout.write(self.style.SUCCESS(
            f'Running stratified benchmark: {len(all_stratified_ids)} questions across {len(question_groups)} intents'
        ))

        # Run each question
        results = []
        errors = []
        graph_times = []
        intent_times = {}

        for qid in all_stratified_ids:
            try:
                question = get_question_by_id(qid)
                if not question:
                    err_msg = f'{qid}: not found'
                    errors.append({'id': qid, 'error': err_msg})
                    continue

                # Run in graph mode
                elapsed_ms, trace, error = run_benchmark_question(question, graph_rag_enabled=True)
                intent = question.get('intent', 'unknown')

                result = {
                    'id': qid,
                    'intent': intent,
                    'elapsed_ms': elapsed_ms,
                    'error': error,
                }

                if error:
                    errors.append({'id': qid, 'error': error})
                else:
                    graph_times.append(elapsed_ms)
                    if intent not in intent_times:
                        intent_times[intent] = []
                    intent_times[intent].append(elapsed_ms)
                    result['status'] = 'ok'
                    result['trace'] = trace

                results.append(result)
                status_str = 'ERROR' if error else f'{elapsed_ms} ms'
                self.stdout.write(f'  {qid} ({intent}): {status_str}')

            except Exception as exc:
                errors.append({'id': qid, 'error': str(exc)})

        # Compute stratified summary
        summary = {
            'tier': 'stratified',
            'question_count': len(all_stratified_ids),
            'question_ok': len(results) - len(errors),
            'question_errors': len(errors),
        }

        if graph_times:
            summary['graph_avg_ms'] = round(sum(graph_times) / len(graph_times), 1)
            summary['graph_p50_ms'] = compute_percentile(graph_times, 0.5)
            summary['graph_p95_ms'] = compute_percentile(graph_times, 0.95)

        # Intent-level summary
        intent_summary = {}
        for intent, times in intent_times.items():
            intent_summary[intent] = {
                'count': len(times),
                'avg_ms': round(sum(times) / len(times), 1),
                'p50_ms': compute_percentile(times, 0.5),
            }
        summary['intent_summary'] = intent_summary

        # Check pass gates
        passed_gates, failed_gates = self.check_gates(
            results, baseline, stratified_config, summary, fail_on_regression
        )
        summary['gates_passed'] = passed_gates
        summary['gates_failed'] = failed_gates

        # Output
        if not output_path:
            from datetime import datetime
            ts = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
            repo_root = Path(settings.BASE_DIR).parent
            output_path = repo_root / f'docs/testing/benchmark-stratified-{ts}.json'

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
        if failed_gates:
            self.stdout.write(self.style.ERROR(f'Failed gates: {", ".join(failed_gates)}'))
            sys.exit(1)

    def check_gates(self, results, baseline, stratified_config, summary, fail_on_regression):
        """Check stratified pass/fail gates."""
        passed = []
        failed = []

        # Gate 1: execution
        error_rate = summary['question_errors'] / summary['question_count'] if summary['question_count'] > 0 else 0
        if error_rate <= 0.02:
            passed.append('execution')
        else:
            failed.append(f"execution: error rate {error_rate * 100:.1f}% (max 2%)")

        # Gate 2: latency_avg_change
        if baseline and 'graph_avg_ms' in summary:
            baseline_stats = baseline.get('summary', {}).get('global_stats', {})
            baseline_avg = baseline_stats.get('graph_avg_ms', 0)
            current_avg = summary['graph_avg_ms']
            change_pct = ((current_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0

            if change_pct <= fail_on_regression:
                passed.append('latency_avg_change')
            else:
                failed.append(f'latency_avg_change: +{change_pct:.1f}% vs baseline (max +{fail_on_regression}%)')

        # Gate 3: latency_p95_change
        if baseline and 'graph_p95_ms' in summary:
            baseline_stats = baseline.get('summary', {}).get('global_stats', {})
            baseline_p95 = baseline_stats.get('graph_p95_ms', 0)
            current_p95 = summary['graph_p95_ms']
            change_pct = ((current_p95 - baseline_p95) / baseline_p95 * 100) if baseline_p95 > 0 else 0

            if change_pct <= 15:
                passed.append('latency_p95_change')
            else:
                failed.append(f'latency_p95_change: +{change_pct:.1f}% vs baseline (max +15%)')

        # Gate 4: intent_balance
        intent_summary = summary.get('intent_summary', {})
        intent_targets = stratified_config.get('intent_targets', {})
        intent_violations = []

        for intent, times_summary in intent_summary.items():
            if baseline:
                baseline_intent = baseline.get('summary', {}).get('intent_stats', {}).get(intent, {})
                baseline_avg = baseline_intent.get('graph_avg_ms', 0)
                current_avg = times_summary['avg_ms']
                change_pct = ((current_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0

                if change_pct > 12:
                    intent_violations.append(f'{intent}: +{change_pct:.1f}%')

        if not intent_violations:
            passed.append('intent_balance')
        else:
            failed.append(f"intent_balance: {'; '.join(intent_violations)}")

        return passed, failed
