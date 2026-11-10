import sys,json,urllib.request,urllib.error,time
from datetime import datetime,timezone
from pathlib import Path
out=Path('/private/tmp/skill-quality-20261110/dogfood/runs/D5-timing/output')
name,method,path=sys.argv[1:4]
assert method in ('GET','PUT') and path in ('/build','/__fixture__/pending','/__fixture__/mode','/api/projects?status=all','/api/projects?status=active','/api/projects?status=archived','/api/projects?status=paused')
data=json.loads(sys.argv[4]) if len(sys.argv)>4 else None
rec={'started':datetime.now(timezone.utc).isoformat(),'method':method,'url':'http://127.0.0.1:63857'+path,'request_body':data}
req=urllib.request.Request(rec['url'],method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
start=time.monotonic()
try:
 r=urllib.request.urlopen(req,timeout=20)
except urllib.error.HTTPError as e:
 r=e
with r:
 rec.update(http_status=r.status,body=json.loads(r.read()),finished=datetime.now(timezone.utc).isoformat(),elapsed_seconds=round(time.monotonic()-start,3))
(out/'evidence'/name).write_text(json.dumps(rec,indent=2))
print(json.dumps(rec,indent=2))
