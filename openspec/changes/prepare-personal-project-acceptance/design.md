## Decisions

1. 使用现有智能体/会话运行时承载四个任务型应用，服务端 catalog 保存 system/user 模板与表单字段。应用安装按 class_id+seed_key 幂等，只在首次插入时绑定内置技能和本班资料，不覆盖教师修改，也不复活已删除智能体。阅读/写作内置技能限定语文标题资料，错题复盘限定数学标题资料，避免初始科学资料被当作相关依据；只为仍完全等于早期内置原文的技能升级默认值，教师改过的原文不动。写作示例须明确是假设，不能称为用户真实经历。学生启动时服务端验证字段、启停与班级，返回会话及不超过500字的展开提问；用户确认发送后沿用并行 SSE。
2. 教师模板选择复制角色模板到当前智能体草稿，只有保存才生效；学生不通过模板接口修改角色。所有模板具体内容随本轮 system/user 消息进入 LLM。
3. 标准 SKILL.md 支持受限 YAML front matter（name/description 必填，triggers/subject/tools/enabled 可选，单行 scalar/inline list），映射到已有技能路由及说明正文。未指定 triggers 时用 name 和 description 作字面触发词，界面提示显式填写。ZIP 仅允许根目录或单一包目录中的 SKILL.md 与其 resources/references 下的 UTF-8 .md/.txt，拒绝路径穿越、链接、重复文件、嵌套包、二进制、超限；最多16项、解压总量128KiB、单文本32KiB。附件持久化但不自动发送。只在命中且启用的已绑定技能进入执行时加载其完整正文，不能声称正文永不发送。
4. 调用详情通过请求级 context collector 包装真实 HTTP 请求；默认关闭。上限8次调用，每次响应128KiB，明确 truncated；保留 request JSON、response 原始 JSON/SSE、HTTP状态及安全错误；SSE原始前缀可能被网关非正文事件占满，另存实际 delta.content（最多16KiB）、finish_reason 和 usage，正文截断单独标记，不保存 headers、API key 或 MCP token。同轮证据写入 assistant 消息单独 JSON 字段，普通历史仅返回 has_trace。GET trace 接口校验本人/本班/消息归属。并发各自独立，保留原始响应与最终可见回答的区别。
5. 请求参数不改变现有网关契约：最终 stream=true/max_tokens=500/temperature=0.2，工具规划 stream=false/max_tokens=700/tools/tool_choice=auto/parallel_tool_calls=false。知识库最多4个切片，每个800字，历史最近6条每条500字；MCP结果为role=tool数据。

## Verification

单元测试覆盖模板字段展开与长度、manifest/ZIP边界、选中与未选中技能/附件注入区别、HTTP真实数据捕获/截断/并发；集成覆盖角色/班级/本人隔离。真实课程网关验证四应用、知识库命中、技能命中/未命中和 MCP，保存无密钥的请求证据；浏览器核对双角色入口和调用详情。
