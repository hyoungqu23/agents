"""Explicit opt-in real CLI evaluation on synthetic data; never collected by unittest."""
import argparse
import json
from pathlib import Path
import shutil

from hm2_review_harness import agent, source
from hm2_review_harness.engine import Engine
from hm2_review_harness.state import save_json
from test_harness import GitFixture, FakeGitHub


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--provider', choices=('codex', 'claude'), default='codex')
    parser.add_argument('--scenarios', nargs='+', choices=('S1', 'S2', 'S3', 'S4'), default=['S1', 'S2', 'S3', 'S4'])
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for scenario in args.scenarios:
        fixture = GitFixture(); fixture.setUp()
        try:
            cfg = fixture.cfg; cfg['provider'] = args.provider; cfg['agent_path'] = shutil.which(args.provider); cfg['timeout_seconds'] = 240
            agent.probe(args.provider, cfg['agent_path'])
            directory = args.output / scenario; directory.mkdir()
            prior_head = fixture.head
            if scenario == 'S1':
                fixture.g('checkout', '-q', '--detach', fixture.base)
                (fixture.repo / 'app.py').write_text('def first(rows):\n    return rows[0]\n')
            if scenario == 'S4':
                (fixture.repo / 'app.py').write_text('def first(rows):\n    return rows[0] if rows else None\n')
                (fixture.repo / 'export.py').write_text('def export(rows):\n    return sorted(rows, reverse=True)\n')
                fixture.g('add', 'app.py', 'export.py'); fixture.g('commit', '-qm', 'handle empty input and change export')
                fixture.head = fixture.g('rev-parse', 'HEAD').strip()
            engine = Engine(cfg, directory / 'state', github=FakeGitHub(fixture.snapshot()))
            try:
                if scenario == 'S1':
                    checkout, scope = source.local_checkout(cfg, fixture.repo, directory / 'source', engine.gate)
                else:
                    checkout = fixture.repo; scope = engine.gate.capture_scope(checkout, fixture.base, fixture.head)
                packet = source.packet(checkout, scope, cfg['max_packet_bytes'], prior_head if scenario == 'S4' else None)
                packet['context'] = {'pull_request': {'title': 'Simplify first-row lookup', 'body': 'Keep first([]) returning None. Export must preserve oldest-first sorted order.'}}
                inputs = []
                if scenario in ('S2', 'S4'):
                    inputs.append({'id': 'inline:C1', 'source': 'inline', 'body': '[P2] Empty rows raise IndexError rather than returning None.',
                                   'review_ref': prior_head, 'path': 'app.py'})
                    packet['sources']['review:' + prior_head + ':app.py'] = source.git(checkout, 'show', prior_head + ':app.py').decode()
                if scenario == 'S2':
                    inputs.append({'id': 'conversation:2', 'source': 'conversation', 'body': '[질문] What ordering does export currently preserve?', 'review_ref': None})
                request = {'schema_version': 1, 'mode': 'draft-only', 'scenario': scenario, 'target': scope['target'], 'claims': inputs}
                save_json(directory / 'request.json', request); save_json(directory / 'scope.json', scope)
                save_json(directory / 'source-packet.json', packet)
                agent_dir = directory / 'agent'; agent_dir.mkdir()
                print(f'{scenario} started: {directory}', flush=True)
                response = agent.run(cfg, request, scope, packet, None, agent_dir)
                assessment = engine._assess(request, response, scope, packet)
                save_json(directory / 'assessment.json', assessment)
                if scenario == 'S2':
                    by_id = {row['id']: row for row in response['claims']}
                    first, question = by_id['inline:C1'], by_id['conversation:2']
                    assert first['current_state'] == 'present' and first['reply'] is None
                    assert question['action'] == 'answer' and question['reply']['label'] == '질문'
                else:
                    eligible = set(assessment['code']['eligible_findings'])
                    expected_path = 'export.py' if scenario == 'S4' else 'app.py'
                    assert any(f['id'] in eligible and f.get('path') == expected_path for f in response['review']['findings'])
                    if scenario == 'S4':
                        assert response['claims'][0]['current_state'] == 'already_addressed'
                        assert response['claims'][0]['verdict'] != 'refuted'
                results.append({'scenario': scenario, 'result': 'passed', 'computed_assessment': assessment['status']})
                save_json(args.output / 'summary.json', results)
                print(json.dumps(results[-1]), flush=True)
            finally:
                engine.store.close()
        finally:
            fixture.doCleanups()


if __name__ == '__main__': main()
