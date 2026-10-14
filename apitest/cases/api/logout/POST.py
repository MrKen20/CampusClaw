def run(c):
 import hashlib,hmac
 token=c.tokens['teacher'];digest=hmac.new(c.env['SESSION_SECRET'].encode(),token.encode(),hashlib.sha256).hexdigest()
 assert c.db("SELECT COUNT(*) FROM sessions WHERE id='"+digest+"'")[0][0]=='1'
 c.request('/api/logout',{},method='POST');c.request('/api/me',expected=401)
 assert c.db("SELECT COUNT(*) FROM sessions WHERE id='"+digest+"'")[0][0]=='0'
