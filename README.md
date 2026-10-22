# CampusClaw

> 价值：面向中小学的教研智能体，以班级为数据边界管理教研材料，知识库是后续智能能力的底座。
> 场景：教师配置多个智能体、提示词、技能与材料绑定；学生可同时打开多个智能体的流式对话。教师登录后上传、查看、下载本班教研材料；学生登录后查看、下载本班材料；材料正文切分入库后可按班级范围检索与问答，命中可回溯到原文并标注出处；跨班访问在服务端被拒绝。
> 不做：本迭代不做重排序、编排框架（LangChain/LlamaIndex）、作业流程、平台超级管理员、SSO/多租户、注册改密、PDF/Word 解析、生产高可用；不用前端隐藏按钮替代服务端鉴权。

本仓库当前交付：第3课认证授权与入库、第4课可追溯检索，第5课智能体配置、技能路由和并行流式会话，以及第6课自建MCP教学工具、受控多轮调用与审计。

## 快速启动（Docker Compose，唯一发布形态）

前置：已安装 Docker Desktop（含 `docker compose`）。

```bash
cp .env.example .env
# 编辑 .env，至少填写：SESSION_SECRET、MYSQL_PASSWORD、SEED_TEACHER_PASSWORD、SEED_STUDENT_PASSWORD
# SESSION_SECRET、MCP_AUTH_TOKEN、MCP_ENCRYPTION_KEY 分别用 openssl rand -hex 32 生成
# 同时填写课程网关 CHAT_* / EMBEDDING_*，具体字段见 .env.example
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
- 部署：Docker Compose（web/api/db/qdrant/mcp-demo），环境变量经 `.env` 注入（`.env.example` 入库，`.env` 不入库）；Qdrant 不映射宿主端口，网关密钥只在服务端使用

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

教师登录后进入侧栏「智能体配置」和「技能管理」，维护本班智能体的名称、角色提示词、启用状态、绑定技能和绑定材料。技能新建/上传使用独立编辑窗口，已有卡片负责编辑、启停与删除，删除前需确认。技能文件中名称、适用条件、启用必填，空一行后写引导规程；第5课内置工具为 `knowledge_search`，第6课增加已批准的 `tool@server` 引用。启用填写「是」或「否」，名称含「解题引导」的技能要求只引导、不直接给最终答案。教师不提供智能体聊天功能。

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


## 第 6 课：MCP 与工具接入

同仓的 `mcp-server/` 是独立 Go 服务，Compose 名称 `mcp-demo`，只在内部网络监听8090，不映射宿主端口。`GET /health` 检查存活；`POST /mcp` 提供带 Bearer 鉴权的 JSON-RPC 2.0 `initialize`、`notifications/initialized`、`tools/list`、`tools/call`。本课实现2025-03-26的无状态HTTP工具子集，返回JSON（客户端同时接受JSON与SSE响应）；不支持stdio、资源、提示或有状态会话，不能视作任意第三方MCP的通用客户端。`formula_hint` 给去括号/分数/面积的检查方法，`unit_convert` 给长度/质量的单位进率，两者都不替学生算最终得数。

### 环境与首次使用

已有环境升级时，在原 `.env` 保留数据库、会话与课程网关配置，另加以下字段，然后运行 `docker compose up -d --build`，不要重置数据卷。

| 变量 | 用途 |
| --- | --- |
| `MCP_AUTH_TOKEN` | 至少24字符，建议独立运行 `openssl rand -hex 32`；API与自建MCP服务共同使用 |
| `MCP_ENCRYPTION_KEY` | 另行生成的64位十六进制串，用于AES-GCM加密登记令牌；须备份，替换后需重新登记令牌 |
| `MCP_ALLOWED_BASE_URLS` | 逗号分隔的精确Base URL白名单，默认 `http://mcp-demo:8090`；禁止URL凭据、查询、fragment和重定向 |
| `MCP_MAX_ROUNDS` | 默认3，允许1–5 |
| `MCP_MAX_CALLS_PER_TURN` | 默认6，允许1–10 |
| `MCP_MAX_CALLS_PER_CONVERSATION` | 默认30，允许1–1000，包含成功/失败/拒绝的可归属调用 |

令牌与加密密钥缺失或非法时启动失败。MCP令牌独立于课程网关API Key，不能互换。所有部署密钥只从环境注入，禁止写入技能文件、前端或镜像。

1. 教师进入「MCP 工具」→「登记服务器」。名称可用 `campus-tools`，Base URL填 `http://mcp-demo:8090`；此自建地址首次登记令牌可留空，由API读取环境配置。编辑时留空保留原令牌。
2. 点击「连接并发现」，查看两个工具的**完整说明与JSON Schema**，逐个批准只读使用。说明/schema/注解变更后必须重新批准，旧指纹会返回409。重新连接相同工具整体替换缓存，不会翻倍；断开或发现失败会清空缓存。
3. 在「技能管理」新建或编辑技能，从选择器插入已批准工具引用，保存后在智能体配置中绑定该技能。工具名严格小写，引用例如：

```text
名称：MCP数学解题引导
适用条件：方程,去括号,面积,单位,换算,米
工具：knowledge_search,formula_hint@campus-tools,unit_convert@campus-tools
启用：是

先了解学生卡在哪一步。需要公式提示时使用formula_hint，单位进率用unit_convert；只给方法，不计算最终得数。
```

4. 学生选择该智能体新建会话，可问“请先用公式工具给我面积提示，再用单位工具给出5米转厘米的进率。只给方法，不算最终答案。” 模型根据问题决定工具、参数和轮次，具体调用顺序不硬编码。回答区显示工具引用、轮次、成功/被拒/出错与摘要，刷新后从历史恢复。
5. 教师在「最近工具调用」查看本班记录与状态筛选。每条含触发用户、会话、提问消息、轮次和时间。删除服务器保留历史审计；旧技能引用在运行时被拒，不冒充仍有可用工具。

### 调用与安全边界

命中技能后只向模型提供该技能绑定的已发现、已批准、只读且非外发工具，名称由服务器ID映射，模型不能指定任意URL。宿主以发现时同一JSON Schema验证参数，在每次执行前重查班级/连接/授权/指纹，再调用真正的远端 `tools/call`。工具结果脱敏后放在 `role=tool` 数据位，绝不拼入system；已知注入句式整条丢弃。文本检测不能保证发现所有注入，实际硬边界仍为白名单、只读批准、参数校验和限额。

模型可原生多轮提出 `tool_calls`，每轮结果回传后继续决策；默认最多3轮、每问6次、会话累计30次。单次MCP请求8秒，工具阶段45秒，总请求90秒。错误、断开、参数不合法或达到限额后停止新工具动作，用已有资料继续回答。学生停止只取消当前会话，其他会话独立生成。无工具技能保留第5课主路径。

SSE先发送含skill/citations的 `meta`，随后每次 `meta.tool_calls` 仅包含新调用，全部在最终正文的首个 `delta` 之前；前端累加调用而不覆盖原引用。最终回答仍来自课程网关的 `stream=true` 真实增量。消息以 `tool_calls_json` 保存调用状态，中断后保留已获得的工具信息与部分正文。

### 管理接口

以下接口全部要求教师身份，并从服务端会话取班级；学生403，未登录401，跨班与不存在同形404。响应不含令牌，仅 `has_auth`。

| 接口 | 作用 |
| --- | --- |
| `GET/POST /api/mcp/servers` | 本班列表/登记 |
| `GET/PUT/DELETE /api/mcp/servers/{id}` | 详情/修改/删除，修改后需重新连接 |
| `POST /api/mcp/servers/{id}/connect` | 握手和整体替换发现缓存；失败502并清空 |
| `POST /api/mcp/servers/{id}/disconnect` | 断开并清空缓存 |
| `GET /api/mcp/servers/{id}/tools` | 完整工具说明、Schema、注解和批准状态 |
| `POST /api/mcp/servers/{id}/tools/{tool}/approve` | 提交当前 `fingerprint` 批准只读使用 |
| `GET /api/mcp/tool-calls` | 本班最近100条审计，按时间倒序 |

Swagger继续从登录页进入，包含上述可试调接口及SSE增量示例。主库新增 `mcp_servers`、`mcp_tools`、`mcp_tool_reviews`、`mcp_tool_changes`、`mcp_tool_calls`；令牌以AES-GCM随机nonce加密保存，审计不存认证头或密钥。

### 第6课验证

`python3 apitest/run_all.py --live` 同时回归第5课双流并发和第6课真实MCP闭环。新增用例按管理接口URL与方法组织，使用本次运行的临时服务器、教师B账号、技能、智能体和会话，结束后按精确ID清理；测试不会修改已有MCP配置。真实调用使用课程网关额度，模型的具体工具决策不保证固定。脚本模型集成测试另行确定性覆盖两轮、Schema拒绝、越权、错误、注入、取消及三类限额，不能把自动测试当作真人同伴互验。

```bash
# 自建工具服务协议/鉴权/错误与提示边界
docker run --rm -v "$PWD/mcp-server:/src" -w /src golang:1.23-alpine go test ./...
# 后端全部单测/静态检查（本机无Go时）
docker run --rm -v "$PWD/backend:/src" -w /src golang:1.23-alpine sh -c 'go test ./... && go vet ./...'
# 在当前Compose数据库运行真实DB及脚本模型集成测试
docker run --rm --env-file .env -e MCP_INTEGRATION=1 -e TUTOR_INTEGRATION=1 \
  --network internetdemo_default -v "$PWD/backend:/src" -w /src golang:1.23-alpine \
  go test -v ./internal/mcp ./internal/tutor
# 前端增量事件与技能引用插入回归
node --experimental-strip-types frontend/tests/tools.test.mjs
python3 scripts/generate_openapi.py --check
python3 apitest/run_all.py --live
# 暂存拟提交的新文件后，扫描当前部署密钥是否进入源码/产物/镜像/日志
python3 scripts/check_deployment_secrets.py --images
```

详细执行证据见 `openspec/changes/add-lesson6-mcp-tools/verification.md`。真人同伴互验仍需由同伴在同一环境用自己的账号验证隔离、令牌不回传、断开失效和审计范围，并留存请求/响应证据，不能由本机自动用例代勾。


## 智能体与对话管理优化（2026-10-22）

教师「智能体配置」每张卡片新增垃圾桶，与删除技能相同需二次确认。取消无副作用；确认后从配置与学生可选列表移除，解除技能/资料绑定。删除智能体不会抹去学生已经保存的对话：旧记录标记 `agent_deleted=true`，只可阅读或删除，继续提问返回409。允许创建同名的新智能体，旧会话仍指向原ID；启动种子不会复活已删智能体。智能体仍有会话生成时删除返回409，等待生成结束后重试。

学生「最近对话」每行新增独立垃圾桶，和打开对话的按钮分开；确认后删除该对话及消息，并移除打开的标签/面板。取消不发请求，失败保留当前内容并提示。只有本人本班可以删除，同班其他学生也不能删除；教师403，非本人/他班/不存在统一404。生成中先停止或等待结束再删除，服务端与提问共用会话互斥，避免流式落库复活已删消息。已有MCP调用审计保留在教师审计范围内。

| 接口 | 身份 | 成功与主要错误 |
| --- | --- | --- |
| `DELETE /api/agents/{id}` | 本班教师 | 204；学生403；他班/不存在404；生成中409 |
| `DELETE /api/conversations/{id}` | 本人本班学生 | 204；教师403；非本人/他班/不存在404；生成中409 |

MySQL幂等增加 `tutor_agents.deleted_at` 和 `active_name` 生成列，以活动名称唯一索引替换原名称索引；已有智能体均默认为未删除，历史与材料数据不重置。回退应用前需保留删除过滤语义，不能直接部署忽略deleted_at的旧版本。

技能与资料上传按钮显示 `.md/.txt`，上传校验与类型范围保持原样。MCP页简介改为通用的标准协议外部工具接入定义。资料库目录的文件列表桌面至少200px，窄屏至少160px；分类独立滚动，目录在低高度下可整体滚动，教师和学生均可阅读。

学生欢迎页不再显示教师角色提示词原文，改用学习引导；空会话的“写下题目和你已经做过的尝试，助手会帮你找到下一步。”保持不变。示例问题按智能体名称和角色设定保守匹配单位、数学、语文、英语、编程、科学、写作、历史及通用解题/概念讲解等功能，欢迎页与空会话使用相同来源；无法识别时隐藏示例。此方式无需额外模型调用，不能保证理解所有自定义角色；示例点击仅填入，不自动发送。

Swagger版本0.5.0，包含两个DELETE、`Conversation.agent_deleted` 和只读/生成中409说明。验收命令仍为 `python3 apitest/run_all.py --live`，新增删除接口用例与精确ID清理；Go集成测试另行验证正在生成的互斥、种子不复活及幂等迁移。前端回归：`node --experimental-strip-types --test frontend/tests/*.test.mjs`。本次执行结果见 `openspec/changes/refine-agent-conversation-management/verification.md`。
