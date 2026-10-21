from mcp_helpers import *
def run(c):
 route='/api/mcp/tool-calls';permission(c,route)
 safe(c,c.request(route))
 if not c.live:return 'Audit authorization verified; real model execution requires --live'
 c.mcp_agent=c.request('/api/agents',{'name':'MCP接口助手'+c.mcp_tag,'prompt':'用简体中文，只引导学生下一步。按学生需要选择教学工具，只给方法。','enabled':True,'skill_ids':[c.mcp_skill['id']],'material_ids':[]},expected=201)
 c.mcp_conv=c.request('/api/conversations',{'agent_id':c.mcp_agent['id']},who='student',expected=201)
 calls=stream_calls(c)
 assert calls and any(t['status']=='ok' for t in calls)
 rows=safe(c,c.request(route));own=[r for r in rows if r['conversation_id']==c.mcp_conv['id']]
 assert {r['id'] for r in own}=={r['id'] for r in calls}
 assert all(r['username']=='student_a1' and r['request_message_id']>0 and r['created_at'] for r in own)
 assert [r['id'] for r in rows]==sorted([r['id'] for r in rows],reverse=True)
 assert not any(r['conversation_id']==c.mcp_conv['id'] for r in c.request(route,who='mcp_other'))
 assert int(c.db('SELECT COUNT(*) FROM mcp_tool_calls WHERE conversation_id='+str(c.mcp_conv['id']))[0][0])==len(calls)
 return 'Real gateway selects actual MCP calls; meta before delta; history and DB audit match; cross-class hidden'
