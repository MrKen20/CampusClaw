def run(c):
 import time
 name='验收临时技能'+str(int(time.time()))
 sk=c.request('/api/skills',{'source_text':f'名称：{name}\n适用条件：测试\n启用：是\n\n引导思路。'},expected=201)
 a=c.request('/api/agents/'+str(c.test_agent_ids[1]));a['skill_ids']=[sk['id']];c.request('/api/agents/'+str(a['id']),a,method='PUT')
 c.request('/api/skills/'+str(sk['id']),method='DELETE',who='student',expected=403)
 c.request('/api/skills/'+str(sk['id']),method='DELETE',expected=204)
 assert c.db('SELECT COUNT(*) FROM tutor_agent_skills WHERE skill_id='+str(sk['id']))[0][0]=='0'
