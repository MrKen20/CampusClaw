from mcp_helpers import *
def run(c):
 permission(c,path(c,'/connect'),{})
 c.request(path(c,'/connect'),{},who='mcp_other',expected=404)
 for _ in range(2):
  s=safe(c,c.request(path(c,'/connect'),{}));assert s['connected'] and s['tool_count']==2
 assert c.db('SELECT COUNT(*) FROM mcp_tools WHERE server_id='+str(c.mcp_server['id']))[0][0]=='2'
 return 'Real self-built initialize/list; reconnect replaces snapshot without duplicates'
