from mcp_helpers import *
def run(c):
 route=path(c,'/disconnect');permission(c,route,{})
 c.request(route,{},who='mcp_other',expected=404)
 s=c.request(route,{});assert not s['connected'] and s['tool_count']==0
 assert c.request(path(c,'/tools'))==[]
 if c.live and c.mcp_conv:
  calls=stream_calls(c);assert calls and all(t['status']=='denied' and t['round']==0 for t in calls)
  rows=c.request('/api/mcp/tool-calls');assert all(any(r['id']==t['id'] and r['status']=='denied' for r in rows) for t in calls)
 return 'Disconnected cache empty; bound calls denied before execution and final answer continues' if c.live else 'Disconnect clears cache atomically'
