"""Local Git contract tests; synthetic evidence is not a browser/model run."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[2] / 'plugins/build/skills/implement/scripts/implementation_state.py'
spec = importlib.util.spec_from_file_location('implementation_state', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ImplementationStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo, self.state = self.root / 'app', self.root / 'state'
        self.repo.mkdir(); self.state.mkdir(); (self.repo / 'src').mkdir()
        self.env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture'); self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'src/app.js').write_text('export const name = "before";\n')
        (self.repo / '.gitignore').write_text('dist/\n')
        self.git('add', '.'); self.git('commit', '-qm', 'base')
        (self.state / 'spec.md').write_text('AC-1: Render the requested name.\n')
        self.inputs = {
            'schema_version': 1, 'task': 'Name screen', 'surface': 'ui', 'scope': ['src'],
            'sources': [{'id': 'spec', 'path': str(self.state / 'spec.md')}],
            'requirements': [{'id': 'AC-1', 'source': 'spec', 'description': 'Render name',
                              'disposition': 'required', 'checks': ['test', 'browser']}],
            'checks': [{'id': 'test', 'kind': 'command', 'required': True, 'description': 'Name behavior assertion'},
                       {'id': 'browser', 'kind': 'browser', 'required': True, 'description': 'Actual rendered name'}],
        }
        self.inputs_path = self.state / 'inputs.json'
        self.baseline_path, self.verified_path, self.result_path = [self.state / n for n in ('target.json', 'verification.json', 'result.json')]
        self.capture_baseline()
        (self.repo / 'src/app.js').write_text('export const name = "requested";\n')
        self.prepare_result()

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(self.repo), *args], env=self.env, text=True).strip()

    def write(self, path, value):
        path.write_text(json.dumps(value, indent=2) + '\n')

    def capture_baseline(self):
        self.write(self.inputs_path, self.inputs)
        self.baseline = gate.capture(self.repo, self.inputs_path)
        self.write(self.baseline_path, self.baseline)

    def prepare_result(self):
        self.verified = gate.capture(self.repo, self.inputs_path)
        self.write(self.verified_path, self.verified)
        evidence = self.state / 'evidence.txt'
        evidence.write_text('Synthetic mechanical-test evidence, not an actual command or browser run.\n')
        entry = {'path': 'evidence.txt', 'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()}
        self.report = {
            'schema_version': 1, 'target': self.verified['digest'],
            'changes': [{'path': p, 'reason': 'Requested implementation'} for p in sorted(
                set(self.baseline['files']) | set(self.verified['files'])) if self.baseline['files'].get(p) != self.verified['files'].get(p)],
            'requirements': [{'id': 'AC-1', 'state': 'implemented', 'reason': 'Code connected to requested behavior',
                              'code': [{'path': 'src/app.js', 'line': 1, 'quote': (self.repo / 'src/app.js').read_text().splitlines()[0]}]}],
            'verification': [
                {'id': 'test', 'status': 'passed', 'detail': 'Recorded assertion', 'target': self.verified['digest'],
                 'command': ['node', '--test'], 'cwd': str(self.repo), 'exit_code': 0, 'evidence': [entry]},
                {'id': 'browser', 'status': 'passed', 'detail': 'Recorded rendered result', 'target': self.verified['digest'],
                 'tool': 'synthetic test double', 'url': 'http://127.0.0.1:1234/', 'scenario': 'Name visible',
                 'viewport': {'width': 1024, 'height': 768}, 'evidence': [entry]},
            ],
        }
        self.write(self.result_path, self.report)

    def assess(self):
        self.write(self.result_path, self.report)
        return gate.assess(self.repo, self.baseline_path, self.verified_path, self.result_path)

    def test_implementation_changes_are_allowed_between_two_snapshots(self):
        self.assertNotEqual(self.baseline['digest'], self.verified['digest'])
        self.assertEqual(self.assess()['status'], 'complete')

    def test_current_source_drift_invalidates_verification(self):
        (self.repo / 'src/app.js').write_text('export const name = "after checks";\n')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_source_change_without_revision_change_invalidates_inputs(self):
        (self.state / 'spec.md').write_text('AC-1: Different outcome; revision unchanged.\n')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_cannot_weaken_checks_or_exclude_requirement_after_capture(self):
        for change in ('checks', 'scope'):
            with self.subTest(change=change):
                value = copy.deepcopy(self.inputs)
                if change == 'checks': value['checks'][0]['required'] = False
                else: value['requirements'][0].update(disposition='excluded', reason='Convenient omission')
                self.write(self.inputs_path, value)
                self.assertEqual(self.assess()['status'], 'invalid')
        self.write(self.inputs_path, self.inputs)

    def test_result_cannot_supply_complete_or_omit_real_changes(self):
        original = copy.deepcopy(self.report)
        for change in ({'status': 'complete'}, {'complete': True}, {'changes': []}, {'target': self.baseline['digest']}):
            self.report = {**original, **change}
            self.assertEqual(self.assess()['status'], 'invalid')

    def test_missing_requirement_or_check_remains_partial(self):
        for field in ('requirements', 'verification'):
            with self.subTest(field=field):
                original = self.report[field]; self.report[field] = []
                self.assertEqual(self.assess()['status'], 'partial')
                self.report[field] = original

    def test_browser_not_run_cannot_become_complete(self):
        browser = self.report['verification'][1]
        browser.update(status='not_run', reason='Browser unavailable')
        verdict = self.assess()
        self.assertEqual(verdict['status'], 'partial')
        self.assertTrue(any(g.get('check') == 'browser' for g in verdict['gaps']))

    def test_failed_and_inapplicable_required_checks_remain_partial(self):
        for status in ('failed', 'not_applicable'):
            self.report['verification'][0].update(status=status, reason='Specific unresolved behavior')
            self.assertEqual(self.assess()['status'], 'partial')

    def test_blocked_requires_no_deliverable_changes_and_unresolved_decisions(self):
        (self.repo / 'src/app.js').write_text('export const name = "before";\n')
        self.prepare_result()
        self.report['requirements'][0].update(state='needs_decision', reason='Name policy not chosen')
        for row in self.report['verification']: row.update(status='not_run', reason='Required policy missing')
        self.assertEqual(self.assess()['status'], 'blocked')
        (self.repo / 'src/other.js').write_text('export const independent = true;\n')
        self.prepare_result()
        self.report['requirements'][0].update(state='needs_decision', reason='Required policy missing')
        self.assertEqual(self.assess()['status'], 'partial')

    def test_duplicate_or_unknown_ids_are_invalid(self):
        original = copy.deepcopy(self.report)
        for field in ('requirements', 'verification'):
            self.report = copy.deepcopy(original)
            self.report[field].append(copy.deepcopy(self.report[field][0]))
            self.assertEqual(self.assess()['status'], 'invalid')
            self.report[field][-1]['id'] = 'invented'
            self.assertEqual(self.assess()['status'], 'invalid')

    def test_fabricated_code_quote_or_location_is_invalid(self):
        for change in ({'quote': 'invented'}, {'line': True}, {'line': 10}, {'path': '../outside'}, {'path': 'absent.js'}):
            location = self.report['requirements'][0]['code'][0]
            original = dict(location); location.update(change)
            self.assertEqual(self.assess()['status'], 'invalid')
            location.clear(); location.update(original)

    def test_changed_or_missing_evidence_and_stale_target_are_invalid(self):
        original = copy.deepcopy(self.report)
        for change in ({'sha256': '0' * 64}, {'path': 'missing.txt'}, {'path': '../inputs.json'}):
            self.report = copy.deepcopy(original)
            self.report['verification'][0]['evidence'][0].update(change)
            self.assertEqual(self.assess()['status'], 'invalid')
        self.report = copy.deepcopy(original)
        self.report['verification'][0]['target'] = self.baseline['digest']
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_command_and_browser_records_need_execution_conditions(self):
        original = copy.deepcopy(self.report)
        for index, field, value in [(0, 'exit_code', True), (0, 'command', 'node --test'),
                                    (0, 'cwd', ''), (1, 'scenario', ''), (1, 'viewport', {'width': True, 'height': 10})]:
            self.report = copy.deepcopy(original)
            self.report['verification'][index][field] = value
            self.assertEqual(self.assess()['status'], 'invalid')

    def test_changes_outside_declared_scope_are_invalid(self):
        (self.repo / 'unrelated.md').write_text('Unexpected work\n')
        self.prepare_result()
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_dirty_user_work_is_preserved_even_inside_change_scope(self):
        (self.repo / 'src/user.js').write_text('User draft\n')
        self.capture_baseline(); self.prepare_result()
        self.assertEqual(self.assess()['status'], 'complete')
        (self.repo / 'src/user.js').write_text('User draft replaced\n')
        self.prepare_result()
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_explicit_editable_dirty_and_preserve_paths(self):
        self.inputs['editable_dirty'] = ['src/app.js']
        self.capture_baseline()
        (self.repo / 'src/app.js').write_text('export const name = "edited current draft";\n')
        self.prepare_result()
        self.assertEqual(self.assess()['status'], 'complete')
        self.inputs['preserve'] = ['src']
        self.capture_baseline()
        (self.repo / 'src/app.js').write_text('export const name = "protected";\n')
        self.prepare_result()
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_staged_change_cannot_hide_behind_identical_working_bytes(self):
        (self.repo / 'src/app.js').write_text('export const staged = true;\n')
        self.git('add', 'src/app.js')
        (self.repo / 'src/app.js').write_text('export const name = "requested";\n')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_untracked_binary_and_executable_changes_invalidate_current_target(self):
        for change in ('binary', 'mode'):
            with self.subTest(change=change):
                if change == 'binary': (self.repo / 'src/asset.bin').write_bytes(b'\x00asset')
                else: (self.repo / 'src/app.js').chmod(0o755)
                self.assertEqual(self.assess()['status'], 'invalid')
                if change == 'binary': (self.repo / 'src/asset.bin').unlink()

    def test_evidence_symlink_does_not_read_outside_state_directory(self):
        (self.state / 'link').symlink_to(self.inputs_path)
        self.report['verification'][0]['evidence'][0]['path'] = 'link'
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_inventory_records_symlink_without_reading_its_destination(self):
        secret = self.root / 'private.txt'; secret.write_text('Do not read this destination')
        (self.repo / 'src/link').symlink_to(secret)
        value = gate.capture(self.repo, self.inputs_path)
        self.assertEqual(value['files']['src/link']['working']['kind'], 'symlink')
        self.assertNotIn('Do not read this destination', json.dumps(value))

    def test_relative_source_cannot_escape_or_follow_symlink(self):
        (self.repo / 'src/link').symlink_to(self.state / 'spec.md')
        for path in ('../state/spec.md', 'src/link'):
            self.inputs['sources'][0]['path'] = path
            self.write(self.inputs_path, self.inputs)
            with self.assertRaises(gate.StateError): gate.capture(self.repo, self.inputs_path)

    def test_ui_inputs_cannot_omit_actual_browser_check(self):
        self.inputs['checks'][1]['required'] = False
        with self.assertRaises(gate.StateError): gate.validate_inputs(self.inputs)

    def test_non_object_inputs_have_a_bounded_error(self):
        for value in (None, [], 'inputs'):
            with self.assertRaises(gate.StateError): gate.validate_inputs(value)

    def test_unsupported_os_reports_unavailable_capture(self):
        with patch.object(gate.os,'O_NOFOLLOW',None):
            with self.assertRaises(gate.StateError):gate.file_bytes(self.inputs_path)

    def test_ignored_source_cannot_supply_untracked_code_evidence(self):
        with (self.repo / '.gitignore').open('a') as stream: stream.write('src/ignored.js\n')
        self.git('add', '.gitignore'); self.git('commit', '-qm', 'ignore fixture')
        self.capture_baseline()
        path=self.repo/'src/ignored.js';path.write_text('export const contract = true;\ncorrect();\n')
        self.prepare_result()
        self.report['requirements'][0]['code']=[{'path':'src/ignored.js','line':1,'quote':'export const contract = true;'}]
        path.write_text('export const contract = true;\nbroken();\n')
        self.assertEqual(self.assess()['status'],'invalid')

    def test_external_source_parent_symlink_cannot_escape_input_root(self):
        outside=self.root/'elsewhere';outside.mkdir();(outside/'spec.md').write_text('Outside source')
        (self.state/'link').symlink_to(outside,target_is_directory=True)
        self.inputs['sources'][0]['path']=str(self.state/'link/spec.md')
        self.write(self.inputs_path,self.inputs)
        with self.assertRaises(gate.StateError):gate.capture(self.repo,self.inputs_path)
        self.inputs['sources'][0]['path']=str(outside/'spec.md')
        self.write(self.inputs_path,self.inputs)
        with self.assertRaises(gate.StateError):gate.capture(self.repo,self.inputs_path)
        self.inputs['source_roots']=[str(outside)]
        self.write(self.inputs_path,self.inputs)
        self.assertIn('spec',gate.capture(self.repo,self.inputs_path)['sources'])

    def test_caller_selected_state_root_alias_survives_recapture(self):
        alias=self.root/'state-alias';alias.symlink_to(self.state,target_is_directory=True)
        self.inputs_path=alias/'inputs.json'
        self.inputs['sources'][0]['path']=str(alias/'spec.md')
        self.capture_baseline();self.prepare_result()
        self.assertEqual(self.assess()['status'],'complete')

    def test_hidden_index_flags_cannot_hide_existing_user_changes(self):
        for option in ('assume-unchanged','skip-worktree'):
            with self.subTest(option=option):
                self.git('update-index','--'+option,'src/app.js')
                with self.assertRaises(gate.StateError):gate.capture(self.repo,self.inputs_path)
                self.git('update-index','--no-'+option,'src/app.js')

    def test_capture_does_not_execute_git_clean_or_process_filters(self):
        marker=self.state/'filter-ran'
        script=self.state/'clean.py'
        script.write_text(f'import pathlib,sys\npathlib.Path({str(marker)!r}).write_text("ran")\nsys.stdout.write(sys.stdin.read())\n')
        (self.repo/'.gitattributes').write_text('src/*.js filter=fixture\n')
        self.git('add','.gitattributes');self.git('commit','-qm','attributes')
        self.git('config','filter.fixture.clean',f'{sys.executable} {script}')
        self.git('config','filter.fixture.process',f'{sys.executable} {script}')
        (self.repo/'src/app.js').write_text('export const name = "manual";\n')
        captured=gate.capture(self.repo,self.inputs_path)
        self.assertIn('src/app.js',captured['dirty'])
        self.assertFalse(marker.exists())

    def test_partial_clone_cannot_lazy_fetch_through_uploadpack(self):
        self.git('config','uploadpack.allowFilter','true')
        clone=self.root/'partial'
        subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','-q','--no-checkout','--filter=tree:0',self.repo.as_uri(),str(clone)],
                       env=self.env,check=True,capture_output=True)
        marker=self.state/'uploadpack-ran';script=self.state/'uploadpack.py'
        script.write_text(f'import pathlib\npathlib.Path({str(marker)!r}).write_text("ran")\nraise SystemExit(1)\n')
        subprocess.run(['git','-C',str(clone),'config','remote.origin.uploadpack',f'{sys.executable} {script}'],env=self.env,check=True)
        with patch.dict(os.environ,{'GIT_NO_LAZY_FETCH':'0'}):
            with self.assertRaises(gate.StateError):gate.capture(clone,self.inputs_path)
        self.assertFalse(marker.exists())

    def test_snapshot_digest_tampering_is_invalid(self):
        self.baseline['dirty'] = ['invented']; self.write(self.baseline_path, self.baseline)
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_digest_valid_but_malformed_snapshot_returns_invalid(self):
        for field,value in [('files',[]),('files',{'src/app.js':None}),('dirty',{}),('inputs',[]),('sources',[])]:
            malformed=copy.deepcopy(self.baseline);malformed[field]=value
            malformed['digest']=gate.digest({k:v for k,v in malformed.items() if k!='digest'})
            self.write(self.baseline_path,malformed)
            self.assertEqual(self.assess()['status'],'invalid')
        self.write(self.baseline_path,self.baseline)

    def test_normalized_scope_paths_have_consistent_semantics(self):
        self.inputs['scope']=['./src/']
        (self.repo/'src/app.js').write_text('export const name = "before";\n')
        self.capture_baseline()
        (self.repo/'src/app.js').write_text('export const name = "normalized scope";\n')
        self.prepare_result()
        self.assertEqual(self.assess()['status'],'complete')

    def test_head_change_is_not_silently_adopted(self):
        self.git('add', '.'); self.git('commit', '-qm', 'new head')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_capture_cli_outputs_new_state_only_outside_checkout(self):
        def invoke(path):
            return subprocess.run([sys.executable, str(SCRIPT), 'capture', '--worktree', str(self.repo),
                                   '--inputs', str(self.inputs_path), '--output', str(path)], text=True, capture_output=True)
        self.assertNotEqual(invoke(self.repo / 'target.json').returncode, 0)
        self.assertFalse((self.repo / 'target.json').exists())
        output = self.state / 'fresh.json'
        self.assertEqual(invoke(output).returncode, 0)
        before = output.read_bytes()
        self.assertNotEqual(invoke(output).returncode, 0)
        self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
