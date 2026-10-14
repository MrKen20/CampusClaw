def run(c):
 for who,user,key in [('teacher','teacher_a','SEED_TEACHER_PASSWORD'),('student','student_a1','SEED_STUDENT_PASSWORD'),('other','student_b1','SEED_STUDENT_PASSWORD')]:
  v=c.request('/api/login',{'username':user,'password':c.env[key]},who=None)
  assert len(v['token'])==64 and v['user']['username']==user
  c.tokens[who]=v['token']
  rows=c.db('SELECT role,class_id FROM users WHERE id='+str(v['user']['id']))
  assert rows[0]==[v['user']['role'],str(v['user']['class_id'])]
 assert c.request('/api/me',who=None,expected=401)['error']
