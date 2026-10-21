## Why
第六课要求在第五课成果上接入真实 MCP 工具服务。当前技能仅接受 knowledge_search，对话没有模型工具决策、参数校验、调用循环和审计，无法完成本课清单与课件补充验收。

## What Changes
- 同仓 mcp-server/ 与 Compose 自建只读教学工具：initialize、tools/list、tools/call，formula_hint 与 unit_convert 仅给提示。
- 教师班级内登记/修改/删除、连接/断开、发现工具与审阅批准；令牌仅服务端加密保存，响应只有 has_auth。
- 技能支持 tool@server；保存前校验格式、同班、连接、发现、只读授权与说明批准。
- 模型在候选工具内选名与参数；宿主以发现的 JSON Schema 校验、复核授权、执行和多轮回传；轮数、每次提问与会话累计次数有上限，失败/超限降级继续真实流式生成。
- 先于正文的 meta.tool_calls、历史回放与教师调用审计；OpenAPI/Swagger、真实网关和数据库断言测试。

## Non-goals
不做第七/八课作业/批改/消息队列/指标追踪，不迁移JWT，不实现个人笔记。仅执行获批的只读、非外发工具；写操作和外发工具默认拒绝，不创建通用人工执行审批平台。不开放任意网络地址：Base URL须属于部署者环境白名单，禁重定向。实现本课HTTP JSON-RPC工具子集，不宣称支持所有MCP传输、资源/提示、远端通知或所有第三方服务器。

## Capabilities
### New Capabilities
- `mcp-tools`: 同仓服务、教师管理与审阅、技能绑定、受控模型调用循环、审计与展示。
### Modified Capabilities
无；已有第五课增量以本 change 的集成要求覆盖，不修改尚未归档的历史 change 或长期主规约。

## Impact
Go新增MCP客户端/存储/权限和工具编排，新增JSON Schema验证库；React新增MCP管理页与工具状态；MySQL新增登记/缓存/审阅变更/审计，消息增加可回放调用信息；Compose新增mcp-demo，.env增加随机令牌、加密密钥、地址白名单与调用上限。仅web映射宿主端口，保留原有数据与学生并发对话。
