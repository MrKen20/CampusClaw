def run(c):
 cid=c.conv[0]['id'];v=c.request('/api/conversations/'+str(cid),who='student');assert v['conversation']['agent_id']==c.test_agent_ids[0]
 missing=c.request('/api/conversations/999999999',who='other',expected=404)
 c.request('/api/conversations/'+str(cid),expected=403)
 assert c.request('/api/conversations/'+str(cid),who='other',expected=404)==missing
