"""Opt-in real-model continuation test using local Git and a gh double only.

Run from any directory: python3 forward_test.py --host codex|claude --output /tmp/new-run
Requires explicit permission for model-service calls; never calls live GitHub.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('fixtures', REPO/'scripts/tests/test_pending_review.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}


def loaded_review_code(events, host):
    """Inspect successful tool calls, not mentions in generated prose."""
    if host == 'codex':
        return any(e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution'
                   and e['item'].get('exit_code') == 0 and 'review-code/SKILL.md' in e['item'].get('command', '')
                   for e in events)
    calls = set()
    for event in events:
        message = event.get('message')
        if not isinstance(message, dict):
            continue
        content = message.get('content', [])
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get('type') == 'tool_use':
                value = block.get('input', {})
                if ('review-code/SKILL.md' in value.get('command', '') or
                        'review-code/SKILL.md' in value.get('file_path', '') or
                        value.get('skill') in ('review:review-code', 'review-code')):
                    calls.add(block['id'])
            elif block.get('type') == 'tool_result' and block.get('tool_use_id') in calls and not block.get('is_error'):
                return True
    return False


def main(host, output):
    output.mkdir(parents=True, exist_ok=False)
    fixture = fixtures.PendingReviewTests()
    fixture.setUp()
    fixture.temp._finalizer.detach()  # Retain raw fixtures/traces for inspection.
    seed, checkout = fixture.seed, fixture.worktree
    fixture.g('-C',str(seed),'checkout','-qb','eval-base',fixture.base)
    (seed/'permissions.py').write_text('def can_edit(role):\n    return role in ("admin", "editor")\n')
    (seed/'AGENTS.md').write_text('API contracts: first_name returns None for empty rows and otherwise the first name. can_edit returns a boolean, true only for admin or editor; all other roles return false.\n')
    fixture.g('-C',str(seed),'add','.');fixture.g('-C',str(seed),'commit','-qm','document API contracts')
    base = fixture.g('-C',str(seed),'rev-parse','HEAD').stdout.strip()
    fixture.g('-C',str(seed),'checkout','-qb','eval-head')
    (seed/'app.py').write_text('def first_name(rows):\n    return rows[0]["name"]\n')
    (seed/'permissions.py').write_text('def can_edit(role):\n    return role == "admin" or "editor"\n')
    fixture.g('-C',str(seed),'commit','-qam','simplify lookups')
    head = fixture.g('-C',str(seed),'rev-parse','HEAD').stdout.strip()
    fixture.g('-C',str(checkout),'checkout','-q','--detach',head)
    workspace = fixture.root/'workspace';workspace.mkdir()
    for plugin in ('review','content'):
        shutil.copytree(REPO/'plugins'/plugin,workspace/'.eval-plugins'/plugin,
                        ignore=shutil.ignore_patterns('evals','__pycache__'))
    binary=workspace/'.tools';binary.mkdir()
    remote=workspace/'.mock-api';remote.mkdir()
    state,calls=remote/'remote.json',remote/'calls.jsonl'
    # Hardcode fixture paths: login shells may reset PATH and custom env variables.
    code=fixtures.GH_DOUBLE.replace("os.environ['PENDING_MOCK_STATE']",repr(str(state)))
    code=code.replace("os.environ['PENDING_MOCK_CALLS']",repr(str(calls)))
    gh=binary/'gh';gh.write_text(f'#!{sys.executable}\n'+code);gh.chmod(0o755)
    runner=workspace/'run-pending.py'
    runner.write_text('import os, sys\n'+
        f'os.environ["PATH"] = {str(binary)+os.pathsep+os.defpath!r}\n'+
        f'os.execv(sys.executable, [sys.executable, {str(workspace/".eval-plugins/review/skills/review-pr/scripts/pending_review.py")!r}, *sys.argv[1:]])\n')
    fixture.state,fixture.calls=state,calls
    fixture.env.update(PATH=str(binary)+os.pathsep+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1')
    fixture.snapshot,fixture.payload,fixture.receipt=(workspace/n for n in ('previous-target.json','previous-draft.json','receipt.json'))
    write(state,{'base_sha':base,'head_sha':head,'worktree':str(checkout),'legacy_comment_shape':True,
                 'diff':fixture.g('-C',str(seed),'diff',f'{base}...{head}').stdout})
    calls.write_text('')
    write(fixture.payload,{'body':'Previous draft summary','comments':[
        {'key':'empty-input','path':'app.py','line':2,'side':'RIGHT',
         'body':'[P1] Empty input now raises IndexError. Preserve the documented None result for first_name([]).'}]})
    result=fixture.invoke('capture','--worktree',str(checkout))
    if result.returncode:raise RuntimeError(result.stderr)
    fixture.save_ok()
    manual_summary='내가 직접 정리한 초안 요약. 이 문장은 그대로 남겨주세요.'
    fixture.remote(review_body=manual_summary)
    before=json.loads(state.read_text())
    write(output/'receipt-before.json',fixture.record())
    write(output/'remote-before.json',before)
    calls.write_text('')
    prompt=f'''Use the trusted review-pr skill at .eval-plugins/review/skills/review-pr/SKILL.md.
합성 PR example/project #7의 Pending 리뷰를 이어서 진행해줘. 앞선 검토는 중간에 멈췄어.
기존 초안과 내가 수정한 요약을 보존하고, 나머지를 검토해서 타당한 새 지적은 Pending으로 저장해줘.
이 요청으로 검증된 새 코멘트의 Pending 저장을 허용한다. 리뷰 제출과 코드 수정은 하지 마.
기존 receipt: {fixture.receipt}
앞선 입력과 snapshot: previous-draft.json, previous-target.json
검토 대상 checkout: {checkout}
현재 base SHA: {base}
현재 head SHA: {head}
checkout은 clean/detached이고 필요한 commit은 이미 로컬에 있다. fetch나 설치는 필요 없다.
현재 폴더는 코디네이터 산출물용이며 새 snapshot/payload/report를 여기 작성할 수 있다.
원자료, .eval-plugins, .tools, .mock-api를 직접 편집하지 마. receipt는 helper로 갱신할 수 있다.
gh는 로컬 API 대역 {gh}이다. 실제 GitHub나 네트워크는 사용하지 마.
helper 실행은 python3 {runner} inspect|capture|save ... 형태로 해줘.
이 고정 wrapper는 helper용 PATH만 설정하며, 로그인 셸 변수나 권한 변경은 필요 없다.
API 대역은 gh api의 user, PR 메타데이터/diff/reviews/comment 조회, Pending 생성,
GraphQL Pending thread 추가를 지원한다. gh pr 명령은 지원하지 않는다.
실제 검증 결과와 한계를 한국어로 보고해줘.
'''
    if host=='codex':
        model='gpt-6-astra'
        cmd=['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check',
             '--sandbox','workspace-write','--model',model,'-c','model_reasoning_effort="low"',
             '-c','web_search="disabled"','-c','sandbox_workspace_write.exclude_slash_tmp=true',
             '-c','sandbox_workspace_write.exclude_tmpdir_env_var=true','--json','--color','never','-']
    else:
        model='claude-sonnet-5-5'
        cmd=['claude','-p','--model',model,'--effort','medium','--output-format','stream-json','--verbose',
             '--no-session-persistence','--strict-mcp-config','--setting-sources','project',
             '--permission-mode','acceptEdits','--permission-prompts','none','--tools','Read,Write,Edit,Bash,Skill',
             '--max-budget-usd','3','--settings',json.dumps({'sandbox':{'enabled':True,'autoAllowBashIfSandboxed':True,
             'allowUnsandboxedCommands':False,'network':{'allowedDomains':[]}}})]
        for plugin in ('review','content'):cmd+=['--plugin-dir',str(workspace/'.eval-plugins'/plugin)]
        cmd+=['--allowedTools',f'Read(/{checkout}/**)']
        prompt='/review:review-pr\n'+prompt
    (output/'prompt.txt').write_text(prompt)
    source_before=hashes(checkout);instructions_before=hashes(workspace/'.eval-plugins')
    write(output/'source-before.json',source_before);write(output/'instruction-hashes.json',instructions_before)
    record={'host':host,'model':model,'command':cmd,'workspace':str(workspace),'checkout':str(checkout),
            'base_sha':base,'head_sha':head,'status':'running'}
    write(output/'result.json',record);start=time.monotonic()
    with (output/'events.jsonl').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
        process=subprocess.Popen(cmd,cwd=workspace,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,
                                 text=True,env=fixture.env,start_new_session=True)
        try:process.communicate(prompt,timeout=600);record['returncode']=process.returncode
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.communicate();record['error']='timeout'
    events=[]
    for line in (output/'events.jsonl').read_text().splitlines():
        try:events.append(json.loads(line))
        except ValueError:pass
    completed=(any(e.get('type')=='turn.completed' for e in events) if host=='codex' else
               any(e.get('type')=='result' and e.get('subtype')=='success' and not e.get('is_error') for e in events))
    finals=([e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
            if host=='codex' else [e.get('result','') for e in events if e.get('type')=='result'])
    (output/'final.md').write_text('\n\n'.join(finals))
    after=json.loads(state.read_text());api_calls=fixture.log();writes=fixture.mutations()
    source_after=hashes(checkout)
    checks={'completed':bool(completed and record.get('returncode')==0),
            'review_code_loaded':loaded_review_code(events,host),
            'source_unchanged':source_before==source_after,
            'instructions_unchanged':instructions_before==hashes(workspace/'.eval-plugins'),
            'api_double_unchanged':gh.read_text()==f'#!{sys.executable}\n'+code,
            'one_pending_append':len(writes)==1 and writes[0]['endpoint']=='graphql',
            'manual_summary_preserved':after['review_body']==manual_summary,
            'existing_comment_preserved':after['review_comments'][0]==before['review_comments'][0],
            'no_duplicate':len(after['review_comments'])==2,
            'new_finding_anchored':any(c['path']=='permissions.py' and c['line']==2 for c in after['review_comments']),
            'pending_on_original_commit':after.get('readback_state','PENDING')=='PENDING' and after['created_head']==head,
            'verified_receipt':fixture.record()['status']=='pending' and fixture.record()['operation'] is None}
    record.update(status='passed' if all(checks.values()) else 'failed',checks=checks,
                  duration_seconds=round(time.monotonic()-start,2))
    for name,value in [('api-calls.json',api_calls),('remote-after.json',after),('receipt-after.json',fixture.record()),
                       ('source-after.json',source_after),('result.json',record)]:write(output/name,value)
    shutil.copytree(workspace,output/'workspace',ignore=shutil.ignore_patterns('__pycache__'))
    print(json.dumps(record,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',choices=('codex','claude'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();main(args.host,args.output)
