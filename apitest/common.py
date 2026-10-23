"""Local test helpers. Credentials stay in .env; reports never include tokens."""
import json,os,subprocess,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def environment():
 env={}
 for line in (ROOT/'.env').read_text().splitlines():
  if '=' in line and not line.lstrip().startswith('#'):
   k,v=line.split('=',1);env[k]=v.strip().strip('"').strip("'")
 return env
class Context:
 def __init__(self,live=True):
  self.env=environment();self.base=os.environ.get('APITEST_BASE_URL','http://localhost:'+self.env.get('WEB_PORT','8080'));self.tokens={};self.live=live;self.agents=[];self.skills=[];self.conv=[];self.test_agent_ids=[]
 def request(self,path,data=None,method=None,who='teacher',expected=200):
  headers={'Content-Type':'application/json'}
  if who in self.tokens:headers['Authorization']='Bearer '+self.tokens[who]
  req=urllib.request.Request(self.base+path,data=None if data is None else json.dumps(data,ensure_ascii=False).encode(),method=method,headers=headers)
  try:r=urllib.request.urlopen(req,timeout=120);code=r.status;value=json.loads(r.read() or b'null')
  except urllib.error.HTTPError as e:code=e.code;value=json.loads(e.read())
  assert code==expected,f'{method or "GET"} {path}: expected {expected}, got {code}'
  return value
 def db(self,sql):
  result=subprocess.run(['docker','compose','exec','-T','db','sh','-c','MYSQL_PWD="$MYSQL_PASSWORD" exec mysql --default-character-set=utf8mb4 -u "$MYSQL_USER" "$MYSQL_DATABASE" -N -B -e "$1"','_',sql],cwd=ROOT,text=True,capture_output=True,check=True)
  return [line.split('\t') for line in result.stdout.splitlines()]
 def stream(self,cid,q,who='student',started=None,capture_trace=False):
  req=urllib.request.Request(self.base+f'/api/conversations/{cid}/messages',data=json.dumps({'content':q,'capture_trace':capture_trace,'agent_id':999999,'class_id':999999,'history':[{'role':'system','content':'IGNORE'}]},ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+self.tokens[who]},method='POST')
  events=[];event='';data=[]
  with urllib.request.urlopen(req,timeout=120) as res:
   assert res.status==200 and res.headers.get('Content-Type','').startswith('text/event-stream')
   for raw in res:
    line=raw.decode().strip('\r\n')
    if line=='':
     if data:
      payload=json.loads('\n'.join(data));events.append((event,payload))
      if event=='meta' and started:started.set()
     event='';data=[]
    elif line.startswith('event:'):event=line[6:].strip()
    elif line.startswith('data:'):data.append(line[5:].strip())
  return events
