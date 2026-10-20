"""Grader sensitivity checks; these are not real model evaluations."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from review_result_fixtures import finding_for, report_for

SCRIPT=Path(__file__).resolve().parents[1]/'behavioral/review_completion.py'
spec=importlib.util.spec_from_file_location('completion_eval',SCRIPT)
evaluation=importlib.util.module_from_spec(spec);spec.loader.exec_module(evaluation)


class CompletionGraderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)

    def fixture(self,case):
        source,_,base,head,_,_=evaluation.prepare(Path(self.temp.name)/case,case)
        scope=evaluation.gate.capture_scope(source,base,head)
        return scope,report_for(scope)

    def supported(self,scope,path='permissions.py',line=2):
        finding=finding_for(scope,path,line)
        finding.update(trigger='A viewer role calls the helper.',effect='A truthy string grants access.')
        return finding

    def test_missing_defect_fails_even_when_structural_result_is_complete(self):
        scope,report=self.fixture('defect');checks,verdict=evaluation.grade('defect',scope,report)
        self.assertEqual(verdict['status'],'complete');self.assertFalse(all(checks.values()))

    def test_known_defect_passes_with_correct_cause_and_effect(self):
        scope,report=self.fixture('defect');report['findings']=[self.supported(scope)]
        checks,_=evaluation.grade('defect',scope,report);self.assertTrue(all(checks.values()))

    def test_false_positive_fails_despite_real_quote_and_valid_schema(self):
        scope,report=self.fixture('clean');report['findings']=[self.supported(scope,'lookup.py',4)]
        checks,verdict=evaluation.grade('clean',scope,report)
        self.assertEqual(verdict['status'],'complete');self.assertFalse(checks['no_false_positive'])

    def test_clean_review_does_not_need_a_finding_quota(self):
        scope,report=self.fixture('clean');checks,_=evaluation.grade('clean',scope,report)
        self.assertTrue(all(checks.values()))

    def test_clean_fixture_preserves_non_string_inputs_as_well(self):
        scope,_=self.fixture('clean')
        # Execute only our literal synthetic fixture, never incoming PR source.
        source=Path(scope['worktree']);before={};after={}
        exec(evaluation.gate.git(source,'show',scope['target']['base_sha']+':permissions.py').decode(),before)
        exec((source/'permissions.py').read_text(),after)
        for value in ('admin','editor','viewer',None,[],{},0):
            self.assertEqual(after['can_edit'](value),before['can_edit'](value))

    def test_deferred_scope_cannot_be_claimed_complete(self):
        scope,report=self.fixture('partial');report['findings']=[self.supported(scope)]
        checks,_=evaluation.grade('partial',scope,report);self.assertFalse(checks['computed_completion'])
        for row in report['files']:
            if row['path']!='permissions.py':row.update(status='unreviewed',note='Deferred by user request.')
        checks,verdict=evaluation.grade('partial',scope,report)
        self.assertEqual(verdict['status'],'partial');self.assertTrue(all(checks.values()))

    def test_unchanged_source_and_instructions_are_required(self):
        scope,report=self.fixture('clean')
        checks,_=evaluation.grade('clean',scope,report,source_unchanged=False)
        self.assertFalse(all(checks.values()))
        checks,_=evaluation.grade('clean',scope,report,instructions_unchanged=False)
        self.assertFalse(all(checks.values()))


if __name__=='__main__':unittest.main()
