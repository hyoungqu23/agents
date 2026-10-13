import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time

repo=Path('/Users/hyoungmin/.codex/worktrees/product-flow-spec/agents')
sys.path.insert(0,str(repo/'scripts/behavioral'))
import cases
import run

root=Path('/private/tmp/hm2-flow-spec-20261014-codex-natural')
root.mkdir(exist_ok=False)
w=root/'workspace';w.mkdir()
subprocess.run(['git','init','-q',str(w)],check=True)
shutil.copy2(repo/'plugins/product/skills/flow-spec/evals/files/direct-input.md',w/'direct-input.md')
for folder in ('skills','references'):
    shutil.copytree(repo/'plugins/product'/folder,w/'.agents'/folder,ignore=shutil.ignore_patterns('evals','__pycache__'))
before=cases.snapshot(w)
prompt='direct-input.mdの内容に基づいて、質問せずにユーザーフローを flow.md にまとめてください。入力は変更せず、外部調査、インストール、commit、公開はしないでください。回答と文書は日本語にしてください。'
# A natural Japanese request also probes language-neutral discovery; no skill name/path is supplied.
command=['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check',
         '--sandbox','workspace-write','--model','gpt-6-astra','-c','model_reasoning_effort="low"',
         '-c','web_search="disabled"','--json','--color','never','-']
record={'mode':'natural discovery from local .agents/skills','prompt':prompt,'command':command,
        'version':subprocess.check_output(['codex','--version'],text=True).strip(),'status':'running'}
(root/'prompt.txt').write_text(prompt)
run.write_json(root/'before.sha256.json',run.hashes(before))
start=time.monotonic()
try:
    run.execute(command,prompt,w,root,300,'gpt-6-astra')
    after=cases.snapshot(w)
    run.write_json(root/'after.sha256.json',run.hashes(after))
    record['checks']=cases.grade('flow-direct',before,after)
    record['status']='passed' if all(c['passed'] for c in record['checks']) else 'failed'
except Exception as e:
    record['status']='error';record['error']=str(e)
record['duration_seconds']=round(time.monotonic()-start,2)
run.write_json(root/'result.json',record)
print(record['status'])
