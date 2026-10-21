from mcp_helpers import *
def run(c):
 for t in c.mcp_tools:
  route=path(c,'/tools/'+t['name']+'/approve');data={'fingerprint':t['fingerprint']}
  permission(c,route,data);c.request(route,data,who='mcp_other',expected=404)
  c.request(route,{'fingerprint':'0'*64},expected=409)
  assert c.request(route,data)['approved']
 refs=[t['name']+'@'+c.mcp_server['name'] for t in c.mcp_tools]
 c.mcp_skill=c.request('/api/skills',{'source_text':source(c,refs)},expected=201)
 assert c.mcp_skill['tools']==refs
 c.request(path(c,'/connect'),{})
 assert all(t['approved'] for t in c.request(path(c,'/tools')))
 return 'Current fingerprint required; approval allows skill binding and survives unchanged rediscovery'
