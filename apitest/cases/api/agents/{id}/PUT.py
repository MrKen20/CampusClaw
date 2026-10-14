def run(c):
 a=c.request('/api/agents/'+str(c.test_agent_ids[0]));original=a.copy()
 other=c.request('/api/agents',who='other')[0]
 bad={**a,'skill_ids':[],'material_ids':[int(c.db('SELECT id FROM materials WHERE class_id=2 LIMIT 1')[0][0])]}
 c.request('/api/agents/'+str(a['id']),bad,method='PUT',expected=404)
 assert c.request('/api/agents/'+str(a['id']))==original
 c.request('/api/agents/'+str(a['id']),a,method='PUT',who='student',expected=403)
 c.request('/api/agents/'+str(other['id']),a,method='PUT',expected=404)
 a['enabled']=False;c.request('/api/agents/'+str(a['id']),a,method='PUT')
 assert all(v['id']!=a['id'] for v in c.request('/api/agents',who='student'))
 c.request('/api/agents/'+str(a['id']),who='student',expected=404)
 c.request('/api/conversations',{'agent_id':a['id']},who='student',expected=404)
 a['enabled']=True;c.request('/api/agents/'+str(a['id']),a,method='PUT')
