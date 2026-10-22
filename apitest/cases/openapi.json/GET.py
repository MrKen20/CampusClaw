def run(c):
 doc=c.request('/openapi.json',who=None);assert doc['openapi'].startswith('3.')
 assert '/api/conversations/{id}/messages' in doc['paths'] and doc['components']['securitySchemes']['bearerAuth']['scheme']=='bearer'

 assert '/api/mcp/servers/{id}/tools/{tool}/approve' in doc['paths']
 op=doc['paths']['/api/mcp/servers/{id}/tools/{tool}/approve']['post']
 assert next(p for p in op['parameters'] if p['name']=='tool')['schema']['type']=='string'
 assert doc['components']['schemas']['MCPServerInput']['properties']['auth_token']['writeOnly']
 assert 'tool_calls' in doc['components']['schemas']['Message']['properties']

 for route in ['/api/agents/{id}','/api/conversations/{id}']:
  assert '204' in doc['paths'][route]['delete']['responses'] and '409' in doc['paths'][route]['delete']['responses']
 assert doc['components']['schemas']['Conversation']['properties']['agent_deleted']['type']=='boolean'
