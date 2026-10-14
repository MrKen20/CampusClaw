# CampusClaw

> 价值：面向中小学的教研智能体，以班级为数据边界管理教研材料，知识库是后续智能能力的底座。
> 场景：教师配置多个智能体、提示词、技能与材料绑定；学生可同时打开多个智能体的流式对话。教师登录后上传、查看、下载本班教研材料；学生登录后查看、下载本班材料；材料正文切分入库后可按班级范围检索与问答，命中可回溯到原文并标注出处；跨班访问在服务端被拒绝。
> 不做：本迭代不做重排序、编排框架（LangChain/LlamaIndex）、作业流程、平台超级管理员、SSO/多租户、注册改密、PDF/Word 解析、生产高可用；不用前端隐藏按钮替代服务端鉴权。

本仓库当前交付：第3课认证授权与入库、第4课可追溯检索，以及第5课智能体配置、技能路由和并行流式会话。

## 快速启动（Docker Compose，唯一发布形态）

前置：已安装 Docker Desktop（含 `docker compose`）。

```bash
cp .env.example .env
# 编辑 .env，至少填写：SESSION_SECRET、MYSQL_PASSWORD、SEED_TEACHER_PASSWORD、SEED_STUDENT_PASSWORD
# SESSION_SECRET 可用 openssl rand -hex 32 生成
docker compose up --build -d
docker compose ps
```

- 登录页：<http://localhost:8080>（端口冲突时改 `.env` 的 `WEB_PORT`）
- 健康检查：`curl http://localhost:8080/health` → `{"status":"ok"}`（未登录也可访问；只表示进程存活，不查数据库）
- 首次启动 MySQL 初始化需几十秒，期间入口可能短暂 502，属正常现象（api 会重试等待 db 就绪）

### 预置账号（口令来自 .env 的 SEED_* 变量）

| 账号 | 角色 | 班级 |
| --- | --- | --- |
| `teacher_a` | 教师（可上传） | 班级 A |
| `student_a1` | 学生（只读） | 班级 A |
| `student_b1` | 学生（只读） | 班级 B |

两班各有一条标题可区分的种子材料（"A 班种子讲义…" / "B 班种子讲义…"），用于验证班级隔离。

### 数据持久化

数据库与上传文件保存在命名 volume 中：`docker compose down` 后再 `up`（不加 `-v`）数据仍在；`down -v` 会清空数据卷，仅用于主动重置。

## 关键约定

- **单实例部署**：登录限流状态保存在 api 进程内存中，多副本会状态不一致；多副本方案留待后续迭代。
- **跨班返回 404**：访问他班材料详情/文件与"记录不存在"返回完全相同的 404（不用 403，避免暴露资源存在性）；跨班探测只记录到服务端日志。
- **租户标识只取自会话**：请求参数、请求头、表单中的 `class_id` 一律被忽略；上传的数据归属会话所在班级。
- **失败响应同形**：账号不存在、口令错误、登录限流三种情况返回完全一致的响应，不给账号枚举留依据。
- **数据库不出内网**：只有 web 映射宿主端口；db 不映射 3306，api 不单独暴露；api 使用普通数据库账号连接（root 口令由 db 容器随机生成，不下发）。
- **上传目录不静态暴露**：文件只经 `GET /api/materials/{id}/file` 鉴权下载；直接猜 `/uploads/...` 路径取不到文件。

## 技术栈与架构

浏览器 → Nginx（静态资源 + 同源反代 `/api`、`/health`）→ Go（`net/http`，认证/授权/隔离/上传校验/检索问答）→ MySQL 8.0（正文、切片、ngram 全文索引）+ Qdrant（向量，仅内部网络）

- 前端：React 18 + TypeScript + Vite（`frontend/`），React Markdown + Remark GFM
- 后端：Go + 标准库 `net/http`（`backend/cmd/server` + `backend/internal/{config,db,auth,materials,knowledge,chunking,retrieval}`），bcrypt 口令哈希，服务端会话表 + Bearer Token（`Authorization` 头携带、前端存 localStorage，不用 JWT）
- 检索：切片正文与字符区间留 MySQL `knowledge_chunks`；向量存 Qdrant 集合 `campusclaw_chunks`（余弦，维度 2048），点主键与切片 id 一致，payload 仅含五个标识字段（无正文）
- 部署：Docker Compose（web/api/db/qdrant），环境变量经 `.env` 注入（`.env.example` 入库，`.env` 不入库）；Qdrant 不映射宿主端口，网关密钥只在服务端使用

## 接口一览

| 方法与路径 | 鉴权 | 说明 |
| --- | --- | --- |
| `POST /api/login` | 无 | 校验口令、限流、换发 Token；响应体返回 `{token, user}`；三类失败响应同形 |
| `POST /api/logout` | Token | 删除服务端会话行，旧 Token 立即失效（前端同时清除 localStorage） |
| `GET /api/me` | Token | 返回用户、角色、班级 |
| `GET /api/materials` | Token | 本班列表与搜索（`?q=`） |
| `GET /api/materials/{id}` | Token + 本班 | 详情与知识库正文；跨班 404 |
| `GET /api/materials/{id}/file` | Token + 本班 | 下载原文件；跨班 404 |
| `POST /api/materials` | Token + 教师 | 上传 `.txt`/`.md`（multipart，字段名 `file`）；成功后自动按 auto 策略切分并嵌入入库 |
| `POST /api/search` | Token | 本班切片检索；body `{query, mode?}`，mode ∈ keyword / vector / hybrid（默认 hybrid，RRF k=60 融合） |
| `POST /api/ask` | Token | 问答；body `{question, history?}`；先混合检索前 4 条，有命中才调对话网关，`[n]` 与 citations 顺序一致；无命中返回固定文案 |
| `POST /api/materials/{id}/reindex` | Token + 教师 | 按 `auto` / `custom` / `hierarchy` 策略重建该材料索引（先删旧切片与旧向量，幂等）；跨班 404 |
| `GET /health` | 无 | 存活判定，不查库 |

受保护接口统一携带 `Authorization: Bearer <token>` 请求头；Token 为登录响应下发的不透明随机串，前端存储于浏览器 `localStorage`（键 `campusclaw_token`）。

## 规约

本仓库采用 OpenSpec 规约驱动开发（SDD）：活动变更见 `openspec/changes/`，已归档能力规约见 `openspec/specs/`。无规约不写代码，详见 `AGENTS.md`。

## 第 5 课：智能体与并行流式会话

教师登录后进入侧栏「智能体配置」和「技能管理」，维护本班智能体的名称、角色提示词、启用状态、绑定技能和绑定材料。技能新建/上传使用独立编辑窗口，已有卡片负责编辑、启停与删除，删除前需确认。技能文件中名称、适用条件、启用必填，空一行后写引导规程；工具仅允许 `knowledge_search`。启用填写「是」或「否」，名称含「解题引导」的技能要求只引导、不直接给最终答案。教师不提供智能体聊天功能。

学生登录后默认进入「智能体」，选择启用的智能体，点击「新对话」；可以继续选择另一个智能体并新开对话。会话支持标签切换、并排查看、Enter发送和Shift+Enter换行，每个面板各自流式生成、各自停止。收起面板不删除历史，切换到资料库时仍继续生成；点击会话记录可重新打开。刷新页面后从服务器恢复会话列表，点击记录恢复消息。每个会话创建时锁定智能体，教师修改它的配置或绑定从下一轮生效；智能体停用只阻止新建会话，不阻止原会话继续。

每轮只在智能体绑定的材料里检索，且只在绑定并启用的技能里选择至多一项。编号资料放在用户消息中，角色、技能与固定边界放在系统消息中。历史只取最后六条，每条最多500字。引用先随 `meta` 到达，`delta` 是网关生成的真实增量，助手消息保存后返回 `done`；中途失败或停止保留已生成正文并标为 `partial`。同一会话并发请求返回409，不同会话可同时生成。

第5课会话检索无命中时仍按角色作答，引用为空且不伪造编号；第4课 `/api/ask` 保留无命中不调用模型、返回固定文案的行为。认证继续使用不透明 Bearer Token + 服务端会话，不改为参考原型的JWT。

### 接口文档

登录页底部提供 Swagger 接口文档入口，登录后的工作台不显示此入口。打开 <http://localhost:8080/swagger/>，文档 JSON 为 <http://localhost:8080/openapi.json>。通过 `/api/login` 获取 token，在 Swagger 的 Authorize 中只填写 token（不加 `Bearer `），即可试调受保护接口。Swagger 静态资源随 API 镜像打包，不依赖 CDN；第三方资源版本为 swagger-ui-dist 5.33.2，许可证随资源保留。

文档源为处理函数旁的 `// @api {...}` 注解与 `scripts/api_schemas.json`。修改接口后运行：

```bash
python3 scripts/generate_openapi.py
python3 scripts/generate_openapi.py --check
```

新增接口：`GET/POST /api/agents`、`GET/PUT /api/agents/{id}`、`GET/POST /api/skills`、`GET/PUT/DELETE /api/skills/{id}`、`GET/POST /api/conversations`、`GET /api/conversations/{id}`、`POST /api/conversations/{id}/messages`。提示词通过智能体的 `prompt` 字段设置，不使用全班共享的旧 `/api/prompt`。对象跨班/不存在同形404，教师写操作学生403；会话接口仅允许学生且只允许本人访问，教师访问四个会话接口均返回403。

### 分类资料阅读

「资料库」采用分类目录与正文阅读布局，保留搜索、⌘/Ctrl+K、网格浏览和鉴权下载。分类仅依据标题关键词推导，无法识别的归「其他」，不代表数据库已录入正式学科；本次不含个人笔记。正文安全渲染，搜索和详情切换忽略过期响应。前端回归可运行 `node --experimental-strip-types frontend/tests/auth.test.mjs` 与 `node --experimental-strip-types frontend/tests/library.test.mjs`。

### 接口测试

```bash
# 基础API与数据库一致性检查，不调用模型
python3 apitest/run_all.py
# 完整验收：真实课程网关，双流并行、409、技能开关与消息逐字节落库核对
python3 apitest/run_all.py --live
```

脚本按URL与方法组织在 `apitest/cases/`，HTML报告写入 `apitest/reports/report.html`（基础）或 `apitest/reports/report-live.html`（真实网关），已被Git忽略。测试读取本机 `.env`，不打印密钥/令牌；需现有Compose环境。接口验收会创建名称以「接口验收」开头的配置及测试账号下的会话，真实网关测试会使用当日额度。

Go测试覆盖技能解析/路由、上下文窗口、资料边界、SSE帧与流中断。`TUTOR_INTEGRATION=1` 时，在Compose数据库上额外测试绑定过滤、跨班向量回表兜底、两流并发、取消与部分消息持久化；集成测试只清理自己创建的测试行。前端SSE解帧可运行 `node --experimental-strip-types frontend/tests/sse.test.mjs`。

新增表不替换或清空原材料、知识库、会话认证表。复建使用 `docker compose up -d --build`，不要使用 `down -v`。同伴交叉验证需要真人另行记录，自动测试不替代该环节。
