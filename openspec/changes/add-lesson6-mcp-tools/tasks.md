## 1. 自建服务
- [x] 1.1 实现mcp-server/、两只读提示工具、协议鉴权与Compose/env；verify: Go单测+容器health/list/call/401/错误JSON，密钥不入镜像。
## 2. 管理、存储与绑定
- [ ] 2.1 MCP存储/加密、网络白名单、发现与批准、技能引用/权限校验；verify: Go单测和MySQL集成，CRUD/隔离/清空缓存/重连替换/说明变更/参数Schema/令牌不回传。
## 3. 对话编排
- [ ] 3.1 模型原生工具循环/三类限额/安全结果/审计/SSE及历史；verify: 脚本模型两轮、越权/参数/出错/取消/上限集成测试，第5课回归及真实网关调用。
## 4. 界面
- [ ] 4.1 教师MCP服务器/工具批准/审计与技能引用选择、学生工具状态；verify: 前端构建与SSE状态回归，真实浏览器桌面/390px、深浅色操作和刷新。
## 5. 文档与验收
- [ ] 5.1 OpenAPI/Swagger、URL组织apitest、部署README与证据；verify: OpenAPI --check、Compose全启动、apitest --live全部通过、密钥扫描；留真实同伴互验项未代勾。
