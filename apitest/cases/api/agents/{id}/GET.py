def run(c):
 aid=c.test_agent_ids[0];a=c.request('/api/agents/'+str(aid));assert a['id']==aid
 assert c.request('/api/agents/'+str(aid),who='other',expected=404)==c.request('/api/agents/999999999',who='other',expected=404)
