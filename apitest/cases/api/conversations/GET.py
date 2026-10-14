def run(c):
 own=c.request('/api/conversations',who='student');assert all(v['id'] in [int(r[0]) for r in c.db("SELECT id FROM conversations WHERE user_id=(SELECT id FROM users WHERE username='student_a1') AND class_id=1")] for v in own)
 assert all(v['id'] not in [a['id'] for a in c.conv] for v in c.request('/api/conversations'))
