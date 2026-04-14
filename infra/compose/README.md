# CrewClaw 本地 Docker 启动说明

## 前置条件

- 已安装 **Docker** 与 **Docker Compose**（`docker compose` 插件）
- 仓库根目录能成功构建镜像（首次启动会 `--build`）

## 1. 环境变量

在 `infra/compose/` 下复制示例文件并编辑：

```bash
cd infra/compose
cp .env.example .env
# 国内网络可对照 .env.cn.example 调整镜像源
```

| 变量 | 说明 |
|------|------|
| `CLAWLOOPS_DOMAIN` | 主站域名（默认 `clawloops.localhost`），需与 Traefik 路由一致 |
| `RUNTIME_MANAGER_DOMAIN` | Runtime Manager 子域（默认 `runtime-manager.clawloops.localhost`） |
| `RUNTIME_PUBLIC_HOST` | 对外暴露给运行时的主机名（默认 `localhost`） |
| `DASHSCOPE_API_KEY` | 可选：阿里云 DashScope API Key（当使用 `qwen-max-proxy` 等云模型时必填，填写原始 `sk-...` 即可） |
| `OLLAMA_BASE_URL` | 可选：LiteLLM 访问 Ollama 的地址（默认 `http://host.docker.internal:11434`；若启用内置 Ollama 服务请改为 `http://ollama:11434`） |
| `OPENROUTER_API_KEY` | 可选：OpenRouter API Key（当使用 `openrouter-*` 模型时必填） |
| `LITELLM_MASTER_KEY` | API 与 clawloops-api 访问 LiteLLM 的密钥（默认 `sk-local-master`，生产请改掉） |
| `CLAWLOOPS_MODEL_GATEWAY_BASE_URL` | 模型网关地址，Compose 内一般为 `http://litellm:4000` |
| `CLAWLOOPS_MODEL_GATEWAY_DEFAULT_MODELS` | 默认模型名，需与 `litellm.config.yaml` 里 `model_name` 一致（例如 `qwen-max-proxy`、`ollama-qwen2.5-7b-free`、`openrouter-glm-4.5-air-free`） |
| `WEB_NPM_REGISTRY` / `WEB_PNPM_REGISTRY` | 前端构建用 npm 源 |
| `API_APT_MIRROR` / `API_PIP_INDEX_URL` / `RUNTIME_MANAGER_PIP_INDEX_URL` | API 与 runtime-manager 构建时的 Debian / pip 源 |

注意：
- `docker compose` 会优先读取当前 shell 里已导出的同名环境变量；若宿主机上存在旧的 `DASHSCOPE_API_KEY` / `OPENROUTER_API_KEY`，可能覆盖 `infra/compose/.env`。
- DashScope 这里使用原始 Key 即可，不需要写成 `dashscope:sk-...` 这类带 provider 前缀的格式。

## 2. 本机 hosts（使用 `.localhost` 时）

若使用示例里的 `*.localhost` 域名，多数系统已解析到本机；若浏览器无法访问，可在 `/etc/hosts` 增加：

```text
127.0.0.1  clawloops.localhost runtime-manager.clawloops.localhost
```

## 3. 启动哪些容器

在 **`infra/compose/docker-compose.yml`** 中，默认会拉起：

| 服务 | 容器名 | 作用 |
|------|--------|------|
| `traefik` | `crewclaw-traefik` | 反向代理，对外 **80**（HTTP），仪表板 **8080** |
| `clawloops-web` | `crewclaw-web` | 前端 |
| `clawloops-api` | `crewclaw-api` | 后端 API（路径前缀 `/api`） |
| `runtime-manager` | `crewclaw-runtime-manager` | 运行时管理（需挂载 Docker socket） |
| `litellm` | `crewclaw-litellm` | 模型网关（内部 **4000**） |

**不**在默认 `up` 里启动、需显式 profile 的：`prewarm-openclaw`、`prewarm-litellm`（仅镜像预热）、`ollama`（可选本地模型服务）。

## 4. 启动命令

在 **`infra/compose`** 目录执行：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
```

日志：

```bash
docker compose logs -f
```

## 5. 访问方式

- 主站：`http://<CLAWLOOPS_DOMAIN>`（默认 `http://clawloops.localhost`或 `http://192.168.0.103`）
- API：`http://<CLAWLOOPS_DOMAIN>/api/...`
- Runtime Manager：`http://<RUNTIME_MANAGER_DOMAIN>`
- Traefik 仪表板：`http://127.0.0.1:8080`（当前配置为 insecure dashboard）

## 6. 可选：仅预热镜像

```bash
docker compose --profile prewarm pull
```

## 7. 可选：启用内置 Ollama 服务

如果你不想依赖宿主机安装 Ollama，可启用 compose 内置 `ollama` 服务：

1) 在 `.env` 中设置：

```bash
OLLAMA_BASE_URL=http://ollama:11434
CLAWLOOPS_MODEL_GATEWAY_DEFAULT_MODELS=ollama-qwen2.5-7b-free
```

2) 启动（带 `ollama` profile）：

```bash
docker compose --profile ollama up -d --build
```

3) 拉取模型（在 ollama 容器内执行一次）：

官方镜像里服务监听常用 `OLLAMA_HOST=http://0.0.0.0:11434`；在同一容器里跑 `ollama pull` 时，CLI 也会用这个地址去连 API，在部分环境下会失败并只提示 *something went wrong*。显式指向本机回环即可：

```bash
docker compose exec -e OLLAMA_HOST=http://127.0.0.1:11434 ollama ollama pull qwen2.5:7b
```

---

修改模型列表或供应商时，请同步编辑同目录下的 **`litellm.config.yaml`**，并保证所选模型对应的上游可达：
- DashScope 模型：需要 `DASHSCOPE_API_KEY`
- Ollama 本地模型：需要 `OLLAMA_BASE_URL` 可访问（容器内默认指向宿主机 `11434` 端口）
- OpenRouter 模型：需要 `OPENROUTER_API_KEY`
