## Why
第 4 课已具备本班检索与单次依据问答，但无法由教师配置多个智能体、限定各自技能与材料，也没有持久化流式会话。第 5 课需把角色提示词、解题引导和知识库接入同一回答，并支持同时开启多个独立流式对话。

## What Changes
- 新增教师管理的本班智能体：名称、提示词、启停、技能与材料绑定；学生只选启用的。
- 新增按课件中文元数据格式编写/上传的技能、确定性单技能路由。
- 新增私人会话与消息，创建时锁定智能体；读取最近六条历史，绑定与配置每轮重读。
- 真正调用网关 stream=true，以 SSE meta/delta/done/error 返回，引用先到、消息持久化。无依据的会话仍生成但不写伪引用；既有 /api/ask 行为不变。
- 前端支持多个会话面板并行生成，独立状态与取消；同一会话重复并发发送返回 409，不影响其他会话。
- 从处理函数 API 注解生成 OpenAPI，离线提供 Swagger UI；新增按 URL 组织的 Python 接口测试、数据库一致性检查与不入 Git 的 HTML 报告。

## Capabilities
### New Capabilities
- `streaming-tutor`: 智能体、技能、私人会话、限定资料检索、SSE、多会话并行及接口文档与测试。
### Modified Capabilities
无。认证沿用活动变更 switch-auth-to-bearer-token 的不透明 Bearer Token；长期 auth-upload 尚为 Cookie，后续由其独立归档更新，不在本 change 回写。

## Impact
新增 backend/internal/tutor、apidocs；在 db 与启动入口接入；复用 retrieval 并新增绑定材料范围过滤和真实流式客户端；新增前端助手页面；修改 Nginx；新增 apitest、OpenAPI 生成脚本、Swagger 本地资源。

## Non-goals
不做作业、批改、错题、MCP、外部工具执行、多代理自主编排、JWT/OAuth、刷新令牌、多副本、资料收藏与笔记、计费系统；不删除既有资料或清空数据卷，不归档旧 change。本次多智能体指多个独立会话并行运行，不指一个提问同时编排多个模型代理。
