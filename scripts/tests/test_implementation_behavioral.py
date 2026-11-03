"""Grader-sensitivity tests with synthetic records; no model/browser claims."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from test_review_skill_install import broken_links

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('implementation_evaluation', ROOT / 'scripts/behavioral/implementation.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class ImplementationEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name).resolve() / 'case'
        self.metadata = evaluation.prepare(self.output, 'no-browser')
        self.source, self.state = [Path(self.metadata[k]) for k in ('source', 'state')]

    def records(self, *, changed=True, late_baseline=False, browser=False, mixed_browser=False):
        inputs = {'schema_version': 1, 'task': 'Synthetic grader test', 'surface': 'ui', 'scope': ['src', 'tests'],
                  'sources': [{'id': 'spec', 'path': 'spec.md'}],
                  'checks': [{'id': 'app', 'kind': 'browser', 'required': True, 'description': 'Actual UI outcome'}],
                  'requirements': [{'id': f'AC-{i}', 'source': 'spec', 'description': f'Outcome {i}',
                                    'disposition': 'required', 'checks': ['app']} for i in (1, 2, 3)]}
        if mixed_browser:
            inputs['checks'].append({'id':'optional-app','kind':'browser','required':False,'description':'Another browser scenario'})
        evaluation.write(self.state / 'inputs.json', inputs)
        before = evaluation.gate.capture(self.source, self.state / 'inputs.json')
        if changed:
            with (self.source / 'src/app.js').open('a') as stream: stream.write('\n// Synthetic mechanical-grader fixture change.\n')
        after = evaluation.gate.capture(self.source, self.state / 'inputs.json')
        baseline = after if late_baseline else before
        evaluation.write(self.state / 'target.json', baseline)
        evaluation.write(self.state / 'verification-target.json', after)
        check = {'id': 'app', 'status': 'not_run', 'detail': 'Browser unavailable', 'reason': 'This is a synthetic unit test'}
        passed = None
        if browser or mixed_browser:
            evidence = self.state / 'evidence.txt'; evidence.write_text('Synthetic mechanical test evidence only')
            passed={**check,'status':'passed','target':after['digest'],'tool':'synthetic','url':'http://127.0.0.1/',
                    'scenario':'Synthetic observation','viewport':{'width':1000,'height':700},
                    'evidence':[{'path':'evidence.txt','sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}]}
            if browser:check=passed
        report = {'schema_version': 1, 'target': after['digest'],
                  'changes': [] if not changed or late_baseline else [{'path': 'src/app.js', 'reason': 'Synthetic change'}],
                  'requirements': [{'id': f'AC-{i}', 'state': 'implemented', 'reason': 'Synthetic source evidence',
                                    'code': [{'path': 'src/app.js', 'line': 1, 'quote': "import { projects } from './api.js';"}]} for i in (1, 2, 3)],
                  'verification': [check]}
        if mixed_browser:report['verification'].append({**passed,'id':'optional-app'})
        evaluation.write(self.state / 'result.json', report)
        verdict = evaluation.gate.assess(self.source, self.state / 'target.json', self.state / 'verification-target.json', self.state / 'result.json')
        evaluation.write(self.state / 'assessment.json', verdict)
        return report, verdict

    def test_prepare_excludes_grading_inputs_and_keeps_user_draft(self):
        installed = Path(self.metadata['installed'])
        self.assertFalse((installed / 'evals').exists())
        self.assertEqual(broken_links(installed), [])
        self.assertIn('user-draft.md', self.metadata['before'])
        self.assertNotIn('expected_observations', (self.output / 'prompt.txt').read_text())

    def test_realistic_partial_record_is_accepted_only_as_partial_case(self):
        _, verdict = self.records()
        self.assertEqual(verdict['status'], 'partial')
        self.assertEqual(evaluation.grade(self.output,self.observations())['status'], 'passed')

    def observations(self):
        value={'all_ids':['tide','forest','north'],'active_ids':['tide','north'],'archived_ids':['forest'],
               'paused_ids':[],'displayed_counts':[3,2,1,0],'empty_state_visible':True,'selection_hidden':'Tide',
               'selected_after_return':'tide','error_distinct':True,'retry_status':'archived','latest_status':'archived',
               'wide_columns':2,'narrow_columns':1,
               'target':json.loads((self.state/'result.json').read_text())['target']}
        path=self.output/'synthetic-observations.json';evaluation.write(path,value)
        return path

    def test_unimplemented_requirements_do_not_pass_as_useful_partial(self):
        report,_=self.records()
        for row in report['requirements']:row.update(state='unimplemented',reason='Not implemented')
        evaluation.write(self.state/'result.json',report)
        evaluation.write(self.state/'assessment.json',evaluation.gate.assess(self.source,self.state/'target.json',self.state/'verification-target.json',self.state/'result.json'))
        value=evaluation.grade(self.output,self.observations())
        self.assertFalse(value['checks']['requirements_covered']);self.assertEqual(value['status'],'failed')

    def test_namespaced_source_anchors_preserve_required_ids(self):
        inputs={'requirements':[{'id':f'spec:AC-{i}','source':'spec','disposition':'required'} for i in (1,2,3)]}
        report={'requirements':[{'id':f'spec:AC-{i}','state':'implemented'} for i in (1,2,3)]}
        sources={'spec':{'path':str(self.source/'spec.md')}}
        self.assertTrue(evaluation.requirement_coverage(inputs,report,sources,self.source))
        report['requirements'].pop()
        self.assertFalse(evaluation.requirement_coverage(inputs,report,sources,self.source))

    def test_incorrect_count_or_absent_empty_message_fails(self):
        self.records();observations=self.observations()
        for key,value in [('displayed_counts',[3,3,3,3]),('empty_state_visible',False)]:
            original=json.loads(observations.read_text());changed={**original,key:value}
            evaluation.write(observations,changed)
            result=evaluation.grade(self.output,observations)
            self.assertFalse(result['checks']['independent_browser_observations'])
            evaluation.write(observations,original)

    def test_initial_head_and_outside_symlinks_are_accounted_for(self):
        self.records()
        import subprocess
        subprocess.run(['git','-c','core.hooksPath=/dev/null','-C',str(self.source),'commit','--allow-empty','-qm','unexpected commit'],check=True)
        (self.source/'src/app.js').write_bytes((evaluation.SKILL/'evals/files/feature-app/src/app.js').read_bytes())
        self.records()
        value=evaluation.grade(self.output,self.observations())
        self.assertFalse(value['checks']['no_commit_or_head_change'])
        (self.source/'outside-link').symlink_to(self.state,target_is_directory=True)
        value=evaluation.grade(self.output,self.observations())
        self.assertFalse(value['checks']['inputs_and_user_work_preserved'])

    def test_noop_and_late_baseline_cannot_pass(self):
        self.records(changed=False)
        value = evaluation.grade(self.output)
        self.assertFalse(value['checks']['implementation_changed'])
        self.assertEqual(value['status'], 'failed')
        self.records(late_baseline=True)
        value = evaluation.grade(self.output)
        self.assertFalse(value['checks']['baseline_predates_changes'])
        self.assertEqual(value['status'], 'failed')

    def test_fabricated_browser_success_fails_no_browser_case(self):
        self.records(browser=True)
        value = evaluation.grade(self.output)
        self.assertFalse(value['checks']['browser_limit_honest'])
        self.assertEqual(value['status'], 'failed')

    def test_one_skipped_browser_cannot_hide_another_claimed_browser_pass(self):
        self.records(mixed_browser=True)
        value=evaluation.grade(self.output,self.observations())
        self.assertFalse(value['checks']['browser_limit_honest'])
        self.assertEqual(value['status'],'failed')

    def test_user_draft_or_skill_tampering_fails(self):
        self.records()
        (self.source / 'user-draft.md').write_text('replaced')
        (Path(self.metadata['installed']) / 'SKILL.md').write_text('replaced')
        value = evaluation.grade(self.output)
        self.assertFalse(value['checks']['inputs_and_user_work_preserved'])
        self.assertFalse(value['checks']['instructions_unchanged'])
        self.assertEqual(value['status'], 'failed')

    def test_full_case_cannot_pass_without_independent_observations(self):
        self.metadata['case'] = 'full'; evaluation.write(self.output / 'case.json', self.metadata)
        self.records(browser=True)
        value = evaluation.grade(self.output)
        self.assertFalse(value['checks']['independent_browser_observations'])
        self.assertEqual(value['status'], 'failed')

    def test_cannot_prepare_inside_repository_or_overwrite_an_existing_case(self):
        with self.assertRaises(ValueError): evaluation.prepare(ROOT / 'forbidden-evaluation', 'full')
        with self.assertRaises(FileExistsError): evaluation.prepare(self.output, 'full')

    def test_standalone_skill_copy_has_no_outside_reference_links(self):
        installed = Path(self.temp.name) / 'installed/implement'
        shutil.copytree(evaluation.SKILL, installed)
        self.assertEqual(broken_links(installed), [])


if __name__ == '__main__':
    unittest.main()
