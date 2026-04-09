# CrewClaw 一键启动（Ubuntu）

## 用法

### 方式 A：在仓库根目录执行（推荐），其中 /path/to/CrewClaw 表示你的仓库根目录路径。

```bash
cd /path/to/CrewClaw
bash oneclick/start-crewclaw.sh
```

### 方式 B：在任意目录执行（显式指定仓库路径）

```bash
bash /path/to/CrewClaw/oneclick/start-crewclaw.sh /path/to/CrewClaw
```

## 前置条件（重要）

- 操作系统：Ubuntu（脚本在 Ubuntu 22.04/24.04 这类常见版本下最稳；其他 Debian 系也许可用但不保证）。
- 网络要求：
  - 能访问 `download.docker.com`（安装 Docker APT 源与包）
  - 能访问 `deb.debian.org`/`pypi.org`（构建镜像依赖，除非你改成内网镜像源）
  - 使用 `nip.io` 作为域名时，需能解析 `*.nip.io`
- 权限要求：需要 `sudo` 权限（安装包、写入 `/etc/apt/*`、启动 Docker）。
- 端口占用：
  - 默认会启动 Traefik 监听 80（以及 dashboard 8080）；如果 80 已被占用会失败，需要先释放或改 compose 映射。
- 配置要求：必须在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`（脚本会检测为空并中止）。

## 启动后如何访问

- 主站（控制台）：`http://clawloops.<服务器IP>.nip.io`
- Traefik Dashboard：`http://<服务器IP>:8080`

> 注意：当前 OpenClaw Runtime 仍通过“宿主机随机端口”暴露（例如 `:32799`）。如果从公网访问服务器，需要在安全组/防火墙放通对应端口范围，或改造为走 80/443 的反向代理方案。

## 脚本执行逻辑（做了什么）

- 自动检测并安装 Docker + Docker Compose plugin（Ubuntu）。
- 自动启动 Docker 服务并校验可用。
- 自动识别服务器主 IP，并更新 `infra/compose/.env`：
  - `CLAWLOOPS_DOMAIN=clawloops.<IP>.nip.io`
  - `RUNTIME_MANAGER_DOMAIN=runtime-manager.<IP>.nip.io`
  - `RUNTIME_PUBLIC_HOST=<IP>`
- 尝试更新 `infra/traefik/dynamic/middlewares.yml` 中的旧 IP（若存在）。
- 执行 `docker compose up -d --build` 拉起服务。

## 常见问题与排错

### 1) 安装 Docker 时提示 NO\_PUBKEY / GPG 错误

现象示例：`NO_PUBKEY 7EA0A9C3F273FCD8`、`InRelease 没有数字签名`。通常是你的机器：

- 没有 Docker 的 APT keyring
- 或 keyring 文件已损坏（例如下载被代理/劫持返回了 HTML）

处理方式：

```bash
sudo rm -f /etc/apt/keyrings/docker.gpg /etc/apt/keyrings/docker.gpg.tmp
bash oneclick/start-crewclaw.sh /path/to/CrewClaw
```

如果在公司内网/代理环境，确认 `curl https://download.docker.com/linux/ubuntu/gpg` 能获取到正确的 key 内容（并确保系统时间正确，否则签名校验也可能异常）。

### 2) docker compose down 提示 network “Resource is still in use”

表示还有容器仍连接在 `clawloops_shared` 网络上（通常是 per-user runtime 容器），无须担心！


### 3) 访问主站返回 404

优先确认：

- Traefik 是否在运行：`docker ps | grep traefik`
- `infra/compose/.env` 里的 `CLAWLOOPS_DOMAIN` 是否与你当前服务器 IP 一致
- `infra/traefik/dynamic/middlewares.yml` 内域名/IP 是否已被更新

### 4) Runtime 启动失败：network not found

多见于网络被重建后，旧容器仍记录了不存在的 network ID。处理方式通常是删除该 runtime 容器，让系统重建：

```bash
docker ps -a --filter label=clawloops.managed=true
docker rm -f <容器ID>
```

## 重要说明（安全）

- 你必须在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`，否则 LiteLLM 调用 DashScope 会返回 500。
- 不要把真实 API Key（例如 DashScope/OpenAI/Anthropic）提交到仓库；建议只在部署机的 `.env` 里配置，并限制文件权限。

