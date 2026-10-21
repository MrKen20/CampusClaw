"""MCP fixtures owned by one suite run; never print credentials or remote bodies."""
import json,time
BASE='/api/mcp/servers'
def path(c,suffix=''):
 return BASE+'/'+str(c.mcp_server['id'])+suffix
def safe(c,value):
 text=json.dumps(value,ensure_ascii=False)
 assert 'auth_token' not in text and 'token_cipher' not in text
 for key in ['MCP_AUTH_TOKEN','MCP_ENCRYPTION_KEY','CHAT_API_KEY']:
  secret=c.env.get(key,'')
  assert not secret or secret not in text
 return value
def setup(c):
 c.mcp_tag=str(time.time_ns());c.mcp_server=None;c.mcp_agent=None;c.mcp_skill=None;c.mcp_conv=None;c.mcp_other_uid=None
 username='mcp_peer_'+c.mcp_tag
 rows=c.db("INSERT INTO users(username,password_hash,role,class_id) SELECT '"+username+"',password_hash,'teacher',2 FROM users WHERE username='teacher_a'; SELECT LAST_INSERT_ID()")
 c.mcp_other_uid=int(rows[-1][0])
 login=c.request('/api/login',{'username':username,'password':c.env['SEED_TEACHER_PASSWORD']},who=None);c.tokens['mcp_other']=login['token']
 c.mcp_server=c.request(BASE,{'name':'apitest-mcp-'+c.mcp_tag,'base_url':'http://mcp-demo:8090','auth_token':'','class_id':2},expected=201)
 safe(c,c.mcp_server)
def source(c,refs):
 return '名称：MCP接口'+c.mcp_tag[-12:]+'\n适用条件：方程,去括号,面积,单位,米\n工具：'+','.join(refs)+'\n启用：是\n\n先了解学生卡在哪一步。需要公式提示时使用formula_hint，单位进率用unit_convert；只给方法，不算最终答案。'
def permission(c,route,data=None,method=None):
 c.request(route,data,method=method,who='student',expected=403)
 c.request(route,data,method=method,who=None,expected=401)
def stream_calls(c):
 events=c.stream(c.mcp_conv['id'],'请先调用公式工具给我面积方法，再调用单位工具给出5米转厘米的进率，只讲方法，不给最终得数。')
 assert events[-1][0]=='done' and any(k=='delta' for k,v in events)
 calls=[call for k,v in events if k=='meta' for call in v.get('tool_calls',[])]
 first=next(i for i,(k,v) in enumerate(events) if k=='delta')
 assert all(i<first for i,(k,v) in enumerate(events) if k=='meta' and v.get('tool_calls'))
 history=c.request('/api/conversations/'+str(c.mcp_conv['id']),who='student')
 assert history['messages'][-1].get('tool_calls')==calls
 safe(c,calls)
 return calls
def cleanup(c):
 # Exact fixture IDs only. Foreign keys cascade their messages/bindings/cache.
 if not hasattr(c,'mcp_tag'):return
 sid=(c.mcp_server or {}).get('id')
 if c.mcp_conv:c.db('DELETE FROM conversations WHERE id='+str(c.mcp_conv['id']))
 if c.mcp_agent:c.db('DELETE FROM tutor_agents WHERE id='+str(c.mcp_agent['id']))
 if c.mcp_skill:c.db('DELETE FROM tutor_skills WHERE id='+str(c.mcp_skill['id']))
 if sid:
  c.db('DELETE FROM mcp_tool_calls WHERE server_id='+str(sid))
  c.db('DELETE FROM mcp_tool_changes WHERE server_id='+str(sid))
  c.db('DELETE FROM mcp_servers WHERE id='+str(sid))
 if c.mcp_other_uid:
  c.db('DELETE FROM sessions WHERE user_id='+str(c.mcp_other_uid))
  c.db('DELETE FROM users WHERE id='+str(c.mcp_other_uid))
