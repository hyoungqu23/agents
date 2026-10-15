"""Synthetic ledger builders for contract tests, not a model review or grader."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/review/skills/review-code/scripts/review_result.py'
spec = importlib.util.spec_from_file_location('review_result', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def report_for(scope):
    return {
        'schema_version': 1, 'target': scope['target'],
        'files': [{'path': f['path'], 'classification': 'source', 'risk': 'medium',
                   'status': 'reviewed', 'note': 'Synthetic contract fixture; semantics are evaluated separately.'}
                  for f in scope['files']],
        'passes': {name: {'status': 'complete', 'note': 'Synthetic recorded pass.'}
                   for name in ('standards', 'spec', 'runtime')},
        'quality': {name: {'status': 'not_applicable', 'note': 'Contract fixture only.'} for name in gate.QUALITY},
        'verification': [{'kind': 'static', 'status': 'passed', 'detail': 'Synthetic recorded static comparison.'}],
        'findings': [], 'limitations': []}


def finding_for(scope, path, line, body='Restore the documented behavior.', key='empty-input', revision=None):
    revision = revision or ('head' if scope['target']['mode'] == 'commits' else 'working')
    try:
        quote = gate.source_lines(scope, {'path': path, 'revision': revision})[line-1]
    except (ValueError, OSError, IndexError, TypeError):
        quote = 'Invalid anchor fixture'
    return {'id': key, 'status': 'supported', 'severity': 'P1', 'path': path, 'line': line,
            'revision': revision, 'trigger': 'Synthetic trigger', 'effect': 'Synthetic observed effect',
            'fix': 'Restore the contract', 'refutation': 'Synthetic contrary-evidence check',
            'evidence': [{'path': path, 'revision': revision, 'line': line, 'quote': quote}], 'comment': body}
