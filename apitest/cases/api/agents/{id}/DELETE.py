from deletion_helpers import setup
def run(c):
 setup(c);aid=c.delete_agent['id'];route='/api/agents/'+str(aid)
 c.request(route,method='DELETE',who=None,expected=401)
 c.request(route,method='DELETE',who='student',expected=403)
 assert c.request(route,method='DELETE',who='delete_teacher_b',expected=404)==c.request('/api/agents/999999999',method='DELETE',who='delete_teacher_b',expected=404)
 c.request(route,method='DELETE',expected=204)
 for who in ['teacher','student']:
  c.request(route,who=who,expected=404)
  assert not any(a['id']==aid for a in c.request('/api/agents',who=who))
 c.request(route,method='DELETE',expected=404)
 c.request(route,c.delete_payload,method='PUT',expected=404)
 assert c.db('SELECT deleted_at IS NOT NULL,enabled FROM tutor_agents WHERE id='+str(aid))[0]==['1','0']
 for table in ['tutor_agent_skills','tutor_agent_materials']:
  assert c.db('SELECT COUNT(*) FROM '+table+' WHERE agent_id='+str(aid))[0][0]=='0'
 cid=c.deletion['conversations'][0];cp='/api/conversations/'+str(cid)
 history=c.request(cp,who='student');assert history['conversation']['agent_deleted'] and history['messages'][0]['content']=='删除验收消息'
 before=c.db('SELECT COUNT(*) FROM messages WHERE conversation_id='+str(cid))
 c.request(cp+'/messages',{'content':'不应继续生成'},who='student',expected=409)
 assert before==c.db('SELECT COUNT(*) FROM messages WHERE conversation_id='+str(cid))
 c.request('/api/conversations',{'agent_id':aid},who='student',expected=404)
 replacement=c.request('/api/agents',c.delete_payload,expected=201);c.deletion['agents'].append(replacement['id'])
 assert replacement['id']!=aid and c.request(cp,who='student')['conversation']['agent_id']==aid
 return 'Teacher-only class-safe204; bindings cleared, history read-only409; same name recreated with separate ID'
