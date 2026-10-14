# Change: switch-auth-to-bearer-token

## Why

第 3 课交付（已归档为 `auth-upload` 主力规约）采用「服务端会话 + HttpOnly Cookie」下发会话 ID。本次按课堂作业要求（图示：浏览器开发者工具 → Application → Local Storage 面板中展示 token），将登录认证的凭据传递方式切换为 **Bearer Token**：登录成功后响应体返回不透明 Token，前端存入浏览器 `localStorage`，后续请求经 `Authorization: Bearer <token>` 头携带，服务端校验会话后放行。

服务端会话存储、撤销、限流、bcrypt 口令校验等安全语义**全部保留**——变的只是凭据的「下发通道」（Set-Cookie → 响应体）与「回传通道」（Cookie 头 → Authorization 头）。

## What Changes

- **登录响应返回 Token**：`POST /api/login` 成功时不再 `Set-Cookie`，改为在 JSON 响应体中返回 `{token, user}`；`token` 为 256-bit 随机不透明串，`user` 与 `GET /api/me` 同构。
- **请求凭据改走 Authorization 头**：受保护 API 的中间件从 `Authorization: Bearer <token>` 头解析凭据，查 `sessions` 表校验；不再读取 Cookie。
- **前端 Token 存 localStorage**：登录成功后前端将 token 写入 `localStorage`（键 `campusclaw_token`）；刷新页面从 localStorage 读取 token 并以 `GET /api/me` 恢复身份；收到 401 或登出时清除。
- **登出撤销 Token**：`POST /api/logout` 携带 Bearer 头，服务端删除对应会话行，旧 Token 立即失效；前端同时清除 localStorage。
- **防会话固定语义保留**：登录时若请求携带旧 Token 则一并作废；登录成功一律换发新 Token。
- **不变项**：`sessions` 表结构与 HMAC 存储、会话 TTL、登录失败限流、三类失败响应同形、角色/班级每次请求从服务端读取、跨班同形 404、Docker Compose 拓扑。

## Capabilities

### Modified Capabilities

- `auth-upload`：修订 R1「用户登录与会话」、R2「角色权限」、R3「班级隔离」、R9「最小 Web 界面」中所有涉及 Cookie 的表述，改为 Bearer Token + localStorage 方案；其余 Requirement（上传入库、详情下载、种子数据、密钥管理、Compose 部署、界面体验）不受影响。

## Impact

- 后端：`backend/internal/auth/auth.go`（Login 响应体、Middleware 解析 Authorization 头、Logout 取头删行）。
- 前端：`frontend/src/api.ts`（token 存取 localStorage、fetch/XHR 附 Authorization 头、401 清 token 回登录页）。
- 文档：README「接口一览」更新（登录响应含 token、请求需带 Authorization 头）。
- 无数据库迁移：`sessions` 表结构与数据完全沿用。

## Non-goals（非目标）

- **不引入 JWT / OAuth2 / OIDC**：Token 仍为不透明随机串 + 服务端会话行，保持即时撤销能力；JWT 的无状态签名与「登出立即失效」目标冲突。
- **不做 refresh token 轮换**：单 Token + 服务端 TTL 已满足本课验收。
- **不做 Cookie 双轨兼容**：一次性切换，避免两套凭据并存的攻击面与测试矩阵。
- **不改变服务端授权语义**：角色、班级仍每次请求从服务端读取；localStorage 中只允许存不透明 token，不存角色/班级/任何授权判断依据。
