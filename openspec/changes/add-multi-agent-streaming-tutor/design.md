## Context
见 proposal；现有 Go net/http + React + MySQL/Qdrant，认证沿用不透明 Bearer，旧占位 assistants/skills 表没有业务数据。本课以2026-10-14读到的scope/session/skill-model/route/stream/answer/apply/think与任务清单为依据；原型仅作交互参考，JWT不迁入。

## Goals / Non-Goals
目标：配置、绑定、私人消息、真实SSE及多面板并行；非目标见proposal。

## Decisions
1. 使用新的 tutor_agents/tutor_skills 表避免破坏原 skills 占位表；两张绑定表带外键、会话/消息附索引、role CHECK。幂等建表与种子只插缺失项，不覆盖教师配置。为每班预置两个不同角色智能体和一条解题引导技能，默认绑定本班已有材料；新上传由教师显式绑定。
2. Binding事务先验证本班关联，再写配置/替换绑定。所有新对象错误统一资源不存在404。技能中文单文件解析，不引入MCP/脚本执行。
3. retrieval新增SearchBound，将允许材料集合带入关键字SQL、Qdrant过滤与回表，在取top-k前过滤；旧Search不改变。学科标题过滤在top4后。
4. ChatClient新增Stream调用stream=true；逐SSE帧解析choices.delta.content，必须收到[DONE]。不把完整回答拆字伪装流式。按会话id的sync.Map锁采用LoadOrStore即时409，不同会话不锁。数据库写partial/complete；断连保存用独立短超时上下文，不继续上游生成。
5. 系统消息角色/技能/固定安全边界，用户消息资料；历史最近6条500字，最新用户内容替换为证据块，不重复本轮。引用过滤器跨片段缓存[n]，无效编号剥除，仅合法范围保留；最终正文等于已推送文本。
6. 前端助手页常驻于已登录App，不因材料页切换卸载；多个会话以id索引状态，各自AbortController。可同时开启多个智能体，取消只作用一个；登出/401终止全部并清状态，防跨账户消息遗留。
7. API注解用单行JSON @api，Python生成OpenAPI（显式schema/error/security），Go embed本地swagger-ui-dist资源。生成检查比对main路由。apitest用Python标准库HTTP+docker exec数据库查询；不输出令牌/密钥。网关真实验证控制调用数，复杂故障/并发用mock网关Go测试。

## Risks / Trade-offs
- 模型引导行为→固定硬约束、低温度及真实题目开关对照；不声称提示词能替代访问控制。
- 同会话并发→409避免历史交错；锁仅单实例有效，与现有部署相符。
- 生成中断→保存部分正文并标partial，页面展示未完成；不自动重发POST以免重复消息。
- 网关额度→配置来自本机.env，真实演示少量调用，自动基础测试可不触发模型。

## Migration Plan
不删旧表/卷，仅增加表；docker compose up --build，重复启动验证幂等。旧页面、问答/上传不变；回滚旧镜像，新表数据保留。不回写openspec/specs或归档旧change。
