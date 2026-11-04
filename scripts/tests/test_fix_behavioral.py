"""Mechanical sensitivity only: synthetic records/observations are not host runs."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

from test_review_skill_install import broken_links

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/behavioral'))
spec = importlib.util.spec_from_file_location('fix_evaluation', ROOT / 'scripts/behavioral/fix.py')
evaluation = importlib.util.module_from_spec(spec); spec.loader.exec_module(evaluation)


class FixEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.output = self.root / 'case'

    def records(self, case='no-browser', changed=True):
        metadata = evaluation.prepare(self.output, case)
        self.source, self.state = Path(metadata['source']), Path(metadata['state'])
        if changed:
            path = self.source / ('src/project-list.js' if case == 'bug' else 'src/app.js')
            with path.open('a') as stream: stream.write('\n// Synthetic mechanical-test edit.\n')
        self.refresh_changes()
        evidence = self.state / 'evidence.txt'; evidence.write_text('Synthetic evidence only, not an executed check.\n')
        self.result = {'schema_version': 1, 'changed_files': self.changes,
                       'change_reasons': {p: 'Synthetic test edit' for p in self.changes},
                       'items': [{'id': evaluation.CASES[case][1], 'action': 'already_satisfied' if case == 'no-change' else 'applied',
                                  'reason': 'Synthetic record', 'checks': [
                                      {'kind': 'command', 'status': 'passed', 'detail': 'Synthetic check', 'command': ['node', '--test'],
                                       'cwd': str(self.source), 'exit_code': 0, 'evidence': ['evidence.txt']},
                                      {'kind': 'browser', 'status': 'not_run' if case == 'no-browser' else 'passed',
                                       'detail': 'Synthetic browser record', 'reason': 'Synthetic limitation', 'tool': 'test double',
                                       'url': 'http://127.0.0.1/', 'scenario': 'Synthetic observation',
                                       'viewport': {'width': 1000, 'height': 800}, 'evidence': ['evidence.txt']},
                                  ]}]}
        self.observed = {k: True for k in ('model_contract', 'selection_preserved', 'retry_current_filter', 'actual_app',
                         'reset_to_all', 'select_synchronized', 'selection_restored', 'action_empty_only', 'design_matches',
                         'responsive', 'regression_failed_before', 'regression_passed_after', 'latest_result')}
        self.observed['source_digest'] = evaluation.gate.digest(evaluation.hashes(self.source))

    def refresh_changes(self):
        coordinator = self.output / 'coordinator'
        before = evaluation.gate.snapshot(coordinator / 'baseline.json')
        after = evaluation.gate.capture(self.source, coordinator / 'inputs.json')
        actual = {p for p in set(before['files']) | set(after['files']) if before['files'].get(p) != after['files'].get(p)}
        hashes = evaluation.hashes(self.source)
        self.changes = {p: hashes.get(p) for p in actual}

    def grade(self):
        evaluation.write(self.state / 'result.json', self.result)
        observation = self.root / 'synthetic-observations.json'; evaluation.write(observation, self.observed)
        return evaluation.grade(self.output, observation)

    def test_standalone_install_and_prepare_boundaries(self):
        self.records()
        installed = self.output / 'fix'
        self.assertFalse((installed / 'evals').exists()); self.assertEqual(broken_links(installed), [])
        self.assertIn('src/user-note.js', evaluation.gate.snapshot(self.output / 'coordinator/baseline.json')['dirty'])
        with self.assertRaises(FileExistsError): evaluation.prepare(self.output, 'bug')
        with self.assertRaises(ValueError): evaluation.prepare(ROOT / 'forbidden', 'bug')

    def test_partial_adapter_accepts_recorded_browser_limit(self):
        self.records(); self.assertEqual(self.grade()['status'], 'passed')

    def test_no_change_disposition_does_not_require_an_edit(self):
        self.records('no-change', changed=False)
        self.assertEqual(self.grade()['status'], 'passed')
        self.result['items'][0]['checks'][1]['status'] = 'not_run'
        self.assertEqual(self.grade()['status'], 'passed')
        self.result['items'][0]['checks'][1]['status'] = 'failed'
        self.assertEqual(self.grade()['status'], 'failed')

    def test_noop_and_unapplied_items_do_not_pass_correction_cases(self):
        self.records(changed=False)
        self.assertFalse(self.grade()['checks']['change_matches_case'])
        for action in ('already_satisfied', 'needs_decision', 'not_applied'):
            self.result['items'][0]['action'] = action
            self.assertFalse(self.grade()['checks']['disposition'])

    def test_unsupported_or_self_assessed_schema_is_rejected(self):
        self.records()
        original = copy.deepcopy(self.result)
        for extra in ({'schema_version': True}, {'status': 'complete'}, {'complete': True}):
            self.result = {**original, **extra}
            self.assertFalse(self.grade()['checks']['result_contract'])

    def test_malformed_checks_fail_without_crashing(self):
        self.records()
        for value in (None, 'passed', []):
            self.result['items'][0]['checks'] = [value]
            self.assertEqual(self.grade()['status'], 'failed')

    def test_false_browser_pass_cannot_hide_in_an_optional_record(self):
        self.records()
        self.result['items'][0]['checks'].append({**self.result['items'][0]['checks'][1], 'status': 'passed'})
        self.assertFalse(self.grade()['checks']['browser_boundary'])

    def test_full_ui_case_needs_actual_browser_record(self):
        self.records('qa'); self.result['items'][0]['checks'].pop()
        self.assertFalse(self.grade()['checks']['browser_boundary'])

    def test_evidence_cannot_escape_or_be_empty(self):
        self.records(); record = self.result['items'][0]['checks'][0]
        (self.state / 'link').symlink_to(self.source / 'task.md')
        for path in ('missing', '../source/task.md', 'link'):
            record['evidence'] = [path]; self.assertEqual(self.grade()['status'], 'failed')
        record['evidence'] = ['evidence.txt']; (self.state / 'evidence.txt').write_text('')
        self.assertEqual(self.grade()['status'], 'failed')

    def test_empty_stdout_can_accompany_nonempty_execution_evidence(self):
        self.records(); (self.state / 'stdout.txt').write_text('')
        self.result['items'][0]['checks'][0]['evidence'].append('stdout.txt')
        self.assertEqual(self.grade()['status'], 'passed')

    def test_preserved_work_tests_and_scope_cannot_be_changed(self):
        self.records()
        for name in ('src/user-note.js', 'task.md', 'server.mjs'):
            path = self.source / name; original = path.read_bytes(); path.write_text('replaced')
            self.assertFalse(self.grade()['checks']['protected_work_preserved']); path.write_bytes(original)
        (self.source / 'outside.txt').write_text('unrequested')
        self.assertFalse(self.grade()['checks']['scope_preserved'])

    def test_original_test_prefix_may_be_extended_but_not_weakened(self):
        self.records(); path = self.source / 'tests/project-list.test.mjs'
        original = path.read_bytes()
        path.write_bytes(original + b'\n// Synthetic appended test.\n')
        self.assertTrue(self.grade()['checks']['original_tests_preserved'])
        path.write_bytes(original.replace(b'assert.equal', b'assert.notEqual'))
        self.assertFalse(self.grade()['checks']['original_tests_preserved'])

    def test_argv_alias_requires_real_argv_shape_and_consistency(self):
        self.records(); record = self.result['items'][0]['checks'][0]
        record['argv'] = record.pop('command')
        self.assertEqual(self.grade()['status'], 'passed')
        record['command'] = ['invented']; self.assertEqual(self.grade()['status'], 'failed')
        record.pop('command'); record['argv'] = 'node --test'
        self.assertEqual(self.grade()['status'], 'failed')

    def test_current_target_and_reset_observations_are_required(self):
        self.records()
        for name in ('source_digest', 'select_synchronized', 'selection_restored', 'responsive', 'design_matches'):
            original = self.observed[name]; self.observed[name] = False
            self.assertEqual(self.grade()['status'], 'failed'); self.observed[name] = original
        (self.source / 'src/app.js').write_text('changed after checks')
        self.assertFalse(self.grade()['checks']['current_files_accounted'])

    def test_cached_file_needs_its_real_hash_and_fresh_observation(self):
        self.records()
        name = 'tests/__pycache__/fixture.json'
        path = self.source / name; path.parent.mkdir(); path.write_text('{"answer":1}\n')
        expected = evaluation.hashes(self.source)
        expected[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.result['changed_files'][name] = expected[name]
        self.result['change_reasons'][name] = 'Synthetic fixture input'
        self.observed['source_digest'] = evaluation.gate.digest(expected)
        self.assertEqual(self.grade()['status'], 'passed')

        self.result['changed_files'][name] = None
        self.assertFalse(self.grade()['checks']['current_files_accounted'])
        path.write_text('{"answer":2}\n')
        self.result['changed_files'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        verdict = self.grade()
        self.assertTrue(verdict['checks']['current_files_accounted'])
        self.assertFalse(verdict['checks']['observations_current'])

    def test_cached_symlink_is_not_an_omitted_or_regular_output(self):
        self.records()
        name = 'tests/__pycache__/fixture.json'
        path = self.source / name; path.parent.mkdir(); path.symlink_to(self.source / 'task.md')
        self.refresh_changes(); self.result['changed_files'] = self.changes
        self.result['change_reasons'] = {p: 'Synthetic output' for p in self.changes}
        self.assertFalse(self.grade()['checks']['regular_outputs'])

    def test_initial_untracked_cached_user_work_remains_protected(self):
        self.records()
        original = evaluation.gate.git(self.source, 'show', 'HEAD:src/app.js')
        name = 'tests/__pycache__/user-draft.json'
        path = self.source / name; path.parent.mkdir()
        coordinator = self.output / 'coordinator'
        for staged in (False, True):
            with self.subTest(staged=staged):
                (self.source / 'src/app.js').write_text(original)
                path.write_text('Existing draft\n')
                if staged:
                    subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(self.source), 'add', '--', name], check=True)
                baseline = evaluation.gate.capture(self.source, coordinator / 'inputs.json')
                evaluation.write(coordinator / 'baseline.json', baseline)
                metadata = evaluation.gate.load(coordinator / 'case.json')
                metadata['before'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
                evaluation.write(coordinator / 'case.json', metadata)
                (self.source / 'src/app.js').write_text(original + '\n// Synthetic correction.\n')
                self.refresh_changes(); self.result['changed_files'] = self.changes
                self.result['change_reasons'] = {p: 'Synthetic correction' for p in self.changes}
                expected = evaluation.hashes(self.source); expected[name] = metadata['before'][name]
                self.observed['source_digest'] = evaluation.gate.digest(expected)
                self.assertEqual(self.grade()['status'], 'passed')
                path.write_text('Unauthorized replacement\n')
                verdict = self.grade()
                self.assertFalse(verdict['checks']['protected_work_preserved'])

    def test_ignored_files_added_outside_scope_are_still_rejected(self):
        self.records()
        path = self.source / 'node_modules/unrequested.txt'; path.parent.mkdir(); path.write_text('Unrequested file\n')
        self.assertFalse(self.grade()['checks']['scope_preserved'])

    def test_initial_head_and_instruction_changes_do_not_pass(self):
        self.records()
        import subprocess
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(self.source), 'commit', '--allow-empty', '-qm', 'unexpected'], check=True)
        self.assertFalse(self.grade()['checks']['head_preserved'])
        (self.output / 'fix/SKILL.md').write_text('replacement')
        self.assertFalse(self.grade()['checks']['instructions_preserved'])

    def test_bug_case_requires_pre_fix_regression_failure(self):
        self.records('bug'); self.observed['regression_failed_before'] = False
        self.assertFalse(self.grade()['checks']['independent_outcomes'])


if __name__ == '__main__':
    unittest.main()
