# 第5课实现与验收记录

日期：2026-10-14（北京时间）。来源：当日重新读取课程 scope、session、skill-model、route、stream、answer、apply、think、任务清单，原型教师界面与已登录课程网关。新增用户要求：学生可同时开启多个普通LLM式对话；本实现为多个独立会话面板，非模型多代理协作。

## 实际运行的检查

| 检查 | 结果与证据 |
|---|---|
| `openspec validate add-multi-agent-streaming-tutor --strict` | 通过 |
| `python3 scripts/generate_openapi.py --check` | 处理器注解与全部24个业务操作一致（17个路径），生成文档无漂移 |
| `docker compose build api web` | 通过；API镜像内执行go vet/go test，Web镜像内执行TypeScript/Vite构建 |
| `node --experimental-strip-types frontend/tests/sse.test.mjs` | 通过：UTF-8逐字节分段、CRLF、帧边界、meta/delta/done |
| `python3 apitest/run_all.py --live` | 18/18通过；HTML位于本机apitest/reports/report-live.html，Git忽略 |
| `go test -race ./internal/tutor ./internal/retrieval` | 在Go1.23容器、现有Compose网络、TUTOR_INTEGRATION=1下通过；测试容器安装gcc/musl-dev以启用race |
| 改动后的Go集成回归 | 通过；包括嵌套/跨delta引用过滤新用例 |
| Docker状态 | web/api/db/qdrant均running；仅web发布8080 |
| 密钥边界 | 活动API Key与SESSION_SECRET不在前端产物、API文档、Git追踪文件；.env被忽略且权限600 |

## 关键行为证据

- 教师写配置；学生403；智能体、绑定资源、技能跨班/不存在同形404；越界绑定拒绝后原配置逐字段不变。
- 学生本人会话可读；同班他人及他班均404；消息体伪造agent_id/class_id/history不改变会话配置。
- 真实网关stream=true：两个不同智能体会话同时返回meta和多次delta；同一会话重复发送409；delta拼接与done消息及数据库HEX(content)逐字节相同。
- 解题引导启用时只提示去括号检查思路；停用后同一会话meta.skill为空、回答转为直接说明规则。智能体停用后原会话继续，但学生列表隐藏且新建404。
- 检索只限本班绑定材料：可控向量服务故意返回未绑定/他班候选，回表仍排除；空绑定直接空检索且继续模型作答，无伪编号。
- 第4课/api/ask以“今天天气怎么样”验证：当前本班检索无命中，返回固定文案和空引用。
- 可控网关中途EOF与客户端取消：已输出片段保存为partial，无完整done；另一会话仍可继续；集成测试仅清理自己创建的临时行。
- 浏览器实际开启解题助手与知识讲解助手两面板，同时显示生成中；“磁铁能吸木块吗”得到科学材料引用，点击引用显示材料原文；刷新后登录态恢复，重新打开两会话可见保存的消息与出处。
- 本地Swagger正常加载；Authorize填不透明Bearer Token后实际执行GET/api/me，得到200与student_a1身份。Swagger令牌不持久化，临时测试令牌已撤销。

## 边界与仍需真人完成的事项

同伴四项交叉验证未完成，不勾选6.3，也不归档change。自动模拟不同账号不是同伴互验。旧第4课与Token变更不在本次归档；长期openspec/specs未改动。

接口测试保留“接口验收”配置与student_a1测试会话，便于复核；未删除原材料/知识库或清空卷。网关BASE_URL与模型信息核对后沿用，当前账户密钥仅写入本机.env，没有重新公开或重置密钥。
