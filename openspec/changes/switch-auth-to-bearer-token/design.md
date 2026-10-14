# Design: switch-auth-to-bearer-token

## Context

现有实现：登录成功 → `Set-Cookie`（HttpOnly、SameSite=Lax）下发 32 字节随机会话 ID → 中间件从 Cookie 取 ID 查 `sessions` 表（库存 HMAC）。作业要求改为 token + localStorage。本设计回答「token 用什么形态、怎么传、存哪里、安全语义如何不退化」。

## Goals / Non-Goals

- Goals：登录返回 token；前端存 localStorage；请求经 Authorization: Bearer 携带；登出即时失效；既有安全语义（同形失败、限流、HMAC 存储、服务端授权）不退化。
- Non-Goals：JWT、refresh token、多端会话管理、Cookie 双轨。

## Decisions

### D1. Token 形态：沿用「不透明随机串 + 服务端会话行」，不引入 JWT

- 备选 A（采纳）：256-bit crypto/rand 十六进制串，`sessions` 表存其 HMAC-SHA256(SESSION_SECRET)，请求时查表校验。
- 备选 B（否决）：JWT。理由：JWT 签发后无法即时撤销（登出只能等过期或维护吊销列表），与 spec「登出 MUST 立即失效」直接冲突；且签名密钥泄露即全域沦陷。
- 收益：`sessions` 表结构、TTL、撤销、限流逻辑零改动，风险最小；token 不含角色/班级等可读信息，与「不透明」约束一致。

### D2. 传输通道：`Authorization: Bearer <token>`，彻底移除 Cookie

- 登录响应不再 `Set-Cookie`；受保护 API 只认 Authorization 头。
- 显式凭据头避免 Cookie 的 CSRF 面；本机 HTTP 环境下也无需考虑 `Secure` 属性。
- 服务端对「格式不对的头」（缺 Bearer 前缀、空值）与「无效 token」一律 401 同形，不泄露校验细节。

### D3. 前端存储：`localStorage`，键 `campusclaw_token`

- 作业图示要求 token 可在 DevTools → Application → Local Storage 中查看。
- **风险权衡（如实记录）**：localStorage 可被 XSS 读取，抗 XSS 弱于 HttpOnly Cookie。缓解：① localStorage 仅存不透明 token，不存角色/班级等授权判断依据，授权仍每次请求从服务端读取；② 沿用既有前端转义防线（Markdown 渲染转义、不渲染脚本）；③ 401/登出即清除。
- 不用 sessionStorage：需支持「刷新/重开标签页恢复身份」（spec R9）。

### D4. 登录响应：`{token, user}`，user 与 `/api/me` 同构

- 免去登录后立刻再请求一次 `/api/me` 的往返；前端 `onSuccess` 直接拿到授权上下文渲染材料页。

### D5. 防会话固定：登录换发新 Token，旧 Token 作废

- 登录请求若携带旧 Token（Authorization 头），服务端先删其会话行；随后一律换发新 Token。
- 语义与原「登录成功换发会话 ID」一致，仅通道不同。

### D6. 登出：服务端删行 + 前端清 localStorage

- `POST /api/logout` 携带 Bearer 头 → 服务端删除会话行（旧 Token 即时失效）；前端无论响应成败都清除 `campusclaw_token` 并回登录页。

### D7. 401 全局处理

- 前端任一请求收到 401（token 缺失/过期/被撤销）→ 清除 localStorage 中的 token → 跳登录页。与原 Cookie 方案的 401 处理一致，仅多一步清理本地 token。

## Risks / Trade-offs

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| XSS 可窃取 token | localStorage 不受 HttpOnly 保护 | 前端转义防线 + 不存授权信息 + 401/登出即清 |
| token 泄露后至 TTL 前有效 | 与原 Cookie 方案相同 | 登出撤销 + TTL 有限（沿用 `SESSION_TTL`） |
| 用户手改 localStorage | token 换成无效串 | 中间件查表校验，一律 401，无副作用 |

## Migration Plan

1. 一次性切换（无双轨）：后端 Login/Middleware/Logout 同 commit 改为 Token 方案，前端 api.ts 同步改。
2. 已有 `sessions` 数据自然失效（用户重新登录即可），无需数据迁移。
3. README 接口一览同步更新，避免第三方按旧 Cookie 约定集成。

## Open Questions

（无——作业已给定 token + localStorage 的目标形态，其余按最小改动原则取舍。）
