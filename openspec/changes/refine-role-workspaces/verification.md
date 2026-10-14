# 工作台改版验收记录

日期：2026-10-14。部署：http://localhost:8080/ 。范围以本 change 的 proposal/design/spec 为准；资料库只做分类阅读，不做个人笔记。

## 自动验收

- `npm --prefix frontend run build`：TypeScript 与 Vite 构建成功。
- `node --experimental-strip-types frontend/tests/auth.test.mjs`：错误登录401保留错误提示，受保护接口401清理会话并触发过期回调。
- `node --experimental-strip-types frontend/tests/library.test.mjs`：标题分类、旧请求失效/卸载失效、Bearer下载正文和401处理通过。
- `node --experimental-strip-types frontend/tests/sse.test.mjs`：UTF-8拆包、CRLF、SSE帧边界、终止事件回归通过。
- `python3 scripts/generate_openapi.py --check`：文档与注册路由/注解一致。
- `openspec validate refine-role-workspaces --strict`：通过。
- `docker compose build api`：镜像内 `go vet ./...`、`go test ./...`、二进制构建均成功，包含 RequireStudent 角色测试。
- `python3 apitest/run_all.py --live`：18 PASS，0 FAIL，0 SKIP。包含响应与数据库断言、教师四会话接口拒绝、两真实流并发、配置下一轮生效和引用/权限检查。报告在被忽略的 `apitest/reports/report-live.html`。
- api、web 已重新构建并启动；MySQL/Qdrant/上传卷保留。

## 原生 Chrome 实际操作与截图走查

- 登录页：分栏品牌布局，账号快捷填充，错误账号显示“账号或密码错误”；未出现“迭代1知识库底座”。不自动保存浏览器口令。
- 教师：默认智能体配置，侧栏只有一处知识问答，无新建聊天/会话入口；技能管理为已有卡片与独立新建窗口。
- 新建临时技能 → 保存 → 停用 → 编辑并重新启用 → 打开删除确认 → 取消：状态与内容正确。再次打开新建，恢复独立默认模板，没有旧ID/内容混入。实际删除通过鉴权API完成，仅删除本轮自己新建的临时技能，并核对其不存在；未删除原有技能。
- 学生会话26/27：Enter发送、两会话并排、独立流式增量；在27生成期间向26发送，两个请求各自处理。点击单独停止，显示“已停止，已生成的内容会保留”。
- 回答出现真实资料编号与摘录，点击引用进入对应科学资料；切回对话仍保留两个面板及内容。刷新后从历史打开26，用户消息、回答和引用恢复。
- 资料：分类目录、正文阅读；快速更换搜索词后显示最新的无匹配结果；清空恢复本班3份资料；下载原文成功，Chrome出现下载完成状态。
- 登录、教师配置、学生欢迎/聊天、资料阅读均检查桌面截图；学生聊天和资料检查深色截图。设备预览明确设为390×844，检查登录、教师卡片、学生会话、资料阅读的浅/深色截图，未观察到页面整体横向溢出。目录/标签使用局部滚动，长正文与移动端页面可以纵向滚动。修复窄屏品牌文案不自然的换行后再次核对。
- 登录页点击 Swagger，最终网址为 `/swagger/`，实际可见 CampusClaw API、认证说明、智能体/技能/会话路由正文。登录后的业务页不提供文档入口。

## 交付边界

分类依据标题关键词，未知归“其他”，未增加正式学科字段或个人笔记。收起会话不删除数据。现有测试/历史记录保留。课程要求的小组同伴互验仍由真实同伴执行，本记录不代替或代勾该步骤；长期主规约与之前待互验的 change 本次未回写/归档。
