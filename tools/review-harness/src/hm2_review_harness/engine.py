"""Collect events, apply four review workflows, validate, then stage Pending drafts."""
import json
import os
from pathlib import Path
import time
import uuid
import subprocess
import hashlib

from . import __version__, agent, delivery, source
from .github import ApiError, GitHub, claims, fingerprint
from .state import HarnessError, Store, device, digest, save_json
from .trusted import module


class Engine:
    def __init__(self, config, root, *, github=None, reviewer=None):
        self.config = config; self.root = Path(root); self.store = Store(root)
        self.gh = github or GitHub(config, root); self.reviewer = reviewer or agent.run
        self.gate = module('review-code', 'review_result.py')
        self.contract = module('review-code', 'automation_contract.py')
        # Trusted helpers use these installed executables even under launchd.
        os.environ['PATH'] = os.pathsep.join(dict.fromkeys([
            str(Path(config['git_path']).parent), str(Path(config['gh_path']).parent), os.environ.get('PATH', '')]))

    def poll(self):
        login = self.gh.login(); self.store.wake_budget()
        self.store.prune(self.config.get('retention_days', 14), apply=True)
        if self.store.storage_bytes() < self.config.get('max_state_bytes', 2 * 1024 ** 3):
            with self.store.db:
                self.store.db.execute("UPDATE jobs SET status='queued' WHERE status='storage_limited'")
        tracked = self.store.tracked()
        for repository in self.config['repositories']:
            repo = repository['name']
            pulls = self.gh.pages(f'repos/{repo}/pulls?state=open', cached=True)
            enrolled = {row['pr'] for row in tracked if row.get('repo') == repo and row.get('state') == 'open'}
            selected = set(enrolled) | set(self.gh.reviewed(repo, login))
            for pr in pulls:
                own = pr['user']['login'].lower() == login.lower()
                requested = any(row['login'].lower() == login.lower() for row in pr.get('requested_reviewers', []))
                requested |= any(row['slug'] in repository.get('teams', []) for row in pr.get('requested_teams', []))
                if own or requested:
                    selected.add(pr['number'])
            for number in sorted(selected):
                self.enqueue_pr(repo, number)

    def enqueue_pr(self, repo, number, force=False):
        if repo not in [r['name'] for r in self.config['repositories']]:
            raise HarnessError('Repository is outside the registered scope')
        snapshot = self.gh.snapshot(repo, number); pr = snapshot['pr']; login = self.config['login']
        own_reviews = [r for r in snapshot['reviews'] if r['state'] != 'PENDING'
                       and (r.get('user') or {}).get('login', '').lower() == login.lower()]
        scenario = 'S2' if pr['user']['login'].lower() == login.lower() else ('S4' if own_reviews else 'S3')
        inputs = claims(snapshot, scenario, login)
        stamp = fingerprint(snapshot, login)
        requested = any(r['login'].lower() == login.lower() for r in pr.get('requested_reviewers', []))
        teams = next(r.get('teams', []) for r in self.config['repositories'] if r['name'] == repo)
        requested |= any(r['slug'] in teams for r in pr.get('requested_teams', []))
        watch_key = f'{self.config["hostname"]}/{repo}/{number}'
        previous = self.store.db.execute('SELECT data FROM watches WHERE id=?', (watch_key,)).fetchone()
        prior = json.loads(previous[0]) if previous else None
        event = {'hostname': self.config['hostname'], 'repo': repo, 'pr': number, 'fingerprint': stamp,
                 'source_fingerprint': fingerprint(snapshot), 'account': login, 'policy_version': __version__, 'claims': inputs}
        value = {'hostname': self.config['hostname'], 'repo': repo, 'pr': number, 'fingerprint': stamp,
                 'account': login, 'policy_version': __version__, 'state': pr['state'], 'requested': requested}
        active = pr['state'] == 'open' and not pr.get('draft') and (scenario != 'S2' or bool(inputs))
        changed = prior is None or prior['fingerprint'] != stamp or prior.get('policy_version') != __version__ or (requested and not prior.get('requested'))
        if force and active:
            event['manual_request'] = uuid.uuid4().hex
            self.store.observe(watch_key, value)
            return self.store.enqueue(scenario, event)
        return self.store.observe(watch_key, value, scenario if active and changed else None, event if active and changed else None)

    def notify_implementation(self, worktree, assessment, inputs=None):
        path = Path(worktree).resolve()
        repository = next((r for r in self.config['repositories'] if r.get('path') and Path(r['path']).resolve() == path), None)
        if repository is None:
            raise HarnessError('Implementation checkout is not registered')
        if assessment.get('status') != 'complete':
            raise HarnessError('Only an assessed implementation completion triggers S1')
        scope = self.gate.capture_scope(path, working_tree=True)
        context = None
        if inputs:
            context = {'requirements': inputs.get('requirements', []), 'checks': inputs.get('checks', []), 'sources': []}
            used = 0
            for row in inputs.get('sources', []):
                input_path = Path(row['path'])
                if not input_path.is_absolute():
                    input_path = path / input_path
                if input_path.is_symlink() or not input_path.is_file():
                    raise HarnessError('Implementation source is unavailable or symlinked')
                raw = input_path.read_bytes(); used += len(raw)
                if used > self.config['max_packet_bytes']:
                    raise HarnessError('Implementation requirements exceed the review packet limit')
                context['sources'].append({'id': row['id'], 'text': raw.decode(), 'sha256': hashlib.sha256(raw).hexdigest()})
        return self.store.enqueue('S1', {'hostname': self.config['hostname'], 'repo': repository['name'],
                                        'worktree': str(path), 'target': scope['target'],
                                        'account': self.config['login'], 'assessment': assessment,
                                        'implementation_context': context, 'policy_version': __version__, 'claims': []})

    def _assess(self, request, response, scope, packet):
        self.contract.validate(request, response)
        if scope['target']['mode'] == 'working-tree' and self.gate.capture_scope(scope['worktree'], working_tree=True) != scope:
            raise HarnessError('Review source changed during analysis')
        if scope['target']['mode'] == 'commits' and self.gate.capture_scope(
                scope['worktree'], scope['target']['base_sha'], scope['target']['head_sha']) != scope:
            raise HarnessError('Review source changed during analysis')
        code = None
        if response['review'] is not None:
            report = response['review']
            if packet['omitted']:
                report.setdefault('limitations', []).append('Source packet omitted: ' + ', '.join(packet['omitted']))
                report.setdefault('passes', {})['runtime'] = {'status': 'partial', 'note': 'Packet omissions leave source paths unverified.'}
            code = self.gate.assess(scope, report)
            if code['status'] == 'invalid':
                raise HarnessError('Model returned an invalid or stale code ledger')
        by_id = {row['id']: row for row in request['claims']}
        claim_gaps = []
        for row in response['claims']:
            claim = by_id[row['id']]
            for ref in row['evidence'] + row['counterevidence']:
                if ref.get('revision') == 'review':
                    old = claim.get('review_ref')
                    if not old:
                        raise HarnessError('Original review revision is unavailable')
                    old_scope = {**scope, 'target': {**scope['target'], 'base_sha': old}}
                    self.gate.check_evidence(old_scope, [{**ref, 'revision': 'base'}])
                else:
                    self.gate.check_evidence(scope, [ref])
            if row['verdict'] == 'unresolved':
                claim_gaps.append(row['id'] + ': ' + row['missing_evidence'])
            if (row['current_state'] == 'already_addressed' and row['verdict'] == 'confirmed'
                    and not any(r.get('revision') == 'review' for r in row['evidence'])):
                claim_gaps.append(row['id'] + ': original correctness not independently verified at its review revision')
                row['reply'] = None
        return {'code': code, 'claim_gaps': claim_gaps,
                'status': 'partial' if claim_gaps or packet['omitted'] or (code and code['status'] != 'complete') else 'complete'}

    def run_one(self):
        job = self.store.next()
        if job is None or self.config.get('paused'):
            return None
        key = job['id']; event = json.loads(job['event'])
        if event.get('account') != self.config['login']:
            self.store.update(key, 'auth_required', error='Queued work belongs to another account'); return key
        if self.store.storage_bytes() >= self.config.get('max_state_bytes', 2 * 1024 ** 3):
            self.store.update(key, 'storage_limited', error='Local state budget reached; prune old runs or raise the configured limit'); return key
        if self.store.daily_count() >= self.config['daily_runs']:
            self.store.update(key, 'budget_limited', error='Daily model-run limit reached; resumes on the next UTC day')
            return key
        run_dir = self.root / 'runs' / (time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + '-' + key[:10] + '-' + uuid.uuid4().hex[:8])
        run_dir.mkdir(parents=True, mode=0o700)
        self.store.update(key, 'collecting', run_dir=run_dir)
        snapshot = None
        try:
            prior = self.store.previous(event['hostname'], event['repo'], event.get('pr')) if event.get('pr') else None
            if job['scenario'] == 'S1':
                actual = self.gate.capture_scope(event['worktree'], working_tree=True)
                if actual['target'] != event['target']:
                    self.store.update(key, 'superseded', error='Implementation changed after completion notification'); return key
                self.store.update(key, 'snapshotting')
                checkout, scope = source.local_checkout(self.config, event['worktree'], run_dir / 'source', self.gate)
            else:
                self.gh.login(); snapshot = self.gh.snapshot(event['repo'], event['pr'])
                if fingerprint(snapshot) != event['source_fingerprint'] or snapshot['pr']['state'] != 'open':
                    self.store.update(key, 'superseded', error='PR or conversation changed while queued'); return key
                self.store.update(key, 'snapshotting')
                checkout = source.pr_checkout(self.config, event, snapshot, run_dir / 'source')
                scope = self.gate.capture_scope(checkout, snapshot['pr']['base']['sha'], snapshot['pr']['head']['sha'])
            previous_head = None
            if snapshot and job['scenario'] == 'S4':
                submitted = [r for r in snapshot['reviews'] if r['state'] != 'PENDING'
                             and (r.get('user') or {}).get('login', '').lower() == self.config['login'].lower()]
                previous_head = submitted[-1].get('commit_id') if submitted else None
            context = {'claims': event['claims'], 'implementation': event.get('implementation_context'),
                       'pull_request': {k: snapshot['pr'].get(k) for k in ('title', 'body', 'html_url')} if snapshot else None}
            remaining = self.config['max_packet_bytes'] - len(json.dumps(context, ensure_ascii=False).encode())
            if remaining < 1:
                raise HarnessError('Review context exceeds packet budget; narrow scope or raise the configured limit')
            packet = source.packet(checkout, scope, remaining, previous_head)
            packet['context'] = context
            for claim in event['claims']:
                if claim.get('review_ref') and claim.get('path'):
                    try:
                        value = source.git(checkout, 'show', claim['review_ref'] + ':' + claim['path']).decode()
                        if len(value.encode()) < self.config['max_packet_bytes'] // 10:
                            packet['sources']['review:' + claim['review_ref'] + ':' + claim['path']] = value
                    except (HarnessError, UnicodeError):
                        pass
            request = {'schema_version': 1, 'mode': 'draft-only', 'scenario': job['scenario'],
                       'target': scope['target'], 'claims': event['claims']}
            save_json(run_dir / 'request.json', request); save_json(run_dir / 'scope.json', scope)
            save_json(run_dir / 'source-packet.json', packet)
            self.store.update(key, 'reviewing'); self.store.record_model_call(key)
            agent_dir = run_dir / 'agent'; agent_dir.mkdir()
            response = self.reviewer(self.config, request, scope, packet, prior, agent_dir)
            save_json(run_dir / 'response.json', response)
            assessment = self._assess(request, response, scope, packet)
            save_json(run_dir / 'assessment.json', assessment)
            output = {'response': response, 'assessment': assessment, 'delivery': {'status': 'local_ready'}}
            if snapshot and fingerprint(self.gh.snapshot(event['repo'], event['pr'])) != event['source_fingerprint']:
                self.store.update(key, 'superseded', result=output, error='Source/conversation changed during review')
                self._report(run_dir, job, output)
                return key
            self._report(run_dir, job, output)
            # Preserve analysis even if remote delivery is blocked or uncertain.
            self.store.update(key, 'local_ready', result=output)
            if (snapshot and self.config['pending_enabled']
                    and self.config['active_device'] == device(self.root)):
                self.store.update(key, 'saving')
                output['delivery'] = delivery.save(self.config, self.gh, event, snapshot, scope, response,
                                                   assessment['code'], run_dir, self.root)
            status = output['delivery']['status']
            if assessment['status'] != 'complete' and status == 'local_ready':
                status = 'partial'
            self.store.update(key, status, result=output); self._report(run_dir, job, output)
        except delivery.DeliveryError as error:
            self._failure(job, run_dir, error.status, error)
        except ApiError as error:
            status = 'auth_required' if error.status == 401 else ('write_unconfirmed' if self._saving(key) else 'failed')
            self._failure(job, run_dir, status, error)
        except (RuntimeError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            self._failure(job, run_dir, 'write_unconfirmed' if self._saving(key) else 'partial', error)
        return key

    def _failure(self, job, run_dir, status, error):
        row = self.store.db.execute('SELECT result FROM jobs WHERE id=?', (job['id'],)).fetchone()
        output = json.loads(row[0]) if row[0] else None
        if output:
            output['delivery'] = {'status': status, 'error': str(error)}
            self._report(run_dir, job, output)
        else:
            (run_dir / 'report.md').write_text(f'# {job["scenario"]} review\n\nStatus: {status}\n\n{error}\n\nThis run did not establish complete review coverage.\n')
        self.store.update(job['id'], status, error=str(error), result=output)

    def _saving(self, key):
        return self.store.db.execute('SELECT status FROM jobs WHERE id=?', (key,)).fetchone()[0] == 'saving'

    def _report(self, directory, job, output):
        response = output['response']; assessment = output['assessment']
        lines = [f'# {job["scenario"]} review', '', f'Assessment: {assessment["status"]}',
                 f'Delivery: {output["delivery"]["status"]}', '', 'No review was submitted automatically.', '']
        if output['delivery'].get('error'):
            lines += [output['delivery']['error'], '']
        if output['delivery'].get('existing_concerns'):
            lines += ['Existing concerns retained in their original threads: ' + ', '.join(output['delivery']['existing_concerns']), '']
        if response['review']:
            for finding in response['review']['findings']:
                if finding.get('id') in assessment['code']['eligible_findings']:
                    lines += [f'## {finding.get("comment", finding["id"])}', f'{finding.get("path")}:{finding.get("line")}', '']
        for row in response['claims']:
            lines += [f'## {row["id"]}', f'{row["verdict"]} / {row["current_state"]} / {row["action"]}', '']
            if row.get('reply'):
                lines += [row['reply']['body'], '']
            if row.get('missing_evidence'):
                lines += [row['missing_evidence'], '']
        code_gaps = [str(gap) for gap in (assessment['code'] or {}).get('gaps', [])]
        lines += ['## Gaps', '', *assessment['claim_gaps'], *code_gaps,
                  *((response.get('review') or {}).get('limitations') or []), *(response.get('limitations') or [])]
        (directory / 'report.md').write_text('\n'.join(lines) + '\n')
