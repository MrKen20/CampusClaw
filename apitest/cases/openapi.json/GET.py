def run(c):
 doc=c.request('/openapi.json',who=None);assert doc['openapi'].startswith('3.')
 assert '/api/conversations/{id}/messages' in doc['paths'] and doc['components']['securitySchemes']['bearerAuth']['scheme']=='bearer'
