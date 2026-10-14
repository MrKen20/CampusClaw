def run(c):
 v=c.request('/api/search',{'query':'教研','mode':'keyword','class_id':2});assert isinstance(v['hits'],list)
 for hit in v['hits']:
  rows=c.db('SELECT class_id,HEX(chunk_text) FROM knowledge_chunks WHERE id='+str(hit['chunk_id']));assert rows[0][0]=='1' and bytes.fromhex(rows[0][1]).decode()==hit['excerpt']
 c.request('/api/search',{'query':'','mode':'keyword'},expected=400)
 c.request('/api/search',{'query':'教研','mode':'invalid'},expected=400)
