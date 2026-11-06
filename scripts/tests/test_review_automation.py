"""Draft-only contracts and source-backed five-prefix ledger behavior."""
import copy
import importlib.util
from pathlib import Path
import unittest

import test_review_result as review_tests

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('automation', ROOT / 'plugins/review/skills/review-code/scripts/automation_contract.py')
automation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(automation)


class CommentPolicyTests(unittest.TestCase):
    setUp = review_tests.ReviewResultTests.setUp
    g = review_tests.ReviewResultTests.g
    assess = review_tests.ReviewResultTests.assess

    def test_p999_is_optional_and_requires_opt_in(self):
        row = self.report['findings'][0]
        row.update(severity='P999', comment='[P999] Prefer the existing local naming style.')
        self.assertEqual(self.assess()['eligible_findings'], [])
        self.report['comment_policy'] = 'hm2-five'
        self.assertEqual(self.assess()['eligible_findings'], ['empty-input'])

    def test_question_has_evidence_and_no_severity(self):
        self.report['comment_policy'] = 'hm2-five'
        row = self.report['findings'][0]
        row.update(kind='question', severity=None, question='Does empty input remain supported?',
                   why='The current implementation removes its guard.', comment='[질문] Is empty input still supported?')
        self.assertEqual(self.assess()['eligible_findings'], ['empty-input'])
        row['severity'] = 'P2'
        self.assertEqual(self.assess()['eligible_findings'], [])

    def test_wrong_prefix_or_missing_question_fact_prevents_delivery(self):
        self.report['comment_policy'] = 'hm2-five'
        row = self.report['findings'][0]
        row['comment'] = '[P0] Empty rows fail.'
        self.assertEqual(self.assess()['eligible_findings'], [])
        row.update(kind='question', severity=None, comment='[질문] Is this intended?')
        self.assertEqual(self.assess()['eligible_findings'], [])


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.request = {'schema_version': 1, 'mode': 'draft-only', 'scenario': 'S2',
                        'target': {'head_sha': 'a' * 40}, 'claims': [{'id': 'c1', 'body': 'Empty input fails.'}]}
        self.result = {'schema_version': 1, 'scenario': 'S2', 'target': self.request['target'],
                       'review': None, 'limitations': [], 'claims': [{
                           'id': 'c1', 'verdict': 'confirmed', 'current_state': 'present', 'action': 'fix',
                           'evidence': [{'path': 'app.py', 'line': 2, 'revision': 'head', 'quote': 'return rows[0]'}],
                           'counterevidence': [], 'missing_evidence': None, 'reply': None}]}

    def test_claim_only_run_does_not_require_whole_code_review(self):
        self.assertIs(automation.validate(self.request, self.result), self.result)

    def test_omitted_duplicate_and_unknown_claims_are_rejected(self):
        for rows in ([], self.result['claims'] * 2, [dict(self.result['claims'][0], id='other')]):
            result = copy.deepcopy(self.result); result['claims'] = rows
            with self.assertRaises(automation.ContractError):
                automation.validate(self.request, result)

    def test_stale_target_and_wrong_scenario_are_rejected(self):
        for change in ({'target': {'head_sha': 'b' * 40}}, {'scenario': 'S4'}):
            with self.assertRaises(automation.ContractError):
                automation.validate(self.request, {**self.result, **change})

    def test_unimplemented_fix_cannot_claim_completion(self):
        row = self.result['claims'][0]; row['reply'] = {'label': 'P2', 'body': '[P2] Fixed.'}
        with self.assertRaises(automation.ContractError):
            automation.validate(self.request, self.result)
        row.update(current_state='already_addressed', action='already-addressed')
        automation.validate(self.request, self.result)

    def test_unresolved_claim_needs_missing_fact_and_only_question_reply(self):
        row = self.result['claims'][0]; row.update(verdict='unresolved', current_state='unknown', action='defer', evidence=[])
        with self.assertRaises(automation.ContractError):
            automation.validate(self.request, self.result)
        row['missing_evidence'] = 'The matching server schema is unavailable.'
        row['reply'] = {'label': '질문', 'body': '[질문] Which server schema defines empty input?'}
        automation.validate(self.request, self.result)
        row['reply'] = {'label': 'P999', 'body': '[P999] Maybe empty input is unsafe.'}
        with self.assertRaises(automation.ContractError):
            automation.validate(self.request, self.result)

    def test_every_code_scenario_requires_matching_ledger(self):
        for scenario in ('S1', 'S3', 'S4'):
            request = {**self.request, 'scenario': scenario}
            result = {**self.result, 'scenario': scenario}
            with self.assertRaises(automation.ContractError):
                automation.validate(request, result)
            result['review'] = {'target': request['target'], 'comment_policy': 'hm2-five'}
            automation.validate(request, result)

    def test_answer_cannot_assign_severity_to_question(self):
        row = self.result['claims'][0]
        row.update(action='answer', reply={'label': 'P1', 'body': '[P1] Why was this changed?'})
        with self.assertRaises(automation.ContractError):
            automation.validate(self.request, self.result)
        row['reply'] = {'label': '질문', 'body': '[질문] Empty input is supported by the documented contract.'}
        automation.validate(self.request, self.result)

    def test_state_invariant_applies_without_a_reply(self):
        self.result['claims'][0]['action'] = 'already-addressed'
        with self.assertRaises(automation.ContractError):
            automation.validate(self.request, self.result)


if __name__ == '__main__':
    unittest.main()
