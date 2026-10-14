def run(c):
 for aid in c.test_agent_ids:
  v=c.request('/api/conversations',{'agent_id':aid,'class_id':2},who='student',expected=201);c.conv.append(v)
  rows=c.db('SELECT class_id,user_id,agent_id,title FROM conversations WHERE id='+str(v['id']))
  assert rows[0]==['1',c.db("SELECT id FROM users WHERE username='student_a1'")[0][0],str(aid),'新的提问']
 c.request('/api/conversations',{'agent_id':999999999},who='student',expected=404)

 before=c.db('SELECT COUNT(*) FROM conversations')
 c.request('/api/conversations',{'agent_id':c.test_agent_ids[0]},expected=403)
 assert before==c.db('SELECT COUNT(*) FROM conversations')
 before=c.db('SELECT COUNT(*) FROM messages')
 c.request('/api/conversations/'+str(c.conv[0]['id'])+'/messages',{'content':'教师不得提问'},expected=403)
 assert before==c.db('SELECT COUNT(*) FROM messages')
