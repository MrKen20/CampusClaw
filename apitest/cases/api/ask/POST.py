def run(c):
 if not c.live:return 'SKIP: use --live for gateway checks'
 v=c.request('/api/ask',{'question':'今天天气怎么样'});assert v['answer']=='资料中未找到相关内容' and v['citations']==[]
