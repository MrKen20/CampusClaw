def run(c):
 c.skills=c.request('/api/skills');assert any('解题引导' in s['name'] for s in c.skills)
 rows=c.db('SELECT COUNT(*) FROM tutor_skills WHERE class_id=1');assert int(rows[0][0])==len(c.skills)
