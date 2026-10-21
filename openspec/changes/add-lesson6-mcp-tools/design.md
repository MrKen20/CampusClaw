## Context
已实际读取2026-10-21提供的全部第6课HTML正文并核对最终URL，原型OpenAPI与截图仅作交互参考；网关实测支持OpenAI function tool_calls。现有Go+MySQL/Qdrant，学生SSE和独立会话保留。历史主规约中的Cookie/迭代1文字是旧事实，按已实现的Bearer增量和本次用户授权推进。

## Goals / Non-Goals
完整实现本课工具两端和模型多轮编排；Non-goals见proposal，尤其不做写入/外发工具、后续课程业务和全协议兼容。

## Decisions
1. 自建Go独立模块 mcp-server，8090只在Compose内网开放，固定POST /mcp JSON-RPC、GET /health；2025-03-26协议版本、stateless，接受initialized通知，GET /mcp返回405。令牌必须来自MCP_AUTH_TOKEN，无默认值，Origin非空拒绝。两个工具均标注readOnlyHint=true、openWorldHint=false，不求最终得数。
2. backend/internal/mcp 独立管理器：AES-GCM加密令牌（MCP_ENCRYPTION_KEY随机32字节环境密钥），登记留空时自建地址使用MCP_AUTH_TOKEN；编辑留空保留原密钥。前端只显示has_auth，提交后清空输入。Base URL只允许MCP_ALLOWED_BASE_URLS部署白名单的精确地址，禁止凭据/查询/fragment/非HTTP(S)；客户端不使用代理、不跟随重定向，8秒超时、1MB响应上限，固定安全错误不回显远端响应或请求头。
3. 数据表mcp_servers(class_id,name,base_url,token_cipher,connected,last_error,revision)、mcp_tools(服务器外键、name、description、input_schema、annotations、fingerprint、approved)、mcp_tool_reviews(历史指纹/批准指纹)、mcp_tool_changes(变更记录)、mcp_tool_calls(班级/服务器快照名/用户/会话/提问消息/轮次/引用/状态/脱敏摘要/时间)。删服务器保留审计。连接先置未连接并清空缓存，握手/发现/schema检查全部成功才原子替换；服务器锁串行配置改动，调用持读锁复核当前状态，断开成功后新调用均被拒。
4. 教师查看完整说明和参数结构后逐工具批准只读执行；名称/说明/schema/annotations指纹变化撤回批准并留变更记录。服务器重连同指纹保留批准。保存技能须工具已批准且只读；缺注解、写操作和外发工具拒绝。工具名^[a-z][a-z0-9_]{0,47}$，服务器名^[a-z][a-z0-9_-]{0,47}$，大小写不自动修正。
5. JSON Schema编译校验使用santhosh-tekuri/jsonschema/v5（禁外部URL引用），限制根object/发现数量64/说明2000字/schema32KB。模型function名称由服务器ID/工具名构造，本次候选集与引用映射唯一；仅命中技能的MCP绑定进入候选，不暴露URL/令牌。工具返回最长2000字，先脱敏再已知注入句式检查，命中整条替换固定说明，作为role=tool而非system追加；已有检索证据仍在user消息。
6. 编排先以stream=false让模型提出原生tool_calls，解析参数按发现schema校验并逐工具授权，工具结果回传后可继续多轮；最后调用已有stream=true输出真实delta，绝不把完整回答拆字伪造流。默认3轮、每问6次、每会话30次，均可环境配置且有合理上限；工具阶段时间预算45秒，每远端调用8秒，整体请求90秒。达到任一预算停止调用并用已有资料/结果作答，局部错误不阻断主路径。未连接/已删绑定在候选准备时明确denied，能归属服务器的写审计，已删/他班不泄露身份。模型请求候选外工具同样denied。
7. 初始meta带skill/citations；每次调用再发meta.tool_calls（只含新事件），全部在最终delta前。messages新增可空tool_calls_json用于刷新回放，前端增量累积且不清空之前citations；会话独立控制器与停止行为保持。无工具技能完全沿用第5课链路。
8. 教师新增MCP工具侧栏：服务器卡片/独立登记编辑窗口、连接断开/工具详情/批准只读/删除确认与审计表；技能编辑器可从已批准工具插入引用。学生仅在回答边显示工具/轮次/状态/摘要，不显示服务地址与凭证；深浅色与390px沿用现有风格。Swagger入口继续只在登录页。

## API
教师专用 /api/mcp/servers GET/POST，/{id} GET/PUT/DELETE，/{id}/connect POST，/{id}/disconnect POST，/{id}/tools GET，/{id}/tools/{tool}/approve POST（携带fingerprint，变化409）；/api/mcp/tool-calls GET（倒序最多100）。未登录401、学生403、跨班/缺失404完全同形、配置不合法400、连接失败502且安全提示、DB故障503。

## Risks / Trade-offs
只支持本课HTTP工具子集；第三方地址需部署者显式加入白名单，写/外发工具不执行。模型决策有不确定性，以脚本模型验证两轮/错误/预算等分支，再以课程网关验证真实路径；不为通过测试硬编码某个提问必调。工具说明检查不是完备注入防护，硬边界是候选授权、只读批准与限额。加密环境密钥应持续保管，换密钥须重新登记令牌。

## Migration / Verification
幂等建表/消息新增列，不覆盖现有记录。生成随机本地.env配置但不输出密钥。各task独立verify/commit；真实Compose服务、网关、DB断言、浏览器和密钥扫描均留证据；人工同伴互验只列待办，不代勾、不回写长期主规约。
