def run(c):
 own=c.request('/api/conversations',who='student');assert all(v['id'] in [int(r[0]) for r in c.db("SELECT id FROM conversations WHERE user_id=(SELECT id FROM users WHERE username='student_a1') AND class_id=1")] for v in own)
 c.request('/api/conversations',expected=403)

 from datetime import datetime
 assert all(datetime.fromisoformat(v['created_at'].replace('Z','+00:00')).tzinfo is not None and datetime.fromisoformat(v['updated_at'].replace('Z','+00:00')).tzinfo is not None for v in own)
 assert own==sorted(own,key=lambda v:(v['updated_at'],v['id']),reverse=True)
