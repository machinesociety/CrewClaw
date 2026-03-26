# ClawLoops 冻结基线（baseline-v0.12-lightweight-auth）

冻结目标：在 **业务内轻量认证（server-side session + HttpOnly cookie）** 与 **Runtime V1 冻结** 前提下，把字段、错误码与接口边界冻结为单一真相源，避免前后端联调过程中口径漂移。

- **基线版本**：v0.12-lightweight-auth
- **冻结日期**：2026-03-26

## 权威来源（v0.12）

- `docs/后端/API_Spec.md`
- `docs/后端/Lightweight_Auth_Implementation_Guide.md`
- `docs/前端/*`（前端状态机与页面调用流程）

## 单一真相源

本目录内 JSON 冻结物为准（Markdown 仅解释）。

本目录冻结物：

- `enums.json`：枚举唯一真相源
- `errors.json`：错误码注册表（`{ http, code, scope }`）
- `api-boundary.json`：接口边界规则（按 `"METHOD /path"` 粒度冻结）
- `session_user.schema.json`：`SessionUser` JSON Schema
- `auth_me_response.schema.json`：`GET /api/v1/auth/me` 响应体 schema
- `auth_access.schema.json`：`GET /api/v1/auth/access` 响应体 schema
- `auth_options.schema.json`：`GET /api/v1/auth/options` 响应体 schema
- `invitation_preview.schema.json`：invitation 预览响应体 schema
- `invitation_accept.schema.json`：invitation accept 响应体 schema

## v0.12 核心语义冻结

- **不再依赖外部 IAM（Authentik/SSO）**：平台自行承担用户、密码哈希、session、invitation。
- **登录真相 = 平台 session**：前端不读不写 token，不使用 Bearer；所有 API 请求携带 cookie（`credentials: include`）。
- **cookie 名称**：`clawloops_session`（HttpOnly；SameSite=Lax；Path=/；Secure 按环境配置）。
- **`GET /api/v1/auth/access` 永远 200**：仅返回 `{ allowed, reason }` 作状态判断。
- **disabled 语义**：除 `/api/v1/auth/me` 外，disabled 用户访问业务接口统一 `403 USER_DISABLED`；但 `/api/v1/auth/access` 仍返回 200（`allowed=false`）。
- **禁止旧接口**：`POST /api/v1/auth/post-login` 在 v0.12 视为不存在（contract forbid）。

## 兼容性规则

- 允许：新增可选字段 / 新增错误码 / 新增枚举值（不得改变既有语义）。
- 禁止：字段重命名、改变字段语义、把必填变可选、删除字段、改变错误码语义/HTTP 映射。

