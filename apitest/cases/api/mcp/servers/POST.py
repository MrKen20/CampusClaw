from mcp_helpers import *
def run(c):
 setup(c)
 permission(c,BASE,{'name':'invalid'})
 c.request(BASE,{'name':c.mcp_server['name'],'base_url':'http://mcp-demo:8090'},expected=400)
 for url in ['http://example.com','http://user:pass@mcp-demo:8090','http://mcp-demo:8090?key=x','http://mcp-demo:8090#frag']:
  c.request(BASE,{'name':'rejected','base_url':url,'auth_token':'test-only'},expected=400)
 row=c.db('SELECT class_id,HEX(token_cipher) FROM mcp_servers WHERE id='+str(c.mcp_server['id']))[0]
 assert row[0]=='1' and len(row[1])>128 and c.env['MCP_AUTH_TOKEN'].encode().hex().upper() not in row[1]
 return 'Teacher-only; invalid URLs/duplicate rejected; DB class authoritative and token encrypted'
