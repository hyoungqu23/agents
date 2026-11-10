"""Synthetic file/record regressions; no browser/defect-detection quality claims."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]
_module = importlib.util.spec_from_file_location('dogfood_result', ROOT / 'plugins/build/skills/dogfood/scripts/dogfood_result.py')
gate = importlib.util.module_from_spec(_module)
_module.loader.exec_module(gate)


def png(width=2, height=2):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\0' + b'\xff\xff\xff' * width) * height)) + chunk(b'IEND', b'')


class DogfoodResultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source, self.state = self.root / 'source', self.root / 'run'
        self.source.mkdir(); self.state.mkdir()
        (self.source / 'app.js').write_text('Source before QA')
        self.run_path = self.state / 'run.json'
        self.before, self.after = self.state / 'before.json', self.state / 'after.json'
        (self.state / 'screen.png').write_bytes(png())
        (self.state / 'trace.txt').write_text('Synthetic mechanical-test trace, not actual image inspection')
        self.entries = [{'path': f, 'sha256': hashlib.sha256((self.state / f).read_bytes()).hexdigest()} for f in ('screen.png', 'trace.txt')]
        self.run = {'schema_version': 1,
                    'target': {'url': 'http://127.0.0.1/', 'environment': 'fixture', 'role': 'anonymous',
                               'backend': 'fixture', 'served_build': 'test', 'local_root': str(self.source)},
                    'journeys': [{'id': 'J-1', 'goal': 'Inspect fixture'}],
                    'checks': [{'id': 'C-1', 'journey': 'J-1', 'required': True, 'axis': 'visual', 'purpose': 'Visibility',
                                'expectation': {'source': 'request', 'text': 'Readable content', 'certainty': 'confirmed'},
                                'status': 'passed', 'detail': 'Synthetic normal record', 'evidence': self.entries,
                                'visual': {'image': 'screen.png', 'inspected': True, 'inspection_trace': 'trace.txt',
                                           'pixels': [2, 2], 'css_viewport': [2, 2], 'dpr': 1, 'scale': 1,
                                           'capture': 'viewport', 'comparison_scope': 'Full synthetic fixture', 'observation': 'Synthetic image record'}}],
                    'issues': [], 'data_operations': []}
        self.recapture()

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def recapture(self):
        self.write(self.run_path, self.run)
        snapshot = gate.capture(self.run_path)
        self.write(self.before, snapshot); self.write(self.after, snapshot)
        for c in self.run['checks']:
            c['target'] = snapshot['digest']
        self.run['target_evidence'] = {'target': snapshot['digest'], 'evidence': [self.entries[1]]}
        for i in self.run['issues']:
            i['target'] = snapshot['digest']

    def assess(self):
        self.write(self.run_path, self.run)
        return gate.assess(self.run_path, self.before, self.after)

    def issue(self, classification='reproduced'):
        return {'id': 'I-1', 'check': 'C-1', 'target': self.run['checks'][0]['target'], 'expected': 'Readable',
                'actual': 'Clipped', 'steps': 'Open page with stated viewport/data', 'impact': 'Cannot read result',
                'attempts': 2, 'classification': classification, 'evidence': self.entries}

    def test_complete_and_no_issues_observed(self):
        self.assertEqual(self.assess()['status'], 'complete')
        self.assertEqual(self.assess()['product_result'], 'no_issues_observed')

    def test_complete_and_issues_found_are_independent(self):
        self.run['checks'][0]['status'] = 'failed'; self.run['issues'] = [self.issue()]
        value = self.assess()
        self.assertEqual((value['status'], value['product_result']), ('complete', 'issues_found'))

    def test_blocked_required_check_is_not_complete(self):
        self.run['checks'][0].update(status='blocked', reason='Image viewer unavailable')
        self.assertEqual(self.assess()['status'], 'blocked')

    def test_skip_requires_reason_and_remains_gap(self):
        self.run['checks'][0].update(status='skipped', reason='Tool unavailable')
        self.assertNotEqual(self.assess()['status'], 'complete')
        del self.run['checks'][0]['reason']
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_source_change_invalidates_record(self):
        (self.source / 'app.js').write_text('Source after QA')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_new_source_file_is_in_inventory(self):
        (self.source / 'new.js').write_text('new behavior')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_target_or_role_change_invalidates(self):
        self.run['target']['role'] = 'other-role'
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_required_scope_cannot_be_removed_or_weakened(self):
        self.run['checks'][0]['required'] = False
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_added_exploration_checks_are_allowed_after_recapture(self):
        self.run['checks'].append({**self.run['checks'][0], 'id': 'C-2', 'axis': 'functional'})
        self.write(self.run_path, self.run)
        target = gate.capture(self.run_path); self.write(self.after, target)
        for c in self.run['checks']:
            c['target'] = target['digest']
        self.run['target_evidence']['target'] = target['digest']
        self.assertEqual(self.assess()['status'], 'complete')

    def test_stale_evidence_not_retargeted_automatically(self):
        self.run['checks'][0]['target'] = 'old target'
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_missing_or_changed_image_fails(self):
        (self.state / 'screen.png').write_bytes(b'')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_visual_dom_only_cannot_pass(self):
        self.run['checks'][0].pop('visual')
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_wrong_capture_dimensions_fail(self):
        self.run['checks'][0]['visual']['pixels'] = [3, 2]
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_missing_image_inspection_trace_fails(self):
        self.run['checks'][0]['visual']['inspection_trace'] = 'not-captured.txt'
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_jpeg_host_capture_metadata_is_supported_without_conversion(self):
        header = b'\xff\xd8\xff\xc0' + struct.pack('>HBHHBBB', 11, 8, 4, 6, 1, 1, 0) + b'\xff\xd9'
        self.assertEqual(gate.image_dimensions(header), [6, 4])
        with self.assertRaises(gate.RecordError):
            gate.image_dimensions(header[:7])

    def test_evidence_path_escape_and_symlink_fail(self):
        self.run['checks'][0]['evidence'] = [{'path': '../source/app.js', 'sha256': 'wrong'}]
        self.assertEqual(self.assess()['status'], 'invalid')
        link = self.state / 'link.txt'; link.symlink_to(self.source / 'app.js')
        self.run['checks'][0]['evidence'] = [{'path': 'link.txt', 'sha256': 'wrong'}]
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_unknown_intent_is_not_no_issues_pass(self):
        self.run['checks'][0]['expectation']['certainty'] = 'needs_intent'
        self.recapture()
        value = self.assess()
        self.assertNotEqual(value['status'], 'complete')
        self.assertEqual(value['product_result'], 'undetermined')

    def test_observed_once_is_retained(self):
        self.run['checks'][0]['status'] = 'failed'; self.run['issues'] = [self.issue('observed_once')]
        self.assertEqual(self.assess()['product_result'], 'issues_found')

    def test_failed_check_without_observed_issue_is_invalid(self):
        self.run['checks'][0]['status'] = 'failed'
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_uncertain_write_and_pending_cleanup_are_gaps(self):
        self.run['data_operations'] = [{'id': 'D-1', 'created_ids': [], 'outcome': 'unknown', 'cleanup': 'pending', 'detail': 'Lost response; requery needed'}]
        self.assertEqual(self.assess()['status'], 'partial')
        self.run['data_operations'][0].update(outcome='confirmed', created_ids=['exact-id'], cleanup='done', evidence=[self.entries[1]])
        self.assertEqual(self.assess()['status'], 'complete')

    def test_mocked_or_unqueried_persistence_cannot_complete(self):
        self.run['checks'].append({**self.run['checks'][0], 'id': 'C-2', 'axis': 'persistence'})
        self.recapture()
        self.assertIn('real_persistence_unverified', str(self.assess()))
        self.run['checks'][1]['persistence'] = {'mode': 'real_api', 'requery_trace': 'trace.txt'}
        self.assertEqual(self.assess()['status'], 'complete')

    def test_unknown_served_build_cannot_confirm_a_revision(self):
        self.run['target'].update(desired_revision='specified-commit', served_build='unknown')
        self.recapture()
        self.assertIn('served_revision_unverified', str(self.assess()))

    def test_target_observation_is_required(self):
        self.run.pop('target_evidence')
        self.assertIn('target_unverified', str(self.assess()))

    def test_known_build_without_served_revision_cannot_confirm_requested_code(self):
        self.run['target'].update(desired_revision='commit:' + '1' * 40, served_build='commit:' + '2' * 40)
        self.recapture()
        self.assertIn('served_revision_unverified', str(self.assess()))
        self.assertNotEqual(self.assess()['status'], 'complete')

    def test_known_wrong_served_revision_invalidates_target(self):
        self.run['target'].update(desired_revision='1' * 40, served_revision='2' * 40, served_build='deployment-42')
        self.recapture()
        self.assertEqual(self.assess()['status'], 'invalid')

    def test_matching_revision_with_distinct_deployment_id_can_complete(self):
        revision = 'abcdef0123' * 4
        self.run['target'].update(desired_revision=' commit:' + revision.upper() + ' ', served_revision=revision, served_build='deployment-42')
        self.recapture()
        self.assertEqual(self.assess()['status'], 'complete')

    def test_unknown_served_revision_does_not_match_known_build_id(self):
        for served in ('unknown', 'commit:unknown'):
            with self.subTest(served=served):
                self.run['target'].update(desired_revision='1' * 40, served_revision=served, served_build='deployment-42')
                self.recapture()
                self.assertIn('served_revision_unverified', str(self.assess()))

    def test_passed_check_and_confirmed_failure_are_contradictory(self):
        for classification in ('reproduced', 'observed_once', 'intermittent'):
            with self.subTest(classification=classification):
                issue = self.issue(classification)
                issue['expected'] = self.run['checks'][0]['expectation']['text']
                self.run['issues'] = [issue]
                self.assertEqual(self.assess()['status'], 'invalid')

    def test_unverified_exploration_lead_does_not_turn_a_pass_into_failure(self):
        self.run['issues'] = [self.issue('unverified')]
        value = self.assess()
        self.assertEqual((value['status'], value['product_result']), ('complete', 'undetermined'))

    def test_empty_revision_after_prefix_normalization_is_invalid(self):
        for field in ('desired_revision', 'served_revision'):
            with self.subTest(field=field):
                run = copy.deepcopy(self.run)
                run['target'][field] = 'commit:   '
                self.write(self.run_path, run)
                with self.assertRaises(gate.RecordError):
                    gate.capture(self.run_path)


if __name__ == '__main__':
    unittest.main()
