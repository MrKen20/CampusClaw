from mcp_helpers import *
def run(c):
 permission(c,path(c,'/tools'));c.request(path(c,'/tools'),who='mcp_other',expected=404)
 c.mcp_tools=safe(c,c.request(path(c,'/tools')))
 assert {t['name'] for t in c.mcp_tools}=={'formula_hint','unit_convert'}
 assert all(t['description'] and t['inputSchema']['type']=='object' and t['read_only'] and not t['approved'] for t in c.mcp_tools)
 for ref in ['Formula_hint@'+c.mcp_server['name'],'formula-hint@'+c.mcp_server['name'],'missing@'+c.mcp_server['name'],'formula_hint@missing','formula_hint@'+c.mcp_server['name']]:
  c.request('/api/skills',{'source_text':source(c,[ref])},expected=400)
 return 'Complete descriptors; malformed, missing and unapproved bindings rejected before persistence'
