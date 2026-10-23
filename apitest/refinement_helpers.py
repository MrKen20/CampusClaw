"""Exact-ID fixtures for editable class content. No user materials are mutated."""
import io,json,time,subprocess,urllib.request,urllib.error

def state(c):
 if not hasattr(c,'refinement'):c.refinement={'tag':str(time.time_ns())[-12:],'material':None,'agent':None,'convs':[],'other_uid':None,'titles':[]}
 return c.refinement

def template(c):
 f=state(c);original=next(a for a in c.request('/api/ai-apps') if a['key']=='concept');probe='模板校验：{{topic}}；已有想法：{{attempt}}';version=original['template_version'];route='/api/ai-apps/concept/template';other_before=c.request('/api/ai-apps',who='other')[0]['user_template']
 c.request(route,{'user_template':probe,'expected_version':version},method='PUT',who='student',expected=403)
 c.request(route,{'user_template':'{{topic}}','expected_version':version},method='PUT',expected=400)
 saved=None
 try:
  saved=c.request(route,{'user_template':probe,'expected_version':version,'class_id':2},method='PUT');assert saved['template_version']==version+1
  c.request(route,{'user_template':probe,'expected_version':version},method='PUT',expected=409)
  assert c.request('/api/ai-apps',who='student')[0]['user_template']==probe
  assert c.request('/api/ai-apps',who='other')[0]['user_template']==other_before
  launched=c.request('/api/ai-apps/concept/launch',{'fields':{'topic':'分数通分','attempt':'同乘'}},who='student',expected=201);f['convs'].append(launched['conversation']['id']);assert launched['prompt']=='模板校验：分数通分；已有想法：同乘'
 finally:
  if saved:
   current=c.request('/api/ai-apps')[0];assert current['user_template']==probe and current['template_version']==version+1,'concurrent template edit; refuse overwrite'
   if version==0:c.db("DELETE FROM tutor_app_templates WHERE class_id=1 AND app_key='concept' AND version="+str(version+1))
   else:c.request(route,{'user_template':original['user_template'],'expected_version':version+1},method='PUT')
 return 'Teacher-only versioned template persists, student preview/launch sync, other class unchanged; original restored'

def upload_material(c,title,body):
 boundary='CampusClawMaterialBoundary';payload=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{title}.md"\r\nContent-Type: text/markdown\r\n\r\n'.encode()+body.encode()+f'\r\n--{boundary}--\r\n'.encode())
 req=urllib.request.Request(c.base+'/api/materials',data=payload,method='POST',headers={'Content-Type':'multipart/form-data; boundary='+boundary,'Authorization':'Bearer '+c.tokens['teacher']})
 with urllib.request.urlopen(req,timeout=120) as res:assert res.status==201;return json.loads(res.read())

def edit_material(c):
 f=state(c);title='数学资料维护验证'+f['tag'];old='精确旧词：去括号时只使用旧版的检查步骤。';new='精确新词：去括号应使用乘法分配律，系数与括号内每一项相乘。';f['titles']=[title+'.md',title+'新版'];m=upload_material(c,title,old);f['material']=m;route='/api/materials/'+str(m['id']);detail=c.request(route);assert detail['version']==1
 name='refine_teacherB'+f['tag'];rows=c.db("INSERT INTO users(username,password_hash,role,class_id) SELECT '"+name+"',password_hash,'teacher',2 FROM users WHERE username='teacher_a'; SELECT LAST_INSERT_ID()");f['other_uid']=int(rows[-1][0]);c.tokens['refine_other']=c.request('/api/login',{'username':name,'password':c.env['SEED_TEACHER_PASSWORD']},who=None)['token']
 payload={'title':title+'新版','body':new,'version':1}
 c.request(route,payload,method='PUT',who='student',expected=403);cross=c.request(route,payload,method='PUT',who='refine_other',expected=404);assert cross==c.request('/api/materials/999999999',payload,method='PUT',who='refine_other',expected=404)
 c.request(route,{'title':'x','body':' ','version':1},method='PUT',expected=400);c.request(route,{**payload,'version':999},method='PUT',expected=409)
 updated=c.request(route,payload,method='PUT');assert updated['version']==2 and updated['index_status']=='ready'
 detail=c.request(route,who='student');assert detail['title']==payload['title'] and detail['body']==new and detail['version']==2
 req=urllib.request.Request(c.base+route+'/file',headers={'Authorization':'Bearer '+c.tokens['student']})
 with urllib.request.urlopen(req) as r:assert r.read().decode()==new
 rows=c.db('SELECT chunk_text FROM knowledge_chunks WHERE material_id='+str(m['id']));assert rows and all('精确旧词' not in r[0] for r in rows)
 f['agent']=c.request('/api/agents',{'name':'资料绑定验证'+f['tag'],'prompt':'fixture','enabled':True,'skill_ids':[],'material_ids':[m['id']]},expected=201)
 return 'Title/body/download/chunks updated; invalid/stale writes preserve data; student403 and cross-class404'

def vector_count(c,mid):
 body=json.dumps({'filter':{'must':[{'key':'material_id','match':{'value':mid}}]},'exact':True})
 raw=subprocess.check_output(['docker','compose','exec','-T','api','wget','-qO-','--header=Content-Type: application/json','--post-data='+body,'http://qdrant:6333/collections/campusclaw_chunks/points/count'])
 return json.loads(raw)['result']['count']

def delete_material(c):
 f=state(c);mid=f['material']['id'];route='/api/materials/'+str(mid);assert vector_count(c,mid)>0
 c.request(route,{'version':2},method='DELETE',who='student',expected=403);c.request(route,{'version':2},method='DELETE',who='refine_other',expected=404);c.request(route,{'version':1},method='DELETE',expected=409)
 c.request(route,{'version':2},method='DELETE',expected=204);c.request(route,who='student',expected=404)
 for table,col in [('materials','id'),('knowledge_entries','material_id'),('knowledge_chunks','material_id'),('tutor_agent_materials','material_id')]:assert c.db('SELECT COUNT(*) FROM '+table+' WHERE '+col+'='+str(mid))[0][0]=='0'
 assert c.request('/api/agents/'+str(f['agent']['id']))['material_ids']==[] and vector_count(c,mid)==0
 assert all(m['id']!=mid for m in c.request('/api/materials',who='student'))
 return 'Deletion clears source/chunks/bindings/actual Qdrant points and download/list visibility; stale409'

def cleanup(c):
 if not hasattr(c,'refinement'):return
 f=c.refinement
 for cid in f['convs']:c.db('DELETE FROM conversations WHERE id='+str(cid))
 if f['agent']:c.db('DELETE FROM tutor_agents WHERE id='+str(f['agent']['id']))
 if f['material']:
  mid=f['material']['id'];rows=c.db('SELECT file_path FROM materials WHERE id='+str(mid))
  if rows:
   path=rows[0][0]
   import re
   if re.fullmatch(r'(?:/app/)?uploads/[a-f0-9]{32}\.(?:md|txt)',path):subprocess.run(['docker','compose','exec','-T','api','rm','-f','--',path],check=True)
  for table,col in [('knowledge_chunks','material_id'),('knowledge_entries','material_id'),('materials','id')]:c.db('DELETE FROM '+table+' WHERE '+col+'='+str(mid))
 for title in f['titles']:c.db("DELETE FROM material_seed_suppressions WHERE class_id=1 AND title='"+title+"'")
 if f['other_uid']:
  c.db('DELETE FROM sessions WHERE user_id='+str(f['other_uid']));c.db('DELETE FROM users WHERE id='+str(f['other_uid']))
