"""Original-document regressions. Synthetic records do not prove model behavior."""
import copy
import json
import shutil
import subprocess
import unittest
import test_implementation_state as legacy

gate = legacy.gate


def spec_text(ids=('AC-1', 'AC-2', 'AC-3')):
    return '''---
id: "spec:names"
revision: 1
handoff_version: 1
status: ready
questions: ./QUESTIONS.md
---
# Names
## 6. AC·검증 시나리오
### 6.1 AC 연결
| AC ID | 근거 | 사전 조건 | 행동 | 기대 관찰 결과 | 관련 화면·흐름·API | 확인 방법·미결 참조 |
| --- | --- | --- | --- | --- | --- | --- |
''' + ''.join(f'| {i} | request | loaded | select name | requested name visible | name UI, GET /name | actual name assertion |\n' for i in ids)


def questions(rows=''):
    return '''---
id: "questions:names"
revision: 1
handoff_version: 1
spec: ./SPEC.md
---
## 1. 질문 목록
| ID | 종류 | 질문 요약 | 영향 절·AC·범위 | 미해결 시 차단 | 상태 |
| --- | --- | --- | --- | --- | --- |
''' + rows + '\n## 2. 질문 상세\n'


class SourceCoverageTests(unittest.TestCase):
    git = legacy.ImplementationStateTests.git
    write = legacy.ImplementationStateTests.write
    capture_baseline = legacy.ImplementationStateTests.capture_baseline
    prepare_result = legacy.ImplementationStateTests.prepare_result
    assess = legacy.ImplementationStateTests.assess

    def setUp(self):
        legacy.ImplementationStateTests.setUp(self)
        self.spec = self.state / 'SPEC.md'
        self.q = self.state / 'QUESTIONS.md'
        self.spec.write_text(spec_text())
        self.q.write_text(questions())
        self.inputs['sources'] = [{'id': 'spec', 'path': str(self.spec)}, {'id': 'questions', 'path': str(self.q)}]
        original = self.inputs['requirements'][0]
        self.inputs['requirements'] = [{**copy.deepcopy(original), 'id': f'AC-{i}'} for i in (1, 2, 3)]
        self.refresh()

    def refresh(self):
        self.capture_baseline()
        self.prepare_result()
        original = self.report['requirements'][0]
        self.report['requirements'] = [{**copy.deepcopy(original), 'id': r['id']} for r in self.inputs['requirements']]
        originals = gate.handoff.read_spec(self.spec.read_bytes())['acs'] if 'handoff_version: 1' in self.spec.read_text() else []
        evidence = self.report['verification'][0]['evidence']
        self.report['source_review'] = [
            {'id': r['AC ID'], 'target': self.verified['digest'], 'ac_digest': gate.digest(r),
             'facets': {f: {'expected': r[c], 'verdict': 'matched', 'detail': 'Synthetic comparison of original to manifest/code'}
                        for f, c in {'condition': '사전 조건', 'action': '행동', 'outcome': '기대 관찰 결과',
                                     'interfaces': '관련 화면·흐름·API', 'verification': '확인 방법·미결 참조'}.items()},
             'behavior_checks': ['test', 'browser'], 'evidence': evidence}
            for r in originals if r['AC ID'] in {q['id'] for q in self.inputs['requirements']}]

    def test_all_original_acs_are_covered(self):
        self.assertEqual(self.assess()['status'], 'complete')

    def test_omitted_manifest_ac_cannot_complete(self):
        self.inputs['requirements'].pop()
        self.refresh()
        self.assertIn('missing_or_ambiguous_ac', str(self.assess()))

    def test_duplicate_mapping_is_rejected(self):
        self.inputs['requirements'].append({**self.inputs['requirements'][0], 'id': 'another', 'ac': 'AC-1'})
        self.refresh()
        self.assertNotEqual(self.assess()['status'], 'complete')

    def test_open_and_deferred_blockers_cannot_complete(self):
        for status in ('open', 'deferred'):
            with self.subTest(status=status):
                self.q.write_text(questions(f'| Q-1 | decision | policy | AC-3 | yes | {status} |\n'))
                self.refresh()
                self.assertIn('blocker_not_preserved', str(self.assess()))

    def test_active_question_is_retained_and_independent_work_continues(self):
        self.q.write_text(questions('| Q-1 | decision | policy | AC-3 | yes | deferred |\n'))
        self.refresh()
        self.report['requirements'][-1].update(state='needs_decision', questions=['Q-1'])
        verdict = self.assess()
        self.assertEqual(verdict['status'], 'partial')
        self.assertNotIn('blocker_not_preserved', str(verdict))
        self.assertEqual(self.report['requirements'][0]['state'], 'implemented')

    def test_resolved_and_nonblocking_questions_do_not_block(self):
        self.q.write_text(questions('| Q-1 | decision | policy | AC-3 | yes | resolved |\n| Q-2 | wording | wording | AC-1 | no | deferred |\n'))
        self.refresh()
        self.assertEqual(self.assess()['status'], 'complete')

    def test_section_only_blocker_impact_is_not_silently_ignored(self):
        self.q.write_text(questions('| Q-1 | decision | policy | section 4 | yes | open |\n'))
        self.refresh()
        self.assertNotEqual(self.assess()['status'], 'complete')

    def test_linked_questions_must_be_frozen(self):
        self.inputs['sources'].pop()
        self.refresh()
        self.assertIn('QUESTIONS companion', str(self.assess()))

    def test_original_change_invalidates_previous_review(self):
        self.spec.write_text(self.spec.read_text().replace('requested name visible', 'different name visible'))
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_question_change_invalidates_previous_review(self):
        self.q.write_text(questions('| Q-1 | decision | policy | AC-1 | yes | deferred |\n'))
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_format_errors_never_fall_back_to_direct_requirements(self):
        for old, new in [('handoff_version: 1', 'handoff_version: 9'), ('| AC ID |', '| Criteria |'),
                         ('### 6.1 AC 연결', '### 6.2 Other')]:
            with self.subTest(new=new):
                self.spec.write_text(spec_text().replace(old, new))
                self.capture_baseline(); self.prepare_result()
                self.assertNotEqual(self.assess()['status'], 'complete')

    def test_coverage_not_run_and_semantic_review_not_run_are_not_pass(self):
        self.report.pop('source_review')
        self.assertIn('missing_or_stale_semantic_review', str(self.assess()))

    def test_arbitrary_exclusion_reason_cannot_shrink_scope(self):
        self.inputs['requirements'][-1].update(disposition='excluded', reason='skip inconvenient AC')
        self.refresh()
        self.report['requirements'][-1].update(state='excluded')
        self.assertIn('unsupported_scope_exclusion', str(self.assess()))

    def test_source_backed_partial_scope_can_complete(self):
        authority = self.state / 'request.md'
        quote = 'Implement AC-1 and AC-2 now; exclude AC-3 from this delivery.'
        authority.write_text(quote)
        self.inputs['sources'].append({'id': 'request', 'path': str(authority), 'role': 'scope_authority'})
        self.inputs['requirements'][-1].update(disposition='excluded', reason='Explicit user scope',
                                               exclusion={'source': 'request', 'quote': quote})
        self.q.write_text(questions('| Q-1 | decision | policy | AC-3 | yes | deferred |\n'))
        self.refresh()
        self.report['requirements'][-1].update(state='excluded')
        self.assertEqual(self.assess()['status'], 'complete')

    def test_matching_ids_do_not_substitute_for_semantic_review(self):
        self.report['source_review'][0]['facets']['outcome'].update(verdict='mismatch', detail='Manifest reversed the expected name')
        self.assertIn('semantic_mismatch_or_unreviewed', str(self.assess()))

    def test_static_id_check_cannot_replace_behavior(self):
        self.report['source_review'][0]['behavior_checks'] = []
        self.assertIn('behavior_unverified', str(self.assess()))

    def test_failed_behavior_cannot_complete_even_when_all_ids_match(self):
        self.report['verification'][0].update(status='failed', reason='Expected requested, observed wrong')
        self.assertIn('behavior_unverified', str(self.assess()))

    @unittest.skipUnless(shutil.which('node'), 'Actual JavaScript behavior check needs Node')
    def test_actual_wrong_behavior_is_caught_with_all_ac_ids_present(self):
        (self.repo / 'src/app.js').write_text('export const name = "wrong";\n')
        self.refresh()
        command = ['node', '--input-type=module', '-e',
                   "import{readFileSync}from'node:fs';import assert from'node:assert/strict';"
                   "const {name}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('src/app.js','utf8')));"
                   "assert.equal(name,'requested');"]
        run = subprocess.run(command, cwd=self.repo, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('wrong', run.stderr)
        (self.state / 'actual-behavior.txt').write_text(run.stdout + run.stderr)
        self.report['verification'][0].update(status='failed', reason='Actual JS assertion disagrees with original requested outcome',
                                              command=command, cwd=str(self.repo), exit_code=run.returncode)
        self.assertEqual(self.assess()['status'], 'partial')

    def test_review_cannot_be_reused_after_recapture_with_new_ac_content(self):
        previous = copy.deepcopy(self.report['source_review'])
        self.spec.write_text(self.spec.read_text().replace('requested name visible', 'new name visible'))
        self.refresh()
        self.report['source_review'] = previous
        self.assertIn('missing_or_stale_semantic_review', str(self.assess()))

    def test_namespace_preserves_original_ac_id(self):
        self.inputs['requirements'][0]['id'] = 'spec:AC-1'
        self.refresh()
        row = self.verified['coverage']['handoffs'][0]['spec']['acs'][0]
        review = {'id': 'spec:AC-1', 'target': self.verified['digest'], 'ac_digest': gate.digest(row),
                  'facets': self.report['source_review'][0]['facets'],
                  'behavior_checks': ['test'], 'evidence': self.report['verification'][0]['evidence']}
        self.report['source_review'].insert(0, review)
        self.assertEqual(self.assess()['status'], 'complete')

    def malformed_result(self):
        # Unlike refresh(), this does not assume the original can be parsed.
        self.capture_baseline()
        self.prepare_result()
        row = self.report['requirements'][0]
        self.report['requirements'] = [{**copy.deepcopy(row), 'id': r['id']} for r in self.inputs['requirements']]

    def test_malformed_ac_cannot_disappear_with_omitted_manifest_row(self):
        self.spec.write_text(self.spec.read_text().replace('| AC-3 |', 'AC-3 |'))
        self.inputs['requirements'].pop()
        self.malformed_result()
        self.assertIn('unsupported_handoff', str(self.assess()))
        self.assertNotEqual(self.assess()['status'], 'complete')

    def test_malformed_active_question_does_not_disappear(self):
        self.q.write_text(questions('Q-1 | decision | policy | AC-3 | yes | deferred |\n'))
        self.malformed_result()
        self.assertNotEqual(self.assess()['status'], 'complete')
        self.assertTrue(self.verified['coverage']['errors'])

    def test_decode_failure_cannot_fall_back_with_omitted_ac(self):
        self.spec.write_bytes(self.spec.read_bytes() + b'\xff')
        self.inputs['requirements'].pop()
        self.malformed_result()
        self.assertTrue(self.verified['coverage']['errors'])
        self.assertNotEqual(self.assess()['status'], 'complete')

    def test_frozen_markdown_must_be_readable_even_without_detectable_id(self):
        self.spec.write_bytes(spec_text().encode('utf-16'))
        self.malformed_result()
        self.assertNotEqual(self.assess()['status'], 'complete')

    def test_fenced_handoff_example_does_not_block_direct_input(self):
        source = self.state / 'request.md'
        source.write_text('Render the requested name. Example only:\n```yaml\nid: spec:example\nhandoff_version: 1\n```\n')
        self.inputs['sources'] = [{'id': 'request', 'path': str(source)}]
        self.inputs['requirements'] = [{**self.inputs['requirements'][0], 'source': 'request'}]
        self.malformed_result()
        self.assertEqual(self.verified['coverage'], {'handoffs': [], 'errors': []})
        self.assertEqual(self.assess()['status'], 'complete')

    def test_binary_visual_input_remains_supported(self):
        image = self.state / 'reference.png'; image.write_bytes(b'\x89PNG\r\n\x1a\n\xff')
        self.inputs['sources'].append({'id': 'visual', 'path': str(image)})
        self.refresh()
        self.assertEqual(self.assess()['status'], 'complete')


if __name__ == '__main__':
    unittest.main()
