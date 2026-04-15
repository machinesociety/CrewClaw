# CrewClaw 一键启动（Ubuntu）

## 用法

在仓库目录执行：

```bash
bash oneclick/start-crewclaw.sh
```

或指定仓库路径：

```bash
bash /path/to/CrewClaw/oneclick/start-crewclaw.sh /path/to/CrewClaw
```

## 脚本做了什么

- 自动检测并安装 Docker + Docker Compose plugin（Ubuntu）。
- 自动启动 Docker 服务并校验可用。
- 自动识别服务器主 IP，并更新 `infra/compose/.env`：
  - `CLAWLOOPS_DOMAIN=clawloops.<IP>.nip.io`
  - `RUNTIME_MANAGER_DOMAIN=runtime-manager.<IP>.nip.io`
  - `RUNTIME_ROUTE_HOST_SUFFIX=rt.clawloops.<IP>.nip.io`
  - `RUNTIME_BROWSER_SCHEME=http`
- 尝试更新 `infra/traefik/dynamic/middlewares.yml` 中的旧 IP（若存在）。
- 执行 `docker compose up -d --build` 拉起服务。

## 重要说明

- 你必须在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`，否则 LiteLLM 调用 DashScope 会返回 500。
- OpenClaw 运行时通过子域名暴露（例如 `http://rt-u-123.rt.clawloops.<IP>.nip.io`），由 Traefik 统一走 80/443 入口。
