from mcp_helpers import *
def run(c):
 permission(c,path(c))
 s=safe(c,c.request(path(c)));assert s['has_auth'] and not s['connected']
 assert c.request(path(c),who='mcp_other',expected=404)==c.request(BASE+'/999999999',who='mcp_other',expected=404)
 return 'Student403; missing/cross-class404 identical'
