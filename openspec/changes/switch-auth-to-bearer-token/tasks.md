# Tasks: switch-auth-to-bearer-token

## 1. 规约（Propose）

- [ ] 1.1 编写 change 四件套（proposal / design / specs delta / tasks）
  - **verify**: `openspec validate switch-auth-to-bearer-token --strict` 通过；delta 仅含 4 个 MODIFIED Requirement（R1 用户登录与会话、R2 角色权限、R3 班级隔离、R9 最小 Web 界面），无 ADDED/REMOVED。

## 2. 后端：Token 签发与校验

- [ ] 2.1 `Login`：移除 `Set-Cookie`；成功响应改为 `{"token": "<不透明串>", "user": {…与 /api/me 同构…}}`
  - **verify**: `curl -i -X POST /api/login` 成功响应含 `token` 字段且响应头无 `Set-Cookie`；`token` 为 64 位十六进制、不含角色/班级。
- [ ] 2.2 `Middleware`：从 `Authorization: Bearer <token>` 头解析凭据并查 `sessions` 表；缺头、格式错误、无效/过期 Token 一律 401 同形
  - **verify**: `curl /api/me`（无头）→ 401；带有效 token → 200；带 `Bearer 篡改值` → 401；`curl /api/materials`（无头）→ 401 且无任何材料数据。
- [ ] 2.3 `Logout`：从 Authorization 头取 Token 删除会话行（不再操作 Cookie）
  - **verify**: 登录 → 登出 → 旧 Token 请求 `/api/me` → 401。
- [ ] 2.4 防会话固定保留：登录请求携带旧 Token 时先作废再换发新 Token
  - **verify**: 两次连续登录得到不同 token；首次登录携带（Authorization）旧 token 后，旧 token 立即 401。

## 3. 前端：Token 存储与携带

- [ ] 3.1 `api.ts`：新增 `localStorage` 读写（键 `campusclaw_token`）；`request` 与上传 XHR 均附 `Authorization: Bearer` 头
  - **verify**: 浏览器登录后 DevTools → Application → Local Storage 可见 `campusclaw_token`；Network 面板中 `/api/materials` 等请求带 `Authorization` 头。
- [ ] 3.2 `login` 成功存 Token；`logout` 成功与否都清 Token；任一请求 401 时清 Token 并回登录页
  - **verify**: 登录 → 刷新页面身份仍在（/api/me 恢复）；手动篡改 localStorage 中 token 后刷新 → 落在登录页。
- [ ] 3.3 前端构建通过
  - **verify**: `docker compose build web` 成功（或本地 `npm run build`）无 TypeScript 错误。

## 4. 部署与端到端验收

- [ ] 4.1 `docker compose up -d --build` 重建并启动
  - **verify**: `GET /health` 返回 200；登录页可访问。
- [ ] 4.2 端到端 curl 全链路（教师 A 与学生 B1 各一次）
  - **verify**: 登录拿 token → `/api/me` 返回对应角色班级 → 学生带 token 上传 → 403 → 学生请求 B 班外材料 → 列表只含本班。
- [ ] 4.3 浏览器登录并截图 DevTools → Application → Local Storage 面板中的 `campusclaw_token`
  - **verify**: 截图存入 `docs/evidence/`，图中可见 localStorage 键 `campusclaw_token` 与 token 值。

## 5. 文档

- [ ] 5.1 README「接口一览」更新：登录响应含 `token`；受保护接口需带 `Authorization: Bearer` 头；移除 Cookie 相关表述
  - **verify**: 通读 README 无残留 Cookie 会话表述；`.env.example` 无需变更（`SESSION_SECRET`、`SESSION_TTL` 语义不变）。

## 6. 归档（Archive）

- [ ] 6.1 代码与验证全部完成后执行 `openspec archive switch-auth-to-bearer-token`，delta 并入主力规约
  - **verify**: `openspec/specs/auth-upload/spec.md` 中上述 4 个 Requirement 已更新为 Token 表述；change 移入 `changes/archive/`。
