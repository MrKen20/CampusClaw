# auth-upload Specification（Delta：switch-auth-to-bearer-token）

## MODIFIED Requirements

### Requirement: 用户登录与会话

系统 MUST 提供教师（teacher）、学生（student）两类角色的账号密码登录；登录成功 MUST 建立服务端会话并在响应体返回不透明 Token；后续请求 MUST 通过 `Authorization: Bearer <token>` 请求头携带 Token；登出 MUST 立即使对应 Token 失效。

#### Scenario: 登录成功建立服务端会话

- **WHEN** 用户使用有效账号与密码发起登录（预置账号含教师 A、学生 A1、学生 B1）
- **THEN** 登录 MUST 成功并在服务端建立会话行
- **AND** 响应体 JSON MUST 含 `token` 字段，值为不透明随机 ID（不含角色、班级等可读信息）
- **AND** 响应 MUST NOT 通过 `Set-Cookie` 下发任何会话 Cookie
- **AND** `GET /api/me` 携带该 Token（`Authorization: Bearer` 头）时 MUST 返回用户标识、角色与所属班级三项

#### Scenario: Token 存储于 localStorage

- **WHEN** 前端登录成功
- **THEN** 前端 MUST 将 Token 写入浏览器 `localStorage`（键 `campusclaw_token`）
- **AND** `localStorage` 中 MUST NOT 保存角色、班级或其他授权判断依据

#### Scenario: 三类登录失败响应同形

- **WHEN** 用户分别以「账号不存在」「口令错误」「已被登录限流」三种情形发起登录
- **THEN** 三种响应的状态码、响应体文案 MUST 完全一致
- **AND** 响应 MUST NOT 暗示账号是否存在、是否被锁定
- **AND** 三种情形的响应耗时 MUST 相近（对不存在账号也执行等价耗时的哈希比较）

#### Scenario: 登录限流生效

- **WHEN** 同一账号或来源在短时间内连续多次登录失败
- **THEN** 后续登录尝试 MUST 被限流
- **AND** 限流期间的对外响应 MUST 与「口令错误」同形（不返回 429 或差异化文案）

#### Scenario: 登录成功换发会话 ID

- **WHEN** 用户登录成功
- **THEN** 系统 MUST 换发新的 Token（对应新的会话 ID）
- **AND** 登录前持有的旧 Token（若随 `Authorization` 头携带）MUST 作废

#### Scenario: 未登录访问受保护 API

- **WHEN** 未携带有效 Token 的请求访问受保护 API（如 `GET /api/materials`）
- **THEN** 系统 MUST 返回 HTTP 401
- **AND** 响应体 MUST NOT 包含任何本班或他班材料的标题、正文、文件路径或存储键

#### Scenario: 前端收到 401 回登录页

- **WHEN** 前端任一 API 请求收到 401
- **THEN** 前端 MUST 清除 `localStorage` 中的 Token 并跳转登录页

#### Scenario: 登出后旧 Cookie 立即失效

- **WHEN** 已登录用户携带有效 Token（`Authorization: Bearer` 头）调用 `POST /api/logout`
- **THEN** 服务端 MUST 删除对应会话行，前端 MUST 清除 `localStorage` 中的 Token
- **AND** 此后携带旧 Token 请求受保护 API MUST 返回 401

### Requirement: 角色权限

系统 MUST 按服务端会话中的角色授权：教师可上传、查看、下载本班材料；学生只能查看、下载；角色 MUST 每次请求从服务端读取，MUST NOT 采信客户端声明；客户端存储中仅允许保存不透明 Token，MUST NOT 保存角色等授权判断依据。

#### Scenario: 学生上传被拒绝且无副作用

- **WHEN** 以学生（如学生 A1）有效 Token 向 `POST /api/materials` 提交文件
- **THEN** 系统 MUST 返回 HTTP 403
- **AND** `materials` 与 `knowledge_entries` 表行数 MUST 与请求前相同
- **AND** 上传目录 MUST 无因该请求产生的新文件

#### Scenario: 教师上传被允许

- **WHEN** 以教师（如教师 A）有效 Token 向 `POST /api/materials` 提交合法文件
- **THEN** 系统 MUST 接受请求并完成入库（见「材料上传与知识库入库」）
- **AND** MUST 返回成功（如 HTTP 201）并含新材料标识

#### Scenario: 上传入口依据 /api/me 显示

- **WHEN** 前端渲染材料页
- **THEN** 上传入口 MUST 依据 `GET /api/me` 返回的角色决定是否显示
- **AND** MUST NOT 依据 localStorage 等客户端存储中的角色（客户端存储仅保存不透明 Token）

#### Scenario: 客户端角色声明无效

- **WHEN** 请求在请求体或请求头中携带与会话不一致的 `role` 字段
- **THEN** 系统 MUST 忽略该字段
- **AND** 授权结果 MUST 与不带该字段时一致

#### Scenario: 学生只读本班材料

- **WHEN** 学生 A1 登录后访问本班材料列表与详情
- **THEN** 系统 MUST 正常返回本班可读材料
- **AND** 学生对本班材料的一切写操作（上传、修改、删除）在服务端 MUST 被拒绝

### Requirement: 班级隔离

班级是数据边界。所有材料、知识库查询 MUST 在服务端按会话班级过滤；跨班按 ID 访问 MUST 返回与「记录不存在」完全同形的 404；前端隐藏入口 MUST NOT 作为满足本要求的手段。

#### Scenario: 跨班按 ID 访问返回同形 404

- **WHEN** 班级 A 用户（教师 A 或学生 A1）通过路径参数访问 B 班某材料的详情（`GET /api/materials/{id}`）或文件（`GET /api/materials/{id}/file`）
- **THEN** 系统 MUST 返回 HTTP 404
- **AND** 该响应 MUST 与访问「不存在的 ID」时的响应在状态码与响应体上完全一致
- **AND** 响应 MUST NOT 包含 B 班材料的标题、正文片段、文件路径或存储键

#### Scenario: 列表班级条件只取自会话

- **WHEN** 已登录用户请求 `GET /api/materials` 并在查询参数中携带其他班级的 `class_id`
- **THEN** 系统 MUST 忽略请求中的班级参数
- **AND** 返回结果 MUST 与不带该参数时完全一致

#### Scenario: 列表数据来自按班级过滤的数据库查询

- **WHEN** 教师 A 登录后请求材料列表（含合法搜索关键词）
- **THEN** 返回集合中每条记录 MUST 归属班级 A
- **AND** 数据 MUST 来自带班级过滤条件的数据库查询，MUST NOT 为硬编码演示条目
- **AND** 清空材料表后列表 MUST 为空

#### Scenario: 上传归属会话班级

- **WHEN** 教师 A 上传文件时在表单中携带其他班级字段（如 `class_id=B`）
- **THEN** 新记录 MUST 归属会话所在班级 A
- **AND** 表单中的班级字段 MUST NOT 改变数据归属

#### Scenario: 绕过前端仍被服务端拒绝

- **WHEN** 使用 curl 等工具携带有效 Token（`Authorization: Bearer` 头）直接构造跨班或越权请求（不经前端页面）
- **THEN** 服务端 MUST 按上述各 Scenario 拒绝
- **AND** 拒绝行为 MUST NOT 依赖前端路由守卫或入口隐藏

### Requirement: 最小 Web 界面

系统 MUST 提供登录页与材料页两个页面；登录成功后 Token MUST 存储于浏览器 `localStorage`；身份以 `/api/me` 为唯一依据；Markdown 渲染 MUST 转义防脚本。

#### Scenario: 登录页与材料页可达

- **WHEN** 用户访问应用
- **THEN** 未登录 MUST 落在登录页；登录成功 MUST 进入材料页
- **AND** 材料页 MUST 展示本班材料列表

#### Scenario: 刷新后以 /api/me 恢复身份

- **WHEN** 已登录用户刷新页面或重开标签页
- **THEN** 前端 MUST 从 `localStorage` 读取 Token 并携带其请求 `GET /api/me` 重新确认身份
- **AND** Token 缺失、无效或已过期时 MUST 落在登录页
- **AND** 上传入口、班级信息 MUST 以该响应为准

#### Scenario: 上传入口随角色变化

- **WHEN** 学生与教师分别登录查看材料页
- **THEN** 教师 MUST 看到上传入口
- **AND** 学生 MUST NOT 看到上传入口（但服务端拒绝不依赖此隐藏）

#### Scenario: 材料正文安全渲染

- **WHEN** 材料 Markdown 正文含 `<script>` 等注入内容
- **THEN** 前端 MUST 按渲染库默认转义策略展示
- **AND** 材料中的脚本 MUST NOT 被执行

#### Scenario: 本班搜索范围受限

- **WHEN** 用户在材料页使用搜索
- **THEN** 搜索 MUST 仅在本班材料范围内过滤标题或正文
- **AND** 用 B 班材料标题在 A 班搜索 MUST 无结果
