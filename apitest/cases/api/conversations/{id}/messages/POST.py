def run(c):
 if not c.live:return 'SKIP: use --live for real concurrent streams'
 import concurrent.futures,threading,re
 from datetime import datetime
 start=threading.Event();cid=c.conv[0]['id'];a=c.request('/api/agents/'+str(c.test_agent_ids[0]));a['enabled']=False;c.request('/api/agents/'+str(a['id']),a,method='PUT')
 try:
  with concurrent.futures.ThreadPoolExecutor(2) as pool:
   one=pool.submit(c.stream,cid,'去括号的方程怎么检查？','student',start)
   assert start.wait(60),'first stream did not start'
   c.request(f'/api/conversations/{cid}/messages',{'content':'重复请求'},who='student',expected=409)
   two=pool.submit(c.stream,c.conv[1]['id'],'解释方程去括号的方法。')
   outcomes=[one.result(timeout=120),two.result(timeout=120)]
  for conv,events in zip(c.conv,outcomes):
   assert events[0][0]=='meta' and events[-1][0]=='done',str([x[0] for x in events])
   assert events[0][1]['agent_id']==conv['agent_id'] and events[0][1]['citations']==[]
   parts=[v['text'] for e,v in events if e=='delta'];assert len(parts)>1
   answer=''.join(parts);assert answer and not re.search(r'\[\d+\]',answer) and answer!='资料中未找到相关内容'
   saved=c.request('/api/conversations/'+str(conv['id']),who='student')['messages'];assert saved[-1]['content']==answer and saved[-1]['id']==events[-1][1]['message_id'] and saved[-1]['status']=='complete'
   rows=c.db('SELECT HEX(content),status FROM messages WHERE id='+str(saved[-1]['id']));assert bytes.fromhex(rows[0][0]).decode()==answer and rows[0][1]=='complete'
   meta=events[0][1];assert saved[-2]['created_at']==meta['user_created_at'] and saved[-1]['created_at']==meta['assistant_created_at']==events[-1][1]['created_at']
   for m in saved:assert datetime.fromisoformat(m['created_at'].replace('Z','+00:00')).tzinfo is not None
   latest=c.request('/api/conversations/'+str(conv['id']),who='student')['conversation'];assert latest['updated_at']>=saved[-1]['created_at']
  assert outcomes[0][0][1]['skill']['name']=='接口验收解题引导' and outcomes[1][0][1]['skill'] is None
 finally:
  a['enabled']=True;c.request('/api/agents/'+str(a['id']),a,method='PUT')
