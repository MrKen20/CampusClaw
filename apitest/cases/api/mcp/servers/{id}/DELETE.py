from mcp_helpers import *
def run(c):
 permission(c,path(c),method='DELETE');c.request(path(c),method='DELETE',who='mcp_other',expected=404)
 before=c.db('SELECT COUNT(*) FROM mcp_tool_calls WHERE server_id='+str(c.mcp_server['id']))
 c.request(path(c),method='DELETE',expected=204);c.request(path(c),expected=404)
 assert c.db('SELECT COUNT(*) FROM mcp_tools WHERE server_id='+str(c.mcp_server['id']))[0][0]=='0'
 assert before==c.db('SELECT COUNT(*) FROM mcp_tool_calls WHERE server_id='+str(c.mcp_server['id']))
 if c.live and c.mcp_conv:
  calls=stream_calls(c);assert calls and all(t['status']=='denied' and not t.get('id') for t in calls)
  assert before==c.db('SELECT COUNT(*) FROM mcp_tool_calls WHERE server_id='+str(c.mcp_server['id']))
 return 'Delete clears cache, retains audit; stale skill reference denied without fabricating server identity'
