import json,urllib.request,time
from datetime import datetime,timezone
from pathlib import Path
out=Path('/private/tmp/skill-quality-20261110/dogfood/runs/D5-timing/output/evidence')
records=[]
def req(path,data=None):
 r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:63857'+path,data=json.dumps(data).encode() if data is not None else None,method='PUT' if data is not None else 'GET',headers={'Content-Type':'application/json'}),timeout=3)
 with r: rec={'time':datetime.now(timezone.utc).isoformat(),'method':'PUT' if data is not None else 'GET','path':path,'request_body':data,'http_status':r.status,'body':json.loads(r.read())}
 records.append(rec); (out/'25-failure-race-http-timeline.json').write_text(json.dumps(records,indent=2)); return rec['body']
req('/__fixture__/mode',{'fail':True})
print('Ready: fail mode true; waiting for new UI Active request',flush=True)
deadline=time.monotonic()+45
try:
 while time.monotonic()<deadline:
  body=req('/__fixture__/pending')
  active=[x for x in body['pending'] if x['status']=='active' and x['id']>14]
  if active:
   ident=active[0]['id']; req('/__fixture__/mode',{'fail':False})
   (out/'25-mode-normal-ready.json').write_text(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'active_request_id':ident}))
   print('Active pending; normal mode set for latest request',ident,flush=True)
   break
  time.sleep(.05)
 else: raise TimeoutError('No new active request observed')
 while time.monotonic()<deadline:
  body=req('/__fixture__/pending')
  finished=[x for x in body['completed'] if x['id']==ident]
  if finished:
   print('Old request completed',finished[0],flush=True); break
  time.sleep(.2)
finally:
 req('/__fixture__/mode',{'fail':False})
