from mcp_helpers import *
def run(c):
 permission(c,BASE)
 rows=safe(c,c.request(BASE));assert any(s['id']==c.mcp_server['id'] for s in rows)
 assert all(s['id']!=c.mcp_server['id'] for s in c.request(BASE,who='mcp_other'))
 return 'Class-scoped list has no credential fields or values'
