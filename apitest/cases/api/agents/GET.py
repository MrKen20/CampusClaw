def run(c):
 c.agents=c.request('/api/agents');assert len(c.agents)>=2
 student=c.request('/api/agents',who='student');assert all(a['enabled'] for a in student)
 rows=c.db('SELECT id,name FROM tutor_agents WHERE class_id=1 ORDER BY id')
 assert [(str(a['id']),a['name']) for a in c.agents]==[tuple(r) for r in rows]
