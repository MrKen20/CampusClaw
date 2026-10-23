#!/usr/bin/env python3
import argparse,html,importlib.util,json,sys,time
from pathlib import Path
from common import Context
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true',help='exercise real course gateway, parallel streams and MCP tool loop');args=parser.parse_args();context=Context(args.live);results=[]
root=Path(__file__).parent
# Compose may return before the new API process starts listening behind nginx.
for attempt in range(40):
 try:
  assert context.request('/health',who=None)=={'status':'ok'}
  break
 except Exception:
  if attempt==39:raise SystemExit('API did not become available after 40 readiness checks')
  time.sleep(.5)
for name in json.loads((root/'order.json').read_text()):
 start=time.monotonic()
 try:
  spec=importlib.util.spec_from_file_location('case',root/'cases'/name);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);note=module.run(context) or 'Assertions passed';status='SKIP' if note.startswith('SKIP') else 'PASS'
 except Exception as e:
  status='FAIL';note=type(e).__name__+': '+str(e)
 results.append((name,status,note,round(time.monotonic()-start,2)));print(status,name,note,flush=True)
try:
 from acceptance_helpers import cleanup as cleanup_acceptance
 cleanup_acceptance(context)
except Exception as e:
 results.append(('Acceptance fixture cleanup','FAIL',type(e).__name__,0))
 print('FAIL Acceptance fixture cleanup',type(e).__name__,flush=True)
try:
 from refinement_helpers import cleanup as cleanup_refinements
 cleanup_refinements(context)
except Exception as e:
 results.append(('Refinement fixture cleanup','FAIL',type(e).__name__,0))
 print('FAIL Refinement fixture cleanup',type(e).__name__,flush=True)
# Lifecycle fixtures are private to this run, including on case failure.
try:
 from deletion_helpers import cleanup as cleanup_deletions
 cleanup_deletions(context)
except Exception as e:
 results.append(('Deletion fixture cleanup','FAIL',type(e).__name__,0))
 print('FAIL Deletion fixture cleanup',type(e).__name__,flush=True)
# MCP fixtures are disposable and scoped to exact IDs, including on case failure.
try:
 from mcp_helpers import cleanup
 cleanup(context)
except Exception as e:
 results.append(('MCP fixture cleanup','FAIL',type(e).__name__,0))
 print('FAIL MCP fixture cleanup',type(e).__name__,flush=True)
# All sessions created by the suite are explicitly revoked; no secrets enter report.
for who in ['student','other']:
 try:context.request('/api/logout',{},who=who)
 except Exception:pass
out=root/'reports';out.mkdir(exist_ok=True)
rows=''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in results)
(out/('report-live.html' if args.live else 'report.html')).write_text('<!doctype html><meta charset="UTF-8"><title>CampusClaw API tests</title><style>body{font-family:system-ui;margin:32px}td,th{border:1px solid #ddd;padding:10px}table{border-collapse:collapse}</style><h1>CampusClaw 接口验收</h1><p>运行时间：'+time.strftime('%Y-%m-%d %H:%M:%S')+'</p><table><tr><th>接口脚本</th><th>结果</th><th>断言说明</th><th>秒</th></tr>'+rows+'</table>',encoding='utf-8')
sys.exit(1 if any(r[1]=='FAIL' for r in results) else 0)
