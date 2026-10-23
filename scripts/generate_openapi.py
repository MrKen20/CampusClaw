#!/usr/bin/env python3
"""Generate from @api JSON annotations beside Go handlers; --check detects drift."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def generate():
 paths={};documented=set()
 for file in (ROOT/'backend').rglob('*.go'):
  for line in file.read_text().splitlines():
   if '// @api ' not in line:continue
   v=json.loads(line.split('// @api ',1)[1]);method,path=v['method'],v['path'];documented.add((method,path))
   responses={str(v['status']):{'description':v['summary']}}
   if v.get('response') is not None:
    media='text/event-stream' if v.get('stream') else v.get('media','application/json');content={'schema':v['response']}
    if 'example' in v:content['example']=v['example']
    responses[str(v['status'])]['content']={media:content}
   for code,msg in v['errors'].items():responses[code]={'description':msg,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/Error'},'example':{'error':msg}}}}
   params=v.get('parameters',[])+[{'name':name,'in':'path','required':True,'schema':({'type':'string','pattern':'^[a-z][a-z0-9_]{0,47}$'} if name=='tool' else {'type':'string','enum':['concept','reading','writing','review']} if name=='key' else {'type':'integer','minimum':1})} for name in re.findall(r'\{(\w+)\}',path)]
   op={'summary':v['summary'],'description':v.get('description','')+(' 仅教师可操作。' if v['auth']=='teacher' else ' 仅学生可使用。' if v['auth']=='student' else ''),'operationId':method.lower()+'_'+re.sub(r'[^a-zA-Z0-9]+','_',path).strip('_'),'tags':[path.split('/')[2] if path.startswith('/api/') else 'system'],'security':[] if v['auth']=='public' else [{'bearerAuth':[]}],'responses':responses}
   if params:op['parameters']=params
   if v.get('request'):op['requestBody']={'required':True,'content':{v.get('requestMedia','application/json'):{'schema':v['request']}}}
   paths.setdefault(path,{})[method.lower()]=op
 routes=set(re.findall(r'mux.HandleFunc\("(GET|POST|PUT|DELETE) ([^" ]+)"',(ROOT/'backend/cmd/server/main.go').read_text()))
 if routes!=documented:raise SystemExit(f'Route/documentation drift: missing={routes-documented}, extra={documented-routes}')
 schemas=json.loads((ROOT/'scripts/api_schemas.json').read_text());schemas['Error']={'type':'object','required':['error'],'properties':{'error':{'type':'string'}}}
 return {'openapi':'3.0.3','info':{'title':'CampusClaw API','version':'0.7.1','description':'不透明随机 Bearer Token + 服务端会话；不使用 JWT。角色/班级每次从服务器读取。API注解生成，教师配置即时生效；会话锁定智能体；第6课MCP工具发现、批准、多轮调用及审计；教师智能体删除与学生私人对话删除；四个内置AI应用及模板、SKILL.md/ZIP导入、保留本人LLM诊断API（学生界面无调试入口）；教师应用页维护本班提问模板；资料版本编辑/删除及检索一致性；四应用过滤无关与未使用引用；会话最近活动及消息时间为RFC3339 UTC，SSE与历史一致。'},'servers':[{'url':'/'}],'paths':paths,'components':{'securitySchemes':{'bearerAuth':{'type':'http','scheme':'bearer','description':'POST /api/login 返回的 token，不是 JWT'}},'schemas':schemas}}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();out=ROOT/'backend/internal/apidocs/static/openapi.json';text=json.dumps(generate(),ensure_ascii=False,indent=2)+'\n'
 if args.check:
  if not out.exists() or out.read_text()!=text:raise SystemExit('OpenAPI is stale: run python3 scripts/generate_openapi.py')
  print('OpenAPI matches all registered routes and annotations')
 else:out.write_text(text);print('Generated',len(generate()['paths']),'paths')
