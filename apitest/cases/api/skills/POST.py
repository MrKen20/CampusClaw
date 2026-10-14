def run(c):
 before=c.db('SELECT COUNT(*) FROM tutor_skills')
 for source in ['名称：错误\n启用：是\n\n正文','名称：错误\n名称：重复\n适用条件：a\n启用：是\n\n正文','名称：错误\n适用条件：a\n工具：shell\n启用：是\n\n正文']:
  c.request('/api/skills',{'source_text':source},expected=400)
 assert before==c.db('SELECT COUNT(*) FROM tutor_skills')
 c.request('/api/skills',{'source_text':'invalid'},who='student',expected=403)
