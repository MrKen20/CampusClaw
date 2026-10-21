# 第6课本机验证记录

日期：2026-10-21。环境：macOS、Docker Compose单实例，保留既有MySQL/Qdrant/上传数据；仅web映射8080。变更为 `add-lesson6-mcp-tools`，未改写 `openspec/specs/` 或归档旧change。

## 依据与范围

已读取并核对最终URL的课程正文：[第6课任务清单](https://devops.hello1023.com/课程任务清单-第6课.html)，以及课件preview/index/scope/mcp-model/binding/bridge/security/audit/apply/think。交互参考为用户截图和课程原型OpenAPI。按课件补充要求采用模型原生多轮tool_calls、只读工具审阅、三类预算与安全数据位；保留不透明Bearer、Go侧班级/角色边界和第5课并行SSE。只做本课HTTP工具子集，不增加作业流程、个人笔记或写入/外发工具。

传输细节核对了[官方HTTP传输规范](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)，JSON Schema库按[固定版本文档](https://pkg.go.dev/github.com/santhosh-tekuri/jsonschema/v5@v5.3.1)使用，禁止外部Schema引用。

## 已执行与结果

| 验证 | 本次结果 |
| --- | --- |
| `openspec validate add-lesson6-mcp-tools --strict` | 通过，proposal/design/delta/tasks齐全 |
| 自建mcp-server Go测试，`-count=1` | TestProtocol、TestHintsOnly通过：401、初始化/通知、发现/调用、非法JSON/方法/参数、提示边界 |
| Compose内独立health/list/call | 实际自建服务health正常，发现formula_hint/unit_convert，调用取得教学提示；缺令牌401，8090未映射宿主 |
| 后端 `go test ./... && go vet ./...` | 全部通过 |
| `MCP_INTEGRATION=1 TUTOR_INTEGRATION=1 go test -count=1 -v ./internal/mcp ./internal/tutor` | 真实MySQL+脚本模型/协议服务测试通过：加密、权限/隔离、发现替换、失败/断开清空、说明变更/旧指纹409、Schema、两轮、错误/注入/越权拒绝、三类预算、取消、并发与原检索回归 |
| 前端TypeScript/Vite构建 | 通过，web镜像已重建运行 |
| 前端auth/library/sse/tools四组回归 | 4 PASS；增量meta累加工具且保留引用/技能，不生成空工具栏；技能引用只修改元数据，不覆盖正文 |
| `python3 scripts/generate_openapi.py --check` | 通过，0.4.0、24路径/34操作；包括10个MCP管理操作、字符串tool路径参数、writeOnly令牌与历史tool_calls |
| Compose启动与API重建 | api/web/db/qdrant/mcp-demo均运行；API重建后原campus-tools登记及审计仍在 |
| `python3 apitest/run_all.py --live` | **28 PASS、0 FAIL、0 SKIP**；前18项回归及新增10项MCP；真实课程网关与自建工具闭环，meta在首delta前，DB/历史与审计匹配，断开与删除旧绑定均明确denied |
| 密钥扫描 `python3 scripts/check_deployment_secrets.py --images` | 对当前部署密钥的精确值扫描通过：tracked/staged源码、frontend/dist、最近5条提交patch、api/web/mcp-demo镜像配置及导出内容、24小时服务日志均无匹配；不扫描运行容器环境（必须运行时注入） |
| 临时API测试夹具清理 | 按本次精确ID删除测试服务器、教师B账号、技能、智能体、会话及测试审计；现有配置与演示配置保留 |

第一次在重建API后立即跑验收时遇到短暂502，导致登录未建立及后续断言连锁失败。runner已增加有界的health等待；完整重跑得到上述28 PASS。没有把第一次失败当成功。

## 真实两轮调用与可演示配置

保留教师A的 `campus-tools`（http://mcp-demo:8090）、获批的formula_hint/unit_convert、技能「MCP数学解题引导」和智能体「MCP数学助手」。学生A会话#36的问题：

> 请先用公式工具给我面积提示，再用单位工具确认5米转厘米的进率。只给方法，不算最终答案。

真实网关依次提出第一轮formula_hint（审计#10）、第二轮unit_convert（审计#11），均ok；随后输出真实delta与done。最终回答给出长×宽和×100进率，没有替学生给出500厘米。meta中的两条记录与消息落库/刷新历史一致。这是一次真实模型结果，其他问题的具体选工具和轮次可能不同，不硬编码该路径。

## 浏览器实测

使用本机Google Chrome原生控制，核对实际本地页面与地址：

- 教师MCP页：服务器卡片、连接/工具数、真实两轮审计、完整工具描述和展开的JSON Schema、技能编辑器的已批准引用选项；桌面与390×844窄屏、浅/深色可阅读，窄屏说明弹窗可滚动。审计表在容器内横向滚动，页面无整体横向溢出。
- 学生页：没有MCP管理入口；打开#36看到两条工具引用、成功状态、轮次与展开摘要；刷新后重新打开记录仍恢复两条调用。390×844深色布局正常，工具记录可滚动读到，无整体横向溢出。设备模拟已退出。
- Swagger实际载入 `http://localhost:8080/swagger/`，显示CampusClaw API 0.4.0及MCP全部接口，connect可展开参数/响应与Try it out；接口实际写入/连接/保存的成功与拒绝路径由上述API脚本验证。
- 不生成用户最终作业截图；页面可供用户自行演示与截图。

## 真人同伴互验（待完成，不由自动测试代勾）

课件要求同伴在**同一环境用自己的账号**验证并留存请求/响应截图或日志。本机临时教师B测试只是自动化预检，不能替代以下真人证据：

- [ ] 服务器/工具隔离：同伴列表看不到你的服务器，直接访问与不存在同形404。
- [ ] 令牌不回传：同伴检查完整列表/详情响应，只有has_auth而无密钥原文。
- [ ] 断开即失效：同伴断开后同技能提问显示denied，记录新增拒绝。
- [ ] 审计范围：同伴只看到自己班级范围，另一班记录不出现。

当前change保留未归档，以便补充真人证据；本次五项代码/文档实现任务均已完成并验证。
