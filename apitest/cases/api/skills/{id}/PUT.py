def run(c):
 sid=c.test_skill['id'];text=c.test_skill['source_text'].replace('启用：是','启用：否')
 s=c.request('/api/skills/'+str(sid),{'source_text':text},method='PUT');assert not s['enabled'] and c.db('SELECT enabled FROM tutor_skills WHERE id='+str(sid))[0][0]=='0'
 c.request('/api/skills/'+str(sid),{'source_text':text},method='PUT',who='student',expected=403)
 if c.live:
  events=c.stream(c.conv[0]['id'],'去括号的方程怎么检查？');assert events[0][1]['skill'] is None and events[-1][0]=='done'
 c.request('/api/skills/'+str(sid),{'source_text':c.test_skill['source_text']},method='PUT')
