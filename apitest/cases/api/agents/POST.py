def run(c):
 source='名称：接口验收解题引导\n适用条件：去括号,方程\n工具：knowledge_search\n启用：是\n\n只指出去括号错误和下一步，不写最终得数。'
 old=next((s for s in c.skills if s['name']=='接口验收解题引导'),None)
 sk=c.request('/api/skills/'+str(old['id']) if old else '/api/skills',{'source_text':source},method='PUT' if old else 'POST',expected=200 if old else 201);c.test_skill=sk
 for i in range(2):
  name='接口验收智能体'+str(i+1);old=next((a for a in c.agents if a['name']==name),None)
  payload={'name':name,'prompt':'你是学习助手。用简体中文简短解释去括号方法。','enabled':True,'skill_ids':[sk['id']] if i==0 else [],'material_ids':[]}
  a=c.request('/api/agents/'+str(old['id']) if old else '/api/agents',payload,method='PUT' if old else 'POST',expected=200 if old else 201);c.test_agent_ids.append(a['id'])
  rows=c.db('SELECT prompt,enabled FROM tutor_agents WHERE id='+str(a['id']));assert rows[0]==[payload['prompt'],'1']
 c.request('/api/agents',{'name':'学生不能创建'},who='student',expected=403)
