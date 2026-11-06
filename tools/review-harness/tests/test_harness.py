"""Real Git/SQLite integration with model/API doubles; no model calls or GitHub writes."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from hm2_review_harness import agent, delivery, source
from hm2_review_harness.cli import export, import_config
from hm2_review_harness.engine import Engine
from hm2_review_harness.github import ApiError, claims, fingerprint
from hm2_review_harness.state import HarnessError, Store, defaults, device, digest, instance_lock, read_json, save_json
from hm2_review_harness.trusted import module


def config():
    return {**defaults(), 'login': 'me', 'git_path': shutil.which('git'), 'gh_path': shutil.which('gh') or '/usr/bin/true',
            'agent_path': '/usr/bin/true', 'repositories': [{'name': 'example/app', 'teams': ['developers']}]}


def ledger(scope, path=None, line=2):
    gate = module('review-code', 'review_result.py')
    result = {'schema_version': 1, 'comment_policy': 'hm2-five', 'target': scope['target'],
              'files': [{'path': f['path'], 'classification': 'source', 'risk': 'medium', 'status': 'reviewed',
                         'note': 'Examined empty input and existing export order against the base.'} for f in scope['files']],
              'passes': {name: {'status': 'complete', 'note': 'Static synthetic contract comparison.'} for name in ('standards', 'spec', 'runtime')},
              'quality': {name: {'status': 'not_applicable', 'note': 'Single behavior in this synthetic fixture.'} for name in gate.QUALITY},
              'verification': [{'kind': 'static', 'status': 'passed', 'detail': 'Compared base/head guards and export ordering.'}],
              'findings': [], 'limitations': []}
    if path:
        revision = 'working' if scope['target']['mode'] == 'working-tree' else 'head'
        quote = gate.source_lines(scope, {'path': path, 'revision': revision})[line - 1]
        result['findings'] = [{'id': 'empty-input', 'status': 'supported', 'severity': 'P2', 'path': path, 'line': line,
                               'revision': revision, 'trigger': 'rows is empty', 'effect': 'IndexError replaces None',
                               'fix': 'Keep the empty-input guard', 'refutation': 'The base explicitly accepts empty rows.',
                               'evidence': [{'path': path, 'line': line, 'revision': revision, 'quote': quote}],
                               'comment': '[P2] 빈 배열에서 예외가 발생합니다. 기존 빈 입력 처리를 유지해 주세요.'}]
    return result


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.repo = self.root / 'app'; self.repo.mkdir()
        self.cfg = config(); self.cfg['repositories'][0]['path'] = str(self.repo)
        self.g('init', '-q', '-b', 'main'); self.g('config', 'user.name', 'Fixture'); self.g('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'app.py').write_text('def first(rows):\n    return rows[0] if rows else None\n')
        (self.repo / 'export.py').write_text('def export(rows):\n    return sorted(rows)\n')
        self.g('add', 'app.py', 'export.py'); self.g('commit', '-qm', 'base'); self.base = self.g('rev-parse', 'HEAD').strip()
        (self.repo / 'app.py').write_text('def first(rows):\n    return rows[0]\n')
        self.g('add', 'app.py'); self.g('commit', '-qm', 'remove guard'); self.head = self.g('rev-parse', 'HEAD').strip()
        self.g('checkout', '-q', '--detach')

    def g(self, *args):
        return source.git(self.repo, *args).decode()

    def snapshot(self, own=False, reviewed=False):
        return {'pr': {'number': 7, 'state': 'open', 'draft': False, 'title': 'Simplify lookup', 'body': 'Keep empty input behavior.',
                       'user': {'login': 'me' if own else 'teammate'}, 'head': {'sha': self.head},
                       'base': {'sha': self.base, 'repo': {'full_name': 'example/app'}},
                       'requested_reviewers': [{'login': 'me'}], 'requested_teams': []},
                'threads': [], 'reviews': [{'id': 1, 'state': 'COMMENTED', 'body': '', 'user': {'login': 'me'}, 'commit_id': self.head}] if reviewed else [],
                'conversation': []}


class SourceTests(GitFixture):
    def test_snapshot_preserves_cancelling_index_and_untracked_symlink(self):
        original = (self.repo / 'app.py').read_bytes()
        (self.repo / 'app.py').write_text('staged-only\n'); self.g('add', 'app.py'); (self.repo / 'app.py').write_bytes(original)
        (self.repo / 'new.py').write_text('print("untracked")\n'); (self.repo / 'new.py').chmod(0o755)
        (self.repo / 'outside').symlink_to('/nonexistent/private-data')
        gate = module('review-code', 'review_result.py'); before = gate.capture_scope(self.repo, working_tree=True)
        checkout, copied = source.local_checkout(self.cfg, self.repo, self.root / 'snapshot', gate)
        self.assertEqual(before['target'], copied['target']); self.assertEqual(before, gate.capture_scope(self.repo, working_tree=True))
        self.assertTrue((checkout / 'outside').is_symlink()); self.assertEqual((checkout / 'new.py').stat().st_mode & 0o111, 0o111)

    def test_packet_omission_is_explicit_and_source_hook_never_runs(self):
        marker = self.root / 'hook-ran'
        hook = self.repo / '.git/hooks/post-checkout'; hook.parent.mkdir(exist_ok=True)
        hook.write_text('#!/bin/sh\ntouch ' + str(marker)); hook.chmod(0o755)
        gate = module('review-code', 'review_result.py')
        checkout, scope = source.local_checkout(self.cfg, self.repo, self.root / 'snapshot', gate)
        packet = source.packet(checkout, scope, 1)
        self.assertTrue(packet['omitted']); self.assertFalse(marker.exists())


class FakeGitHub:
    def __init__(self, snapshot):
        self.value = copy.deepcopy(snapshot); self.writes = []; self.review = None; self.lose_reply = False

    def login(self): return 'me'
    def pages(self, *_args, **_kwargs): return [copy.deepcopy(self.value['pr'])]
    def reviewed(self, *_): return [7] if any((r.get('user') or {}).get('login') == 'me' and r['state'] != 'PENDING' for r in self.value['reviews']) else []
    def snapshot(self, *_args): return copy.deepcopy(self.value)

    def api(self, endpoint, payload=None):
        if payload is None:
            return copy.deepcopy(self.review)
        self.writes.append((endpoint, copy.deepcopy(payload)))
        if endpoint.endswith('/reviews'):
            self.review = {'id': 91, 'node_id': 'R91', 'state': 'PENDING', 'commit_id': self.value['pr']['head']['sha'],
                           'body': '', 'user': {'login': 'me'}, 'html_url': 'https://example.invalid/review/91'}
            self.value['reviews'].append(self.review)
            return copy.deepcopy(self.review)
        self.assert_reply(payload)
        comment = {'id': 'C91', 'databaseId': 91, 'body': payload['variables']['input']['body'], 'author': {'login': 'me'},
                   'pullRequestReview': {'databaseId': 91, 'state': 'PENDING'}}
        self.value['threads'][0]['comments'].append(comment)
        if self.lose_reply:
            self.lose_reply = False; raise ApiError('Response was lost after reply creation')
        return {'data': {'addPullRequestReviewThreadReply': {'comment': comment}}}

    def assert_reply(self, payload):
        if 'addPullRequestReviewThreadReply' not in payload['query'] or set(payload['variables']['input']) != {'pullRequestReviewId', 'pullRequestReviewThreadId', 'body'}:
            raise AssertionError('Unexpected remote mutation')


def add_thread(snapshot, author='teammate'):
    snapshot['threads'] = [{'id': 'T1', 'path': 'app.py', 'line': 2, 'originalLine': 2, 'isResolved': False, 'isOutdated': False,
                            'comments': [{'id': 'C1', 'body': 'Empty rows fail.', 'author': {'login': author},
                                          'commit': {'oid': snapshot['pr']['head']['sha']},
                                          'pullRequestReview': {'databaseId': 1, 'state': 'COMMENTED'}}]}]


class EngineTests(GitFixture):
    def reviewer(self, _config, request, scope, _packet, _prior, _directory):
        rows = []
        for claim in request['claims']:
            rows.append({'id': claim['id'], 'verdict': 'confirmed', 'current_state': 'present', 'action': 'fix',
                         'evidence': [{'path': 'app.py', 'revision': 'head', 'line': 2, 'quote': '    return rows[0]'}],
                         'counterevidence': [], 'missing_evidence': None, 'reply': None})
        return {'schema_version': 1, 'scenario': request['scenario'], 'target': request['target'],
                'review': None if request['scenario'] == 'S2' else ledger(scope, 'app.py'), 'claims': rows, 'limitations': []}

    def test_s1_runs_after_completion_and_preserves_original_checkout(self):
        self.g('checkout', '-q', '--detach', self.base)
        (self.repo / 'app.py').write_text('def first(rows):\n    return rows[0]\n')
        (self.repo / 'new.py').write_text('untracked = True\n')
        engine = Engine(self.cfg, self.root / 'state', reviewer=self.reviewer)
        self.addCleanup(engine.store.close)
        before = engine.gate.capture_scope(self.repo, working_tree=True)
        key = engine.notify_implementation(self.repo, {'status': 'complete'})
        engine.run_one(); row = engine.store.rows()[0]
        self.assertEqual(key, row['id']); self.assertEqual(row['status'], 'local_ready')
        self.assertEqual(before, engine.gate.capture_scope(self.repo, working_tree=True))
        self.assertTrue((Path(row['run_dir']) / 'report.md').is_file())

    def test_s2_s3_s4_route_and_run_with_source_validation(self):
        for scenario in ('S2', 'S3', 'S4'):
            with self.subTest(scenario=scenario):
                snapshot = self.snapshot(own=scenario == 'S2', reviewed=scenario == 'S4')
                if scenario in ('S2', 'S4'): add_thread(snapshot, 'me' if scenario == 'S4' else 'teammate')
                gh = FakeGitHub(snapshot); engine = Engine(self.cfg, self.root / scenario, github=gh, reviewer=self.reviewer)
                try:
                    key = engine.enqueue_pr('example/app', 7)
                    self.assertEqual(engine.store.next()['scenario'], scenario)
                    with patch('hm2_review_harness.source.pr_checkout', return_value=self.repo): engine.run_one()
                    self.assertEqual(engine.store.rows()[0]['status'], 'local_ready')
                    self.assertEqual(engine.store.rows()[0]['id'], key)
                    self.assertIsNone(engine.enqueue_pr('example/app', 7)); self.assertFalse(gh.writes)
                finally: engine.store.close()

    def test_same_head_comment_edit_supersedes_queued_input(self):
        snapshot = self.snapshot(own=True); add_thread(snapshot)
        gh = FakeGitHub(snapshot); engine = Engine(self.cfg, self.root / 'state', github=gh, reviewer=self.reviewer)
        self.addCleanup(engine.store.close); engine.enqueue_pr('example/app', 7)
        gh.value['threads'][0]['comments'][0]['body'] += ' New condition.'
        engine.run_one(); self.assertEqual(engine.store.rows()[0]['status'], 'superseded')

    def test_own_submission_does_not_loop_but_author_reply_triggers_recheck(self):
        gh = FakeGitHub(self.snapshot()); engine = Engine(self.cfg, self.root / 'state', github=gh, reviewer=self.reviewer)
        self.addCleanup(engine.store.close)
        engine.poll()
        with patch('hm2_review_harness.source.pr_checkout', return_value=self.repo): engine.run_one()
        gh.value['reviews'].append({'id': 1, 'state': 'COMMENTED', 'body': '[P2] Empty rows fail.', 'user': {'login': 'me'}, 'commit_id': self.head})
        gh.value['pr']['requested_reviewers'] = []; add_thread(gh.value, 'me')
        engine.poll(); self.assertIsNone(engine.store.next())
        gh.value['threads'][0]['comments'].append({'id': 'author-reply', 'body': 'I updated this.', 'author': {'login': 'teammate'}, 'pullRequestReview': None})
        engine.poll(); self.assertEqual(engine.store.next()['scenario'], 'S4')

    def test_old_manually_reviewed_pr_is_discovered_without_new_request(self):
        snapshot = self.snapshot(reviewed=True); snapshot['pr']['requested_reviewers'] = []
        engine = Engine(self.cfg, self.root / 'state', github=FakeGitHub(snapshot), reviewer=self.reviewer)
        self.addCleanup(engine.store.close); engine.poll()
        self.assertEqual(engine.store.next()['scenario'], 'S4')

    def test_implementation_requirements_are_captured_as_review_input(self):
        document = self.root / 'spec.md'; document.write_text('first([]) returns None.\n')
        engine = Engine(self.cfg, self.root / 'state', reviewer=self.reviewer); self.addCleanup(engine.store.close)
        engine.notify_implementation(self.repo, {'status': 'complete'}, {'requirements': [{'id': 'AC1'}], 'sources': [{'id': 'spec', 'path': str(document)}]})
        event = json.loads(engine.store.next()['event'])
        self.assertEqual(event['implementation_context']['sources'][0]['text'], document.read_text())

    def test_relative_implementation_sources_resolve_against_worktree(self):
        (self.repo / 'spec.md').write_text('first([]) returns None.\n')
        engine = Engine(self.cfg, self.root / 'state', reviewer=self.reviewer); self.addCleanup(engine.store.close)
        args = (self.repo, {'status': 'complete'}, {'sources': [{'id': 'spec', 'path': 'spec.md'}]})
        first = engine.notify_implementation(*args); second = engine.notify_implementation(*args)
        self.assertEqual(first, second); self.assertEqual(len(engine.store.rows()), 1)

    def test_s4_retains_review_body_and_conversation_findings(self):
        snapshot = self.snapshot(reviewed=True)
        snapshot['reviews'][0]['body'] = '[P2] Empty input must still return None.'
        snapshot['conversation'] = [{'id': 2, 'body': '[질문] Is export still oldest first?', 'user': {'login': 'me'}}]
        rows = claims(snapshot, 'S4', 'me')
        self.assertEqual({row['id'] for row in rows}, {'review_body:1', 'conversation:2'})
        self.assertEqual(rows[0]['review_ref'], self.head)

    def test_packet_limit_cannot_produce_complete_review(self):
        self.cfg['max_packet_bytes'] = 1
        engine = Engine(self.cfg, self.root / 'state', reviewer=self.reviewer); self.addCleanup(engine.store.close)
        engine.notify_implementation(self.repo, {'status': 'complete'}); engine.run_one()
        self.assertEqual(engine.store.rows()[0]['status'], 'partial')


class StateTests(unittest.TestCase):
    def test_pruning_keeps_uncertain_writes_receipts_and_open_pr_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); store = Store(root)
            keys = []
            for number, status in [(1, 'pending_saved'), (2, 'write_unconfirmed'), (3, 'pending_saved')]:
                key = store.enqueue('S3', {'repo': 'example/app', 'pr': number})
                path = root / 'runs' / str(number); path.mkdir(parents=True); (path / 'report.md').write_text('Evidence')
                store.update(key, status, run_dir=path); keys.append(key)
                store.observe(str(number), {'repo': 'example/app', 'pr': number, 'state': 'open' if number == 3 else 'closed'})
            with store.db: store.db.execute('UPDATE jobs SET updated=?', (time.time() - 30 * 86400,))
            save_json(root / 'receipts/keep/code.json', {'status': 'unconfirmed'})
            self.assertEqual(store.prune(14), [str(root / 'runs/1')]); self.assertTrue((root / 'runs/1').exists())
            store.prune(14, apply=True)
            self.assertFalse((root / 'runs/1').exists()); self.assertTrue((root / 'runs/2').exists()); self.assertTrue((root / 'runs/3').exists())
            self.assertTrue((root / 'receipts/keep/code.json').exists()); store.close()

    def test_queue_deduplication_survives_restart_and_incomplete_writes_do_not_replay(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root); key = store.enqueue('S3', {'pr': 7}); store.update(key, 'saving'); store.close()
            store = Store(root)
            self.assertEqual(store.enqueue('S3', {'pr': 7}), key); store.recover()
            self.assertEqual(store.rows()[0]['status'], 'write_unconfirmed'); self.assertIsNone(store.next()); store.close()

    def test_second_local_service_cannot_take_lock(self):
        with tempfile.TemporaryDirectory() as root, instance_lock(root):
            with self.assertRaises(HarnessError):
                with instance_lock(root): pass

    def test_export_import_excludes_auth_paths_and_defaults_to_paused_nonwriter(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root); original, target = root / 'original', root / 'target'
            cfg = config(); cfg['repositories'][0]['path'] = '/private/old-machine/app'; cfg['pending_enabled'] = True
            save_json(original / 'config.json', cfg)
            export(original, root / 'settings.json', False)
            raw = (root / 'settings.json').read_text(); self.assertNotIn('/private/old-machine', raw); self.assertNotIn('agent_path', raw)
            import_config(target, root / 'settings.json'); imported = read_json(target / 'config.json')
            self.assertTrue(imported['paused']); self.assertFalse(imported['pending_enabled']); self.assertEqual(imported['login'], '')


class DeliveryTests(GitFixture):
    def helper(self, gh):
        class Helper:
            def own_pending(self, *_): return gh.review['id'] if gh.review else None
            def read_review(self, *_): return copy.deepcopy(gh.review), []
        return Helper()

    def response(self, snapshot):
        inputs = claims(snapshot, 'S2', 'me')
        result = {'review': None, 'claims': [{'id': inputs[0]['id'], 'reply': {'label': '질문', 'body': '[질문] 빈 입력은 어떤 계약을 따르나요?'}}]}
        event = {'hostname': 'github.com', 'repo': 'example/app', 'pr': 7, 'claims': inputs}
        return event, result

    def test_only_pending_reply_mutations_and_lost_response_reconciles(self):
        snapshot = self.snapshot(own=True); add_thread(snapshot); gh = FakeGitHub(snapshot)
        event, response = self.response(snapshot); gh.lose_reply = True
        with patch('hm2_review_harness.delivery.module', return_value=self.helper(gh)):
            with self.assertRaises(ApiError):
                delivery.save(self.cfg, gh, event, snapshot, {}, response, None, self.root, self.root / 'state')
            saved = delivery.save(self.cfg, gh, event, snapshot, {}, response, None, self.root, self.root / 'state')
        self.assertEqual(saved['status'], 'pending_saved'); self.assertEqual(len(gh.writes), 2)
        self.assertNotIn('event', gh.writes[0][1]); self.assertEqual(gh.writes[0][1]['commit_id'], self.head)

    def test_existing_manual_pending_is_preserved(self):
        snapshot = self.snapshot(own=True); add_thread(snapshot); gh = FakeGitHub(snapshot)
        gh.review = {'id': 90}; event, response = self.response(snapshot)
        with patch('hm2_review_harness.delivery.module', return_value=self.helper(gh)), self.assertRaises(delivery.DeliveryError):
            delivery.save(self.cfg, gh, event, snapshot, {}, response, None, self.root, self.root / 'state')
        self.assertEqual(gh.writes, [])

    def test_regenerated_reply_wording_never_creates_a_second_draft(self):
        snapshot = self.snapshot(own=True); add_thread(snapshot); gh = FakeGitHub(snapshot)
        event, response = self.response(snapshot)
        with patch('hm2_review_harness.delivery.module', return_value=self.helper(gh)):
            delivery.save(self.cfg, gh, event, snapshot, {}, response, None, self.root, self.root / 'state')
            response['claims'][0]['reply']['body'] = '[질문] 빈 입력 계약을 알려주시겠어요?'
            with self.assertRaises(delivery.DeliveryError):
                delivery.save(self.cfg, gh, event, snapshot, {}, response, None, self.root, self.root / 'state')
        self.assertEqual(len(gh.writes), 2)

    def test_published_finding_is_not_reposted_when_claim_inventory_is_empty(self):
        snapshot = self.snapshot(reviewed=True); gh = FakeGitHub(snapshot)
        gh.review = {'id': 90, 'state': 'COMMENTED'}
        event = {'hostname': 'github.com', 'repo': 'example/app', 'pr': 7, 'claims': []}
        state = self.root / 'state'
        identity = {'host': 'github.com', 'repo': 'example/app', 'pr': 7, 'login': 'me'}
        save_json(state / 'receipts' / digest(identity) / 'code.json', {'review_id': 90, 'managed': {'old-find': {}}})
        report = {'findings': [{'id': 'old-find', 'path': 'app.py', 'line': 2, 'comment': '[P2] Empty rows fail.'}]}
        helper = SimpleNamespace(own_pending=lambda *_: None,
                                 capture=lambda *_: {'base_sha': self.base, 'head_sha': self.head},
                                 changed_lines=lambda *_: {'app.py': {2}}, diff_for=lambda *_: '')
        with patch('hm2_review_harness.delivery.module', return_value=helper):
            result = delivery.save(self.cfg, gh, event, snapshot, {'worktree': str(self.repo)},
                                   {'review': report, 'claims': []}, {'eligible_findings': ['old-find']}, self.root, state)
        self.assertEqual(result['existing_concerns'], ['old-find']); self.assertEqual(gh.writes, [])

    def test_own_pending_does_not_retrigger_review(self):
        snapshot = self.snapshot(); add_thread(snapshot); before = fingerprint(snapshot)
        snapshot['threads'][0]['comments'].append({'id': 'draft', 'body': 'Draft', 'author': {'login': 'me'}, 'pullRequestReview': {'state': 'PENDING'}})
        snapshot['reviews'].append({'state': 'PENDING', 'body': 'Draft'})
        self.assertEqual(fingerprint(snapshot), before)


class AdapterTests(unittest.TestCase):
    def test_codex_command_disables_commands_hooks_plugins_connectors_and_images(self):
        argv = agent.command(config(), Path('/tmp/controlled-run'))
        for feature in agent.CODEX_FEATURES:
            self.assertIn(feature, argv)
        self.assertIn('read-only', argv); self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', argv)


if __name__ == '__main__': unittest.main()
