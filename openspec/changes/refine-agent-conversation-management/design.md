## Context
当前tutor_agents被conversations外键引用，硬删会失败或误删学生历史；messages随conversation级联删除，MCP审计无该外键，可继续保留。流式请求使用按conversation id的busy标记；当前示例常量和agent.prompt直接进入欢迎页，资料列表flex:1/min-height:0会被分类占满。沿用Go/React/MySQL/Bearer与单实例，本次用户授权覆盖旧config中“迭代1”的陈旧范围文字。

## Goals / Non-Goals
落实proposal的九项优化；采用可增量迁移的生命周期标记，不重置数据。Non-goals见proposal；不请求模型生成示例，不创建恢复/回收站产品。

## Decisions
1. 智能体以deleted_at软删除，查询配置/可选/修改排除已删；不级联抹除学生私人消息。保留名称/角色快照所在原行，历史Conversation增加agent_deleted布尔。旧会话提问409并显示只读提示。相较直接级联删会话，该策略保护学生历史；相较仅停用，删除入口与已停用语义分明。
2. 以generated active_name（删除时为NULL）+class_id唯一索引替换原(class_id,name)唯一索引，使同名重建可用；保留seed_key避免启动Seed复活删除记录。迁移先加列/新索引再删除旧索引，按information_schema检测重复启动；不做自动回滚删除事实。
3. Service按agent id保存RW锁：新建和生成持读锁，删除TryLock，正生成则409；同一智能体不同会话可并行持读锁。智能体删除在事务里锁定本班未删行，置deleted_at、enabled=false并清绑定。现有SaveAgent在行锁查询中排除已删除。
4. 对话DELETE与SendMessage共享busy.LoadOrStore，以相同粒度互斥；取得锁后重新核验对话，防先读到再被删的竞态。DELETE只按本人/班级及有效关联归属删除，级联消息，MCP审计保留；不在浏览器发送过程中强制删除。
5. 前端教师统一确认弹窗类型agent/skill，学生历史项将打开按钮与垃圾桶分开，不嵌套button；显示目标名称与不可恢复说明。取消无请求，失败保持列表/弹窗并提示，成功清理open/panels/active；异步打开会话的迟到响应不能复活已删项。
6. 示例以本地纯函数从名称和角色中识别单位/数学/语文/英语/编程/科学/写作及通用解题/概念讲解；具体功能优先，未知返回空数组。欢迎与空会话都按agent_id取当前定义，切换智能体即时变化；只把预置教学示例显示给学生，不输出原始角色提示词。用户图4固定说明不变。
7. 资料目录给文件列表min-height:160px、flex:1，分类区域限制高度可滚动、其余控件不压缩；目录overflow-y:auto保证低高度可访问，移动端列表扩大到至少160px。显示 .md/.txt 不扩展上传类型。MCP文案泛化而不改变服务授权。
8. OpenAPI新增DELETE /api/agents/{id}（teacher）及DELETE /api/conversations/{id}（student）；历史schema含agent_deleted，消息409描述包含只读与生成中。API版本升0.5.0；测试使用独立夹具并按ID清理，真人互验不代勾。

## Risks / Trade-offs
- 学生持有旧页 → API每次复核，409提示刷新/只读，不依赖UI隐藏。
- 同名重建与迁移 → 先建新唯一约束，旧记录保留原ID；种子只INSERT IGNORE，不改用户配置。
- 生成与删除互斥 → 明确409，先停止/等待后重试；不持全局写锁跨网关请求。
- 示例是规则匹配而非语义生成 → 保守识别、未知隐藏，避免捏造助手功能；不承诺覆盖所有自定义角色。

## Migration Plan
启动幂等新增deleted_at/active_name和索引。既有行均未删除，历史不变。正常Compose重建，不使用down -v；若回滚应用版本，需先解决旧代码会重现软删智能体的问题，不直接回退到忽略deleted_at的旧镜像。
