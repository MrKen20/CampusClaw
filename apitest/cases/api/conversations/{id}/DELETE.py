def run(c):
 cid=c.deletion['conversations'][0];route='/api/conversations/'+str(cid)
 before=c.db('SELECT COUNT(*) FROM messages WHERE conversation_id='+str(cid))
 c.request(route,method='DELETE',who=None,expected=401)
 c.request(route,method='DELETE',who='teacher',expected=403)
 for who in ['delete_peer','other']:
  assert c.request(route,method='DELETE',who=who,expected=404)==c.request('/api/conversations/999999999',method='DELETE',who=who,expected=404)
 assert before==c.db('SELECT COUNT(*) FROM messages WHERE conversation_id='+str(cid))
 audit=c.db('SELECT COUNT(*) FROM mcp_tool_calls WHERE conversation_id='+str(cid))
 c.request(route,method='DELETE',who='student',expected=204)
 c.request(route,who='student',expected=404);c.request(route,method='DELETE',who='student',expected=404)
 c.request(route+'/messages',{'content':'不应复活'},who='student',expected=404)
 assert c.db('SELECT COUNT(*) FROM messages WHERE conversation_id='+str(cid))[0][0]=='0'
 assert audit==c.db('SELECT COUNT(*) FROM mcp_tool_calls WHERE conversation_id='+str(cid))
 assert not any(v['id']==cid for v in c.request('/api/conversations',who='student'))
 c.request('/api/conversations/'+str(c.deletion['conversations'][1]),who='student')
 return 'Only owner may delete; same/cross-class strangers404; messages cascaded, audit and other conversations preserved'
