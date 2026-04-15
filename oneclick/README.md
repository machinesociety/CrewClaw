# CrewClaw 一键启动（Linux）

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

- 检查 `docker` 和 `docker compose` 是否可用。
- 校验 Docker daemon 是否可访问；若当前用户无权限，会尝试使用 `sudo docker`。
- 若 `infra/compose/.env` 不存在，则从 `.env.example` 创建。
- 校验当前方案必需的配置项：
  - `CLAWLOOPS_DOMAIN`
  - `RUNTIME_PUBLIC_BASE_URL`
  - `RUNTIME_BROWSER_SCHEME`
  - `DASHSCOPE_API_KEY`
- 若检测到可用局域网 IPv4，会给出建议值；选择后会同时更新：
  - `CLAWLOOPS_DOMAIN`
  - `RUNTIME_PUBLIC_BASE_URL`
- 执行 `docker compose up -d --build` 拉起服务。
- 输出与当前 `.env` 一致的访问地址。

## 重要说明

- 脚本不再限制 Ubuntu，也不再自动安装 Docker；请先按你的 Linux 发行版完成 Docker 安装。
- 脚本不会改写你的域名配置，也不会使用 `nip.io`。它会直接沿用 `infra/compose/.env` 中的配置。
- 默认示例配置使用：
  - `CLAWLOOPS_DOMAIN=clawloops.localhost`
  - `RUNTIME_PUBLIC_BASE_URL=http://clawloops.localhost`
- 你必须在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`，否则 LiteLLM 调用 DashScope 会失败。
- Runtime Manager 统一通过主入口路径访问：`http://clawloops.localhost/runtime-manager`。
- OpenClaw 运行时通过路径暴露，访问形如 `http://clawloops.localhost/runtime/<runtimeId>/chat?session=main#token=<OpenClaw token>`。
- 如果你选择了脚本建议的局域网 IP，主站、Runtime Manager 和 OpenClaw 会统一切到该 IP 入口，便于局域网其他设备访问。
- 若浏览器无法解析 `.localhost`，请按 `infra/compose/README.md` 中的说明补充本机 hosts。
