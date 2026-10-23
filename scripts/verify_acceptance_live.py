#!/usr/bin/env python3
"""Run focused, real-gateway evidence probes. Saves JSON data, not a written report."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'apitest'))
from common import Context
from acceptance_helpers import upload,package
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--applications-only',nargs='+',choices=['concept','reading','writing','review']);args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True);c=Context();created={'agents':[],'skills':[],'materials':[],'convs':[]};summary=json.loads((out/'index.json').read_text())['cases'] if args.applications_only and (out/'index.json').exists() else []

def safe_write(name,data):
 text=json.dumps(data,ensure_ascii=False,indent=2)
 for key in ['CHAT_API_KEY','EMBEDDING_API_KEY','MCP_AUTH_TOKEN','MCP_ENCRYPTION_KEY','SESSION_SECRET','MYSQL_PASSWORD']:
  assert not c.env.get(key) or c.env[key] not in text,'credential in evidence'
 (out/(name+'.json')).write_text(text+'\n')

def record(name,cid,q,extra=None):
 events=c.stream(cid,q,capture_trace=True);assert events[-1][0]=='done',str([e for e,_ in events])
 history=c.request('/api/conversations/'+str(cid),who='student');answer=history['messages'][-1];trace=c.request(f"/api/conversations/{cid}/messages/{answer['id']}/trace",who='student')
 assert answer['status']=='complete' and answer['content'] and all(x['http_status']==200 for x in trace['calls'])
 assert trace['calls'][-1]['output_text'] and not trace['calls'][-1]['output_truncated']
 data={'conversation_id':cid,'question':q,'answer':answer,'trace':trace,**(extra or {})};safe_write(name,data)
 summary[:]=[v for v in summary if v['case']!=name]
 summary.append({'case':name,'verified_at':time.strftime('%Y-%m-%d %H:%M:%S'),'conversation_id':cid,'message_id':answer['id'],'llm_requests':len(trace['calls']),'citations':len(answer['citations']),'skill':answer['skill_name'],'raw_response_truncated':any(x['response_truncated'] for x in trace['calls'])});print('PASS',name,'requests='+str(len(trace['calls'])),'citations='+str(len(answer['citations'])),flush=True);return data

try:
 for who,user,key in [('teacher','teacher_a','SEED_TEACHER_PASSWORD'),('student','student_a1','SEED_STUDENT_PASSWORD')]:c.tokens[who]=c.request('/api/login',{'username':user,'password':c.env[key]},who=None)['token']
 fields={
 'concept':{'topic':'磁铁能吸木块吗？这个概念如何理解？','attempt':'我以为磁铁可以吸所有东西。'},
 'reading':{'text':'他站在雨里，把唯一的伞递给了那个孩子，自己转身走进了雨幕。','attempt':'作者没有直接写他善良，为什么还要描写递伞的动作？'},
 'writing':{'text':'今天我去公园，天气很好，花很好看，我很高兴。','goal':'想让这段作文更具体，但保留我自己的经历。'},
 'review':{'text':'解方程2(x+3)=16。','attempt':'我去括号写成2x+3=16，老师说这一步做错了。'} }
 for app in c.request('/api/ai-apps',who='student'):
  if args.applications_only and app['key'] not in args.applications_only:continue
  launched=c.request('/api/ai-apps/'+app['key']+'/launch',{'fields':fields[app['key']]},who='student',expected=201)
  # Retain these four genuine sample conversations for the user's acceptance demo.
  data=record('app-'+app['key'],launched['conversation']['id'],launched['prompt'],{'app_key':app['key']})
  assert data['answer']['skill_name']==app['name']
  agent=c.request('/api/agents/'+str(app['agent_id']));assert agent['prompt'] in data['trace']['calls'][0]['request']['messages'][0]['content']
 if not args.applications_only:
  # Only the following disposable boundary fixtures are removed in finally.
  tag=str(time.time_ns())[-12:]
  source='---\nname: 渐进验收'+tag+'\ndescription: 检查按需加载\ntriggers: 验证检索\ntools: [knowledge_search]\nenabled: true\n---\n\nSELECTED_BODY_MARKER 先给一个检查思路，不计算最终答案。'
  sk=upload(c,'guide.zip',package({'guide/SKILL.md':source,'guide/references/reference.md':'RESOURCE_EXCLUDED_MARKER'}));created['skills'].append(sk['id'])
  inactive=c.request('/api/skills',{'source_text':'名称：未命中验收'+tag+'\n适用条件：绝无此触发词\n工具：knowledge_search\n启用：是\n\nUNSELECTED_BODY_MARKER 不应进入该次模型上下文。'},expected=201);created['skills'].append(inactive['id'])
  uid=c.request('/api/me')['id'];rows=c.db("INSERT INTO materials(class_id,title,file_path,uploaded_by) VALUES(1,'边界验证资料"+tag+"','',"+str(uid)+"); SELECT LAST_INSERT_ID()")
  mid=int(rows[-1][0]);created['materials'].append(mid)
  # Six distinct indexed chunks ensure top-four retrieval cannot mean sending the entire library.
  for i in range(6):
   text='验证检索：分数通分用于统一分母，注意分子分母同时变化。切片标记CHUNK_'+str(i)+'_MARKER。'
   c.db("INSERT INTO knowledge_chunks(knowledge_entry_id,material_id,class_id,chunk_index,chunk_text,char_start,char_end,index_status) VALUES(1,"+str(mid)+",1,"+str(i)+",'"+text+"',"+str(i*60)+","+str((i+1)*60)+",'ready')")
  agent=c.request('/api/agents',{'name':'边界验证'+tag,'prompt':'BOUND_ROLE_TEMPLATE 用简体中文简短解释。','enabled':True,'skill_ids':[sk['id'],inactive['id']],'material_ids':[mid]},expected=201);created['agents'].append(agent['id'])
  conv=c.request('/api/conversations',{'agent_id':agent['id']},who='student',expected=201);created['convs'].append(conv['id'])
  data=record('skill-and-retrieval',conv['id'],'验证检索：分数通分时该先检查什么？',{'indexed_chunks':6,'bound_skill_count':2,'resource_files':['references/reference.md']})
  request=json.dumps(data['trace']['calls'][0]['request'],ensure_ascii=False)
  assert 0<len(data['answer']['citations'])<=4 and sum(('CHUNK_'+str(i)+'_MARKER') in request for i in range(6))==4
  assert 'SELECTED_BODY_MARKER' in request and 'UNSELECTED_BODY_MARKER' not in request and 'RESOURCE_EXCLUDED_MARKER' not in request
  conv=c.request('/api/conversations',{'agent_id':agent['id']},who='student',expected=201);created['convs'].append(conv['id'])
  data=record('skill-not-triggered',conv['id'],'你好，请简单介绍一下学习方法。');assert data['answer']['skill_name']=='' and 'SELECTED_BODY_MARKER' not in json.dumps(data['trace'])
  mcp_agent=next(a for a in c.request('/api/agents',who='student') if a['name']=='MCP数学助手')
  conv=c.request('/api/conversations',{'agent_id':mcp_agent['id']},who='student',expected=201)
  # Retain one real MCP sample with native tool-call trace for the user's demo.
  data=record('mcp',conv['id'],'请先调用公式工具给我矩形面积的公式提示，再调用单位工具给出5米转厘米的进率，只给方法，不给最终数值答案。')
  assert any(v['phase']=='tool-planning' for v in data['trace']['calls']) and any(v['status']=='ok' for v in data['answer']['tool_calls'])
  final=data['trace']['calls'][-1]['request'];assert any(m['role']=='tool' for m in final['messages']) and final['stream'] and 'tools' not in final
 safe_write('index',{'verified_at':time.strftime('%Y-%m-%d %H:%M:%S'),'cases':summary})
finally:
 for id in created['convs']:c.db('DELETE FROM conversations WHERE id='+str(id))
 for id in created['agents']:c.db('DELETE FROM tutor_agents WHERE id='+str(id))
 for id in created['skills']:c.db('DELETE FROM tutor_skills WHERE id='+str(id))
 for id in created['materials']:
  c.db('DELETE FROM knowledge_chunks WHERE material_id='+str(id));c.db('DELETE FROM materials WHERE id='+str(id))
 for who in list(c.tokens):
  try:c.request('/api/logout',{},who=who)
  except Exception:pass
