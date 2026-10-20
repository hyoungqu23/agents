#!/usr/bin/env python3
"""Opt-in Codex/Claude review-quality cases with host-side semantic assertions.

Only synthetic inputs are sent to model services. This runner never writes to
GitHub. Execute only with authorization for the selected model service.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('review_result', ROOT/'plugins/review/skills/review-code/scripts/review_result.py')
gate = importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
CASES = ('defect', 'clean', 'partial')


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}


def prepare(directory, case):
    source, workspace = directory/'source', directory/'workspace'
    source.mkdir(parents=True);workspace.mkdir()
    env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'PYTHONDONTWRITEBYTECODE':'1'}
    def git(*args):
        return subprocess.check_output(['git','-C',str(source),*args],env=env,text=True).strip()
    git('init','-q','-b','main');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
    (source/'AGENTS.md').write_text('API contracts: can_edit returns bool and permits only admin/editor; any other role returns False. first_name returns None for an empty list and otherwise the first row name. Preserve both contracts.\n')
    (source/'permissions.py').write_text('def can_edit(role):\n    return role in ("admin", "editor")\n')
    (source/'lookup.py').write_text('def first_name(rows):\n    return rows[0]["name"] if rows else None\n')
    git('add','.');git('commit','-qm','base');base=git('rev-parse','HEAD')
    # Parenthesization is equivalent for every input accepted by the base. A set
    # conversion is not: unhashable roles would introduce a real TypeError.
    predicate='(role in ("admin", "editor"))' if case=='clean' else 'role == "admin" or "editor"'
    (source/'permissions.py').write_text('def can_edit(role):\n    return '+predicate+'\n')
    (source/'lookup.py').write_text('def first_name(rows):\n    if not rows:\n        return None\n    return rows[0]["name"]\n')
    (source/'notes.md').write_text('Refactor the helpers without changing their documented contracts.\n')
    git('add','.');git('commit','-qm','simplify helpers');head=git('rev-parse','HEAD')
    git('checkout','-q','--detach',head)
    for plugin in ('review','content'):
        shutil.copytree(ROOT/'plugins'/plugin,workspace/'.eval-plugins'/plugin,
                        ignore=shutil.ignore_patterns('evals','__pycache__'))
    restriction=('이번에는 permissions.py만 검토하고 lookup.py와 notes.md의 내용 검토는 다음으로 미뤄줘. '
                 '두 파일은 변경 목록에서 지우지 말고 검토하지 않았다고 기록해줘.\n' if case=='partial' else '')
    prompt=f'''Use the trusted review-code skill at .eval-plugins/review/skills/review-code/SKILL.md.
이 브랜치 변경을 리뷰해줘. 코드 수정이나 GitHub 쓰기는 하지 마.
검토 대상 checkout: {source}
base: {base}
head: {head}
checkout은 이미 clean/detached이며 필요한 Git 객체가 로컬에 있다.
{restriction}base의 계약과 실제 호출 조건을 근거로 지적하고, 반박 가능한 후보도 확인해줘.
대상 저장소의 코드나 테스트는 실행하지 마. 정적 검토와 신뢰된 Git/검사기만 사용해줘.
현재 폴더는 코디네이터 산출물용이다. skill의 결과 계약에 맞춰 scope.json,
review-result.json, assessment.json, review.md를 여기에 작성해줘.
source checkout과 .eval-plugins는 수정하지 마. 설치, 네트워크, 다른 저장소 조회는 필요 없다.
검토 완료 여부와 실제 수행하지 못한 검증을 한국어로 보고해줘.
'''
    return source, workspace, base, head, env, prompt


def grade(case, scope, report, source_unchanged=True, instructions_unchanged=True):
    verdict=gate.assess(scope,report)
    eligible=[f for f in report.get('findings',[]) if isinstance(f,dict) and f.get('id') in verdict['eligible_findings']]
    correct=[f for f in eligible if f.get('path')=='permissions.py' and f.get('line')==2
             and f.get('severity') in ('P1','P2')]
    checks={'source_unchanged':source_unchanged,'instructions_unchanged':instructions_unchanged,
            'computed_completion':verdict['status']==('partial' if case=='partial' else 'complete'),
            'no_false_positive':not eligible if case=='clean' else len(eligible)==1 and len(correct)==1}
    if case!='clean':
        checks['defect_cause_and_effect']=bool(correct) and any(term in correct[0].get('trigger','').lower()
            for term in ('viewer','guest','reader','admin','권한','허용')) and any(term in correct[0].get('effect','').lower()
            for term in ('truth','string','문자열','참','허용','권한','authorization'))
    if case=='partial':
        reviewed={row.get('path') for row in report.get('files',[]) if isinstance(row,dict) and row.get('status')=='reviewed'}
        checks['deferred_files_not_claimed_reviewed']=not reviewed.intersection({'lookup.py','notes.md'})
        checks['partial_scope_explained']=any(g['code'] in ('missing_file','unreviewed_file') for g in verdict['gaps'])
    return checks,verdict


def command_for(host, model, workspace, source):
    if host=='codex':
        return ['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check',
                '--sandbox','workspace-write','--model',model,'-c','model_reasoning_effort="low"',
                '-c','web_search="disabled"','-c','sandbox_workspace_write.exclude_slash_tmp=true',
                '-c','sandbox_workspace_write.exclude_tmpdir_env_var=true','--json','--color','never','-']
    command=['claude','-p','--model',model,'--effort','medium','--output-format','stream-json','--verbose',
             '--no-session-persistence','--strict-mcp-config','--setting-sources','project',
             '--permission-mode','acceptEdits','--permission-prompts','none','--tools','Read,Write,Edit,Bash,Skill',
             '--max-budget-usd','3','--settings',json.dumps({'sandbox':{'enabled':True,'autoAllowBashIfSandboxed':True,
             'allowUnsandboxedCommands':False,'network':{'allowedDomains':[]}}})]
    for plugin in ('review','content'):command+=['--plugin-dir',str(workspace/'.eval-plugins'/plugin)]
    return command+['--allowedTools',f'Read(/{source}/**)']


def run_case(host,model,directory,case,timeout):
    source,workspace,base,head,env,prompt=prepare(directory,case)
    if host=='claude':prompt='/review:review-code\n'+prompt
    before, instructions=hashes(source),hashes(workspace/'.eval-plugins')
    write(directory/'source-before.json',before);write(directory/'instruction-hashes.json',instructions)
    (directory/'prompt.txt').write_text(prompt)
    command=command_for(host,model,workspace,source)
    record={'host':host,'model':model,'case':case,'command':command,'base':base,'head':head,'status':'error'}
    write(directory/'result.json',record);start=time.monotonic()
    try:
        with (directory/'events.jsonl').open('w') as out,(directory/'stderr.log').open('w') as err:
            process=subprocess.Popen(command,cwd=workspace,stdin=subprocess.PIPE,stdout=out,stderr=err,
                                     env=env,text=True,start_new_session=True)
            try:process.communicate(prompt,timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.communicate();raise RuntimeError('Model execution timed out')
        events=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines() if line.strip()]
        service_errors=[str(e.get('message') or e.get('error','')) for e in events if e.get('type') in ('error','turn.failed')]
        service_errors += [str(e.get('result') or e.get('errors','')) for e in events
                           if e.get('type')=='result' and e.get('is_error')]
        if any(re.search(r'usage limit|rate.?limit|spend limit|quota exceeded',message,re.I) for message in service_errors):
            record['status']='blocked';raise RuntimeError('Model service usage limit; remaining cases not run')
        completed=(any(e.get('type')=='turn.completed' for e in events) if host=='codex' else
                   any(e.get('type')=='result' and e.get('subtype')=='success' and not e.get('is_error') for e in events))
        if process.returncode or not completed:raise RuntimeError('Executor did not complete successfully')
        finals=([e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
                if host=='codex' else [e.get('result','') for e in events if e.get('type')=='result'])
        (directory/'final.md').write_text('\n\n'.join(finals))
        report=json.loads((workspace/'review-result.json').read_text())
        scope=gate.capture_scope(source,base,head)
        checks,verdict=grade(case,scope,report,before==hashes(source),instructions==hashes(workspace/'.eval-plugins'))
        # A model-written assessment is not the authority; recompute independently.
        claimed=json.loads((workspace/'assessment.json').read_text())
        checks['assessment_matches_host']=claimed.get('status')==verdict['status'] and claimed.get('eligible_findings')==verdict['eligible_findings']
        checks['human_report_exists']=(workspace/'review.md').is_file()
        write(directory/'host-assessment.json',verdict)
        record.update(status='passed' if all(checks.values()) else 'failed',checks=checks,returncode=process.returncode)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        record['error']=str(error)
    write(directory/'source-after.json',hashes(source))
    record['duration_seconds']=round(time.monotonic()-start,2);write(directory/'result.json',record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=('codex','claude'),required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',action='append',choices=CASES)
    parser.add_argument('--timeout',type=int,default=600)
    args=parser.parse_args();output=args.output.resolve()
    if output==ROOT or ROOT in output.parents:parser.error('Use a new output directory outside the repository')
    output.mkdir(parents=True,exist_ok=False)
    summary={'host':args.host,'model':args.model,'cases':[],'status':'running'}
    selected=list(dict.fromkeys(args.case or CASES))
    for case in selected:
        result=run_case(args.host,args.model,output/case,case,args.timeout)
        summary['cases'].append(result);write(output/'summary.json',summary)
        print(case+': '+result['status'],flush=True)
        if result['status']=='blocked':break
    summary['not_run']=[case for case in selected if case not in [r['case'] for r in summary['cases']]]
    summary['status']='passed' if all(r['status']=='passed' for r in summary['cases']) else 'failed'
    if any(r['status']=='blocked' for r in summary['cases']):summary['status']='blocked'
    write(output/'summary.json',summary)
    return 0 if summary['status']=='passed' else 1


if __name__=='__main__':sys.exit(main())
