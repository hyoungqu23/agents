"""Real local Git tests for completion/evidence checks; no model or network calls."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from review_result_fixtures import SCRIPT, finding_for, gate, report_for


class ReviewResultTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull}
        self.g('init','-q','-b','main');self.g('config','user.name','Fixture');self.g('config','user.email','fixture@example.invalid')
        (self.repo/'app.py').write_text('def first(rows):\n    return rows[0] if rows else None\n')
        (self.repo/'guard.py').write_text('def allowed(role):\n    return role in ("admin", "editor")\n')
        self.g('add','.');self.g('commit','-qm','base');self.base=self.g('rev-parse','HEAD').strip()
        (self.repo/'app.py').write_text('def first(rows):\n    return rows[0]\n')
        (self.repo/'notes.md').write_text('The empty-input contract still applies.\n')
        self.g('add','.');self.g('commit','-qm','head');self.head=self.g('rev-parse','HEAD').strip()
        self.scope=gate.capture_scope(self.repo,self.base,self.head)
        self.report=report_for(self.scope)
        self.report['findings']=[finding_for(self.scope,'app.py',2)]

    def g(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],env=self.env,text=True)

    def assess(self):return gate.assess(self.scope,self.report)

    def test_complete_result_records_valid_supported_finding(self):
        result=self.assess();self.assertEqual(result['status'],'complete')
        self.assertEqual(result['eligible_findings'],['empty-input'])

    def test_missing_file_is_partial_even_with_correct_finding(self):
        self.report['files']=self.report['files'][:1]
        result=self.assess();self.assertEqual(result['status'],'partial')
        self.assertEqual(result['eligible_findings'],['empty-input'])

    def test_unreviewed_finding_is_not_eligible(self):
        self.report['files'][0]['status']='unreviewed'
        result=self.assess();self.assertEqual(result['status'],'partial');self.assertEqual(result['eligible_findings'],[])

    def test_stale_target_invalidates_all_findings(self):
        for field in ('head_sha','base_sha','diff_sha256','mode'):
            with self.subTest(field=field):
                report=copy.deepcopy(self.report);report['target'][field]='stale'
                result=gate.assess(self.scope,report)
                self.assertEqual(result['status'],'invalid');self.assertEqual(result['eligible_findings'],[])

    def test_model_cannot_supply_its_own_complete_status(self):
        self.report['status']='complete';self.assertEqual(self.assess()['status'],'invalid')

    def test_incomplete_pass_and_quality_remain_partial(self):
        for section,key in [('passes','runtime'),('quality','duplication')]:
            report=copy.deepcopy(self.report);del report[section][key]
            self.assertEqual(gate.assess(self.scope,report)['status'],'partial')

    def test_unavailable_spec_is_disclosed(self):
        self.report['passes']['spec']={'status':'unavailable','note':'No specification was supplied.'}
        result=self.assess();self.assertEqual(result['status'],'complete')
        self.assertEqual(result['spec_conformance'],'unverified')

    def test_high_risk_trace_must_be_accounted_for(self):
        self.report['files'][0]['risk']='high';self.assertEqual(self.assess()['eligible_findings'],[])
        self.report['files'][0]['trace']='Caller input -> rows[0] -> IndexError; no guard.'
        self.assertEqual(self.assess()['status'],'complete')
        self.report['files'][0]['status']='unresolved';self.assertEqual(self.assess()['status'],'partial')

    def test_unresolved_and_disproved_candidates_are_not_promoted(self):
        self.report['findings']=[{'id':'claim','status':'disproved','reason':'Guard rejects the input before indexing.'}]
        self.assertEqual(self.assess()['status'],'complete');self.assertEqual(self.assess()['eligible_findings'],[])
        self.report['findings'][0]['status']='unresolved';self.assertEqual(self.assess()['status'],'partial')

    def test_fabricated_quote_wrong_revision_and_anchor_are_rejected(self):
        for changes in ({'quote':'return fabricated()'},{'revision':'base'},{'line':True},{'line':200},{'path':'../secret'}):
            with self.subTest(changes=changes):
                report=copy.deepcopy(self.report);report['findings'][0]['evidence'][0].update(changes)
                result=gate.assess(self.scope,report);self.assertEqual(result['eligible_findings'],[])

    def test_anchor_needs_its_own_quote_even_when_other_evidence_matches(self):
        self.report['findings'][0]['line']=1
        self.assertEqual(self.assess()['eligible_findings'],[])

    def test_duplicate_finding_id_cannot_select_one_favorable_record(self):
        self.report['findings'].append({'id':'empty-input','status':'unresolved','reason':'Missing contract'})
        result=self.assess();self.assertEqual(result['eligible_findings'],[]);self.assertEqual(result['status'],'partial')

    def test_boolean_lines_and_empty_refutation_are_rejected(self):
        for changes in ({'line':True},{'refutation':''},{'severity':'P0'}):
            report=copy.deepcopy(self.report);report['findings'][0].update(changes)
            self.assertEqual(gate.assess(self.scope,report)['eligible_findings'],[])

    def test_skipped_execution_needs_reason_and_residual_risk(self):
        self.report['verification']=[{'kind':'command','status':'not_run','detail':'pytest'}]
        self.assertEqual(self.assess()['status'],'partial')
        self.report['verification'][0].update(reason='Target code execution was not authorized.',risk='Runtime behavior remains unverified.')
        self.assertEqual(self.assess()['status'],'complete')

    def test_renamed_and_deleted_files_cannot_disappear_from_inventory(self):
        self.g('mv','guard.py','access.py');self.g('rm','notes.md');self.g('commit','-qm','rename and delete')
        scope=gate.capture_scope(self.repo,self.head,'HEAD')
        rows={row['path']:row for row in scope['files']}
        self.assertEqual(rows['access.py']['old_path'],'guard.py');self.assertEqual(rows['notes.md']['change'],'D')
        report=report_for(scope);report['files']=[row for row in report['files'] if row['path']!='notes.md']
        self.assertEqual(gate.assess(scope,report)['status'],'partial')

    def test_staged_unstaged_and_untracked_are_all_in_scope(self):
        (self.repo/'app.py').write_text('staged\n');self.g('add','app.py')
        (self.repo/'guard.py').write_text('unstaged\n');(self.repo/'extra.py').write_text('untracked\n')
        scope=gate.capture_scope(self.repo,working_tree=True)
        self.assertEqual({row['path'] for row in scope['files']},{'app.py','guard.py','extra.py'})
        report=report_for(scope);report['files']=[row for row in report['files'] if row['path']!='extra.py']
        self.assertEqual(gate.assess(scope,report)['status'],'partial')

    def test_canceling_staged_and_unstaged_changes_remain_in_scope(self):
        original=(self.repo/'app.py').read_bytes()
        (self.repo/'app.py').write_text('staged\n');self.g('add','app.py');(self.repo/'app.py').write_bytes(original)
        self.assertEqual(self.g('diff','HEAD','--','app.py'),'')
        scope=gate.capture_scope(self.repo,working_tree=True)
        self.assertIn('app.py',[row['path'] for row in scope['files']])

    def test_untracked_and_binary_byte_changes_invalidate_fingerprint(self):
        for name in ('extra.py','asset.bin'):
            path=self.repo/name;path.write_bytes(b'\x00one')
            before=gate.capture_scope(self.repo,working_tree=True)
            path.write_bytes(b'\x00two')
            after=gate.capture_scope(self.repo,working_tree=True)
            self.assertNotEqual(before['target']['diff_sha256'],after['target']['diff_sha256'])

    def test_staged_binary_change_invalidates_identical_working_copy(self):
        file=self.repo/'asset.bin';file.write_bytes(b'\x00base');self.g('add','.');self.g('commit','-qm','binary base')
        file.write_bytes(b'\x00staged-one');self.g('add','asset.bin');file.write_bytes(b'\x00base')
        before=gate.capture_scope(self.repo,working_tree=True)
        file.write_bytes(b'\x00staged-two');self.g('add','asset.bin');file.write_bytes(b'\x00base')
        after=gate.capture_scope(self.repo,working_tree=True)
        self.assertNotEqual(before['target'],after['target'])

    def test_untracked_executable_bit_and_symlink_type_change_target(self):
        path=self.repo/'script';path.write_text('tool');path.chmod(0o644)
        before=gate.capture_scope(self.repo,working_tree=True)
        path.chmod(0o755);after=gate.capture_scope(self.repo,working_tree=True)
        self.assertNotEqual(before['target'],after['target'])
        path.unlink();path.symlink_to('tool')
        linked=gate.capture_scope(self.repo,working_tree=True)
        path.unlink();path.write_text('tool')
        regular=gate.capture_scope(self.repo,working_tree=True)
        self.assertNotEqual(linked['target'],regular['target'])

    def test_gitlink_change_cannot_be_hidden_by_local_diff_config(self):
        self.g('update-index','--add','--cacheinfo','160000',self.base,'vendor')
        self.g('commit','-qm','submodule base');base=self.g('rev-parse','HEAD').strip()
        self.g('update-index','--cacheinfo','160000',self.head,'vendor')
        self.g('commit','-qm','submodule change');self.g('config','diff.ignoreSubmodules','all')
        self.g('worktree','add','-q','--detach',str(self.repo/'vendor'),self.head)
        # The nested checkout matches the gitlink; its committed pointer still changed.
        scope=gate.capture_scope(self.repo,base,'HEAD')
        self.assertEqual([row['path'] for row in scope['files']],['vendor'])
        report=report_for(scope);report['files']=[]
        self.assertEqual(gate.assess(scope,report)['status'],'partial')

    def test_duplicate_file_cannot_hide_an_unreviewed_disposition(self):
        self.report['files'].append({**self.report['files'][0],'status':'unreviewed'})
        self.assertEqual(self.assess()['eligible_findings'],[])

    def test_committed_review_rejects_dirty_or_different_checkout(self):
        (self.repo/'app.py').write_text('local work\n')
        with self.assertRaises(gate.ResultError):gate.capture_scope(self.repo,self.base,self.head)
        with self.assertRaises(gate.ResultError):gate.capture_scope(self.repo,self.base,self.base)

    def test_working_evidence_does_not_follow_external_symlink(self):
        external=self.root/'private';external.write_text('private secret\n')
        (self.repo/'link').symlink_to(external)
        scope=gate.capture_scope(self.repo,working_tree=True)
        lines=gate.source_lines(scope,{'path':'link','revision':'working'})
        self.assertEqual(lines,[str(external)]);self.assertNotIn('private secret',''.join(lines))

    def test_cli_outputs_partial_and_never_writes_inside_source(self):
        report=self.root/'report.json';self.report['files']=[];report.write_text(json.dumps(self.report))
        args=[sys.executable,str(SCRIPT),'validate','--worktree',str(self.repo),'--base',self.base,'--head',self.head,'--result',str(report)]
        run=subprocess.run(args,env=self.env,text=True,capture_output=True)
        self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['status'],'partial')
        run=subprocess.run([*args,'--output',str(self.repo/'assessment.json')],env=self.env,text=True,capture_output=True)
        self.assertEqual(run.returncode,1);self.assertFalse((self.repo/'assessment.json').exists())

    def test_source_changed_after_capture_invalidates_saved_result(self):
        (self.repo/'app.py').write_text('new code\n');self.g('commit','-qam','new head')
        current=gate.capture_scope(self.repo,self.base,'HEAD')
        self.assertEqual(gate.assess(current,self.report)['status'],'invalid')


if __name__=='__main__':unittest.main()
