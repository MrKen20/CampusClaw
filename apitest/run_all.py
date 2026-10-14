#!/usr/bin/env python3
import argparse,html,importlib.util,json,sys,time
from pathlib import Path
from common import Context
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true',help='exercise course gateway including three real streams');args=parser.parse_args();context=Context(args.live);results=[]
root=Path(__file__).parent
for name in json.loads((root/'order.json').read_text()):
 start=time.monotonic()
 try:
  spec=importlib.util.spec_from_file_location('case',root/'cases'/name);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);note=module.run(context) or 'Assertions passed';status='SKIP' if note.startswith('SKIP') else 'PASS'
 except Exception as e:
  status='FAIL';note=type(e).__name__+': '+str(e)
 results.append((name,status,note,round(time.monotonic()-start,2)));print(status,name,note,flush=True)
# All sessions created by the suite are explicitly revoked; no secrets enter report.
for who in ['student','other']:
 try:context.request('/api/logout',{},who=who)
 except Exception:pass
out=root/'reports';out.mkdir(exist_ok=True)
rows=''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in results)
(out/('report-live.html' if args.live else 'report.html')).write_text('<!doctype html><meta charset="UTF-8"><title>CampusClaw API tests</title><style>body{font-family:system-ui;margin:32px}td,th{border:1px solid #ddd;padding:10px}table{border-collapse:collapse}</style><h1>CampusClaw 接口验收</h1><p>运行时间：'+time.strftime('%Y-%m-%d %H:%M:%S')+'</p><table><tr><th>接口脚本</th><th>结果</th><th>断言说明</th><th>秒</th></tr>'+rows+'</table>',encoding='utf-8')
sys.exit(1 if any(r[1]=='FAIL' for r in results) else 0)
