def run(c):
 sid=c.skills[0]['id'];v=c.request(f'/api/skills/{sid}');assert v['source_text']==c.skills[0]['source_text']
 missing=c.request('/api/skills/999999999',expected=404)
 assert c.request(f'/api/skills/{sid}',who='other',expected=404)==missing
