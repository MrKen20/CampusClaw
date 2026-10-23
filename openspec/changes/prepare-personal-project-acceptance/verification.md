# 本地验证记录（2026-10-22）

- 已读取课程 schedule 正文及最终 URL；Safari 实际点击演示站教师、A1、A2、B1 视角，查看应用配置、学生对话与作业示例。演示站明确是 mock；本地验证使用真实课程网关。
- `openspec validate prepare-personal-project-acceptance --strict` 通过，四件套在实现之前建立；本次不归档、不回写长期 specs。
- Docker Go1.23 环境运行 `TUTOR_INTEGRATION=1 MCP_INTEGRATION=1 go test -count=1 ./...`、`go vet ./...` 通过；包括标准 manifest/ZIP 边界、资料适用范围、占位符原文不被再次展开、按班级安装、删除/停用启动拒绝、默认升级保留教师编辑、真实 HTTP trace、截断、并发和本人隔离。
- 前端 `npm run build` 与6组 Node tests 通过。Safari 双角色核对四应用、学生表单展开/真实发送、教师模板只修改草稿、技能包上传格式、会话历史与调用详情。MCP会话155显示两次实际工具调用和4次LLM请求；最终请求/正文/usage/原始SSE可查看。
- Docker api/web 已重建并启动，现有 MySQL/Qdrant/MCP 服务保留。OpenAPI0.6.0：28 paths /40 operations；`generate_openapi.py --check`通过。
- `python3 apitest/run_all.py --live`：34 PASS /0 FAIL /0 SKIP。原 agents 列表测试改为只比较活跃记录；MCP trace 断开测试区分无候选时拒绝调用和正常工具规划。
- `scripts/verify_acceptance_live.py --output output/acceptance-20261022` 完成7组真实网关验证；在收紧内置技能资料适用范围后，定向重跑 reading/writing/review，三者均0条无关引用。JSON是数据证据，不是PDF/验收报告。
- 6个已索引测试切片实际仅4个进入LLM；2个绑定技能只有命中正文出现，未命中正文和资源标记均不存在；无触发时不发送该技能正文。测试夹具按确切ID清理。
- MCP真实调用：`formula_hint(query="矩形面积的公式")`、`unit_convert(value=5,from="m",to="cm")`，3次规划+1次最终流式请求；原始请求中只有批准的工具说明/参数schema，没有MCP URL或令牌。审计与会话保持。
- 原始SSE存在较多非正文事件，一些响应超过128KiB，因此raw前缀明确标记截断；独立delta.content正文、finish_reason和usage仍保存。不可把截断的raw前缀宣称为完整原始流。
- `check_deployment_secrets.py --images`通过，另扫描35个本次新增源文件/JSON证据，未发现环境密钥；不记录鉴权头。只校验了本机结果，正式教师验收与既有待办的人类同学互验仍由实际执行者确认。
- 遵从本次用户指示：无Git提交、无远端更新、无README扩写、无PDF报告、无图片评分或完整作业评分流程。
