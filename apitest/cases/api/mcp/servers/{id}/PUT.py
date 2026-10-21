from mcp_helpers import *
def run(c):
 data={'name':c.mcp_server['name'],'base_url':'http://mcp-demo:8090','auth_token':''}
 permission(c,path(c),data,'PUT');c.request(path(c),data,method='PUT',who='mcp_other',expected=404)
 before=c.db('SELECT HEX(token_cipher) FROM mcp_servers WHERE id='+str(c.mcp_server['id']))
 safe(c,c.request(path(c),data,method='PUT'))
 assert before==c.db('SELECT HEX(token_cipher) FROM mcp_servers WHERE id='+str(c.mcp_server['id']))
 c.request(path(c),dict(data,auth_token='invalid-token-for-test'),method='PUT')
 c.request(path(c,'/connect'),{},expected=502)
 assert c.request(path(c,'/tools'))==[] and not c.request(path(c))['connected']
 c.request(path(c),dict(data,auth_token=c.env['MCP_AUTH_TOKEN']),method='PUT')
 return 'Blank preserves encrypted token; incorrect remote token causes safe502 and empty cache'
