"""Acceptance fixtures and structural assertions; never print secrets or prompt bodies."""
import io,json,time,zipfile,urllib.request,urllib.error

def upload(c,name,data,who='teacher',expected=201):
 boundary='CampusClawAcceptanceBoundary'
 payload=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+data+f'\r\n--{boundary}--\r\n'.encode())
 headers={'Content-Type':'multipart/form-data; boundary='+boundary}
 if who in c.tokens:headers['Authorization']='Bearer '+c.tokens[who]
 req=urllib.request.Request(c.base+'/api/skills/import',data=payload,headers=headers,method='POST')
 try:
  with urllib.request.urlopen(req,timeout=60) as r:code=r.status;value=json.loads(r.read())
 except urllib.error.HTTPError as e:code=e.code;value=json.loads(e.read())
 assert code==expected,f'import expected {expected}, got {code}'
 return value

def package(files):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
  for k,v in files.items():z.writestr(k,v)
 return b.getvalue()

def fixtures(c):
 if hasattr(c,'acceptance'):return c.acceptance
 c.acceptance={'tag':str(time.time_ns())[-12:],'convs':[],'agents':[],'skills':[]}
 return c.acceptance

def catalog(c):
 f=fixtures(c);apps=c.request('/api/ai-apps');assert {a['key'] for a in apps}=={'concept','reading','writing','review'}
 other=c.request('/api/ai-apps',who='other');assert all(a['agent_id']!=b['agent_id'] for a,b in zip(apps,other))
 assert all(a['system_template'] and '{{' in a['user_template'] and len(a['fields'])==2 for a in apps)
 c.request('/api/ai-apps',who=None,expected=401);f['apps']=apps
 return '4 distinct applications, per-app templates and class-local agents'

def launch(c):
 f=fixtures(c)
 for app in f['apps']:
  fields={v['key']:'学习验收输入' for v in app['fields']}
  launched=c.request('/api/ai-apps/'+app['key']+'/launch',{'fields':fields},who='student',expected=201)
  conv=launched['conversation'];f['convs'].append(conv['id']);assert conv['agent_id']==app['agent_id'] and '{{' not in launched['prompt'] and len(launched['prompt'])<=500
  c.request('/api/conversations/'+str(conv['id']),who='other',expected=404)
 c.request('/api/ai-apps/concept/launch',{'fields':{}},who='student',expected=400)
 c.request('/api/ai-apps/concept/launch',{'fields':{}},expected=403)
 return '4 task forms render without an LLM call; private conversation ownership enforced'

def imports(c):
 f=fixtures(c);source='---\nname: 验收技能'+f['tag']+'\ndescription: 技能包验证\ntriggers: 验收关键词\ntools: [knowledge_search]\nenabled: true\n---\n\nACTIVATED_SKILL_BODY 先检查思路，不给最终答案。'
 skill=upload(c,'guide.zip',package({'guide/SKILL.md':source,'guide/references/note.md':'ATTACHMENT_NOT_AUTO_SENT'}));f['skills'].append(skill['id']);f['skill']=skill
 assert skill['resources']=={'references/note.md':'ATTACHMENT_NOT_AUTO_SENT'}
 saved=c.request('/api/skills/'+str(skill['id']));assert saved['resources']==skill['resources'] and saved['source_text']==source
 c.request('/api/skills/'+str(skill['id']),who='other',expected=404)
 upload(c,'SKILL.md',source.encode(),who='student',expected=403)
 for bad in [{'note.md':'missing'},{'SKILL.md':source,'../escape.txt':'unsafe'},{'SKILL.md':source,'run.py':'code'},{'SKILL.md':source,'references/huge.txt':'x'*33000}]:upload(c,'bad.zip',package(bad),expected=400)
 return 'SKILL.md ZIP persisted; missing manifest, traversal, code and oversize rejected'

def traces(c):
 if not c.live:return 'SKIP: --live for actual gateway trace'
 f=fixtures(c);agent=c.request('/api/agents',{'name':'调用验收'+f['tag'],'prompt':'TRACE_ROLE_TEMPLATE 用简体中文简短回应。','enabled':True,'skill_ids':[f['skill']['id']],'material_ids':[]},expected=201);f['agents'].append(agent['id'])
 conv=c.request('/api/conversations',{'agent_id':agent['id']},who='student',expected=201);f['convs'].append(conv['id'])
 for capture,q in [(True,'验收关键词：请指导我下一步怎么检查？'),(False,'这次不记录调用')]:
  events=c.stream(conv['id'],q,capture_trace=capture);assert events[-1][0]=='done'
  mid=events[-1][1]['message_id'];path=f"/api/conversations/{conv['id']}/messages/{mid}/trace"
  history=c.request('/api/conversations/'+str(conv['id']),who='student');assert history['messages'][-1]['has_trace']==capture
  if not capture:c.request(path,who='student',expected=404);continue
  trace=c.request(path,who='student');assert len(trace['calls'])==1
  call=trace['calls'][0];req=call['request'];assert req['stream'] and req['model']==c.env['CHAT_MODEL'] and req['max_tokens']==500 and req['temperature']==.2
  msg=json.dumps(req['messages'],ensure_ascii=False);assert 'TRACE_ROLE_TEMPLATE' in msg and 'ACTIVATED_SKILL_BODY' in msg and 'ATTACHMENT_NOT_AUTO_SENT' not in msg
  assert call['http_status']==200 and call['output_text'] and (call['response_truncated'] or '[DONE]' in call['response'])
  for name in ['CHAT_API_KEY','MCP_AUTH_TOKEN','SESSION_SECRET']:
   assert not c.env.get(name) or c.env[name] not in json.dumps(trace)
  c.request(path,expected=403);c.request(path,who='other',expected=404)
 return 'real request parameters, activated skill only, default-off tracing and private access verified'

def cleanup(c):
 if not hasattr(c,'acceptance'):return
 f=c.acceptance
 for id in f['convs']:c.db('DELETE FROM conversations WHERE id='+str(id))
 for id in f['agents']:c.db('DELETE FROM tutor_agents WHERE id='+str(id))
 for id in f['skills']:c.db('DELETE FROM tutor_skills WHERE id='+str(id))
