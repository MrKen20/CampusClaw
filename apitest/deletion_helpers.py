"""Exact-ID disposable fixtures for lifecycle endpoints."""
import time
def setup(c):
 c.deletion={'agents':[],'skills':[],'conversations':[],'users':[]}
 c.delete_tag=str(time.time_ns())
 for who,source,role,cls in [('delete_peer','student_a1','student',1),('delete_teacher_b','teacher_a','teacher',2)]:
  name=who+c.delete_tag
  rows=c.db("INSERT INTO users(username,password_hash,role,class_id) SELECT '"+name+"',password_hash,'"+role+"',"+str(cls)+" FROM users WHERE username='"+source+"'; SELECT LAST_INSERT_ID()")
  c.deletion['users'].append(int(rows[-1][0]))
  key='SEED_TEACHER_PASSWORD' if role=='teacher' else 'SEED_STUDENT_PASSWORD'
  c.tokens[who]=c.request('/api/login',{'username':name,'password':c.env[key]},who=None)['token']
 name='删除接口验收'+c.delete_tag
 c.delete_source='名称：删除验收'+c.delete_tag[-12:]+'\n适用条件：测试\n工具：knowledge_search\n启用：是\n\n只提供方法。'
 sk=c.request('/api/skills',{'source_text':c.delete_source},expected=201);c.deletion['skills'].append(sk['id'])
 materials=c.request('/api/materials')
 c.delete_payload={'name':name,'prompt':'数学解题助手，只给提示','enabled':True,'skill_ids':[sk['id']],'material_ids':[materials[0]['id']] if materials else []}
 c.delete_agent=c.request('/api/agents',c.delete_payload,expected=201);c.deletion['agents'].append(c.delete_agent['id'])
 for _ in range(2):
  v=c.request('/api/conversations',{'agent_id':c.delete_agent['id'],'class_id':2},who='student',expected=201);c.deletion['conversations'].append(v['id'])
 cid=c.deletion['conversations'][0]
 c.db("INSERT INTO messages(conversation_id,role,content,citations_json,status) VALUES("+str(cid)+",'user','删除验收消息','[]','complete')")
 # An explicit audit fixture, not a claim that a real tool was executed here.
 uid=int(c.request('/api/me',who='student')['id'])
 c.db("INSERT INTO mcp_tool_calls(class_id,server_id,server_name,tool_name,tool_ref,user_id,conversation_id,request_message_id,round_number,status,summary) VALUES(1,0,'delete-fixture','hint','hint@delete-fixture',"+str(uid)+","+str(cid)+",0,1,'ok','删除边界测试夹具')")
def cleanup(c):
 if not hasattr(c,'deletion'):return
 for cid in c.deletion['conversations']:
  c.db('DELETE FROM mcp_tool_calls WHERE conversation_id='+str(cid));c.db('DELETE FROM conversations WHERE id='+str(cid))
 for aid in c.deletion['agents']:c.db('DELETE FROM tutor_agents WHERE id='+str(aid))
 for sid in c.deletion['skills']:c.db('DELETE FROM tutor_skills WHERE id='+str(sid))
 for uid in c.deletion['users']:
  c.db('DELETE FROM sessions WHERE user_id='+str(uid));c.db('DELETE FROM users WHERE id='+str(uid))
