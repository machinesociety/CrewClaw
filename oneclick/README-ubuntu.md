# CrewClaw 一键启动，执行命令后直接躺平等启动！（Ubuntu）

## 用法

## 国内没有VPN用户，需要解决镜像问题

- 如果是国内，没有挂载VPN，则需要在执行一键启动命令前，使用目前可用的镜像站：

```bash
sudo nano /etc/docker/daemon.json


#将上述文档写入以下内容（JSON格式，如果文件不存在则新建）：
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.unsee.tech",
    "https://docker.udayun.com",
    "https://docker.anyhub.us.kg"
  ]
}

```

<br />

- **重启docker服务**：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker

```

<br />

- 使用官方安装脚本库 + 阿里云镜像一键安装 Docker

```bash
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
```


## 如果涉及到 GitLab Runner 权限问题（配置非root用户权限）：
```bash
sudo usermod -aG docker $USER
newgrp docker  # 立即生效（或重新登录）
```
为了保证你的 ClawLoops 一键启动脚本在 GitLab 之后能跑通，我建议你在修改完脚本后，依然要在虚拟机执行一次：
```bash
sudo usermod -aG docker gitlab-runner
```

## 做完上述操作后，即可执行下面A或B方式的一键启动命令，国内一般第一次下载配置等执行会很慢！

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
  - 能访问 `deb.debian.org`/`pypi.org`（构建镜像依赖）。若出现 `pip ... Read timed out`，建议把 `infra/compose/.env` 里的 `API_PIP_INDEX_URL` / `RUNTIME_MANAGER_PIP_INDEX_URL` 改为可用的镜像源（如公司内网 PyPI 镜像、或国内镜像），再重新运行脚本。
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

### 一、 不要盲目的自行安装docker + docker-compose

脚本会自动检测并安装 Docker + Docker Compose plugin（Ubuntu），无需手动安装。
如果自行安装了，请卸载：

1、停止 Docker 服务：

```bash
  sudo systemctl stop docker
  sudo systemctl stop docker.socket
  sudo systemctl stop containerd
```

2、卸载 Docker：

```bash
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras
```

3、清理残留：

```bash
sudo apt-get autoremove -y
```

4、删除 Docker 的残留：

```bash
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm -rf /etc/docker
```

<br />

5、做完之后：

删除损坏的 Docker 记录

```bash
sudo rm -f /etc/apt/sources.list.d/docker.list

sudo rm -f /etc/apt/keyrings/docker.gpg
```

6、清理并重新更新一遍软件列表：

```bash
sudo apt-get clean

sudo apt-get update
```

7、如果没有出现`NO_PUBKEY` 错误

```bash
bash oneclick/start-crewclaw\.sh
```

<br />

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

### 二、docker compose down 提示 network “Resource is still in use”

表示还有容器仍连接在 `clawloops_shared` 网络上（通常是 per-user runtime 容器），无须担心！

### 三、 访问主站返回 404

优先确认：

- Traefik 是否在运行：`docker ps | grep traefik`
- `infra/compose/.env` 里的 `CLAWLOOPS_DOMAIN` 是否与你当前服务器 IP 一致
- `infra/traefik/dynamic/middlewares.yml` 内域名/IP 是否已被更新

### 四、 Runtime 启动失败：network not found

多见于网络被重建后，旧容器仍记录了不存在的 network ID。处理方式通常是删除该 runtime 容器，让系统重建：

```bash
docker ps -a --filter label=clawloops.managed=true
docker rm -f <容器ID>
```

### 五、构建 clawloops-api 时 pip 超时（Read timed out）

现象示例：`ReadTimeoutError ... files.pythonhosted.org ... Read timed out`。通常是目标机器到 PyPI 的下载链路不稳定（即使 `PIP_INDEX_URL=pypi.org`，实际包文件也会从 `files.pythonhosted.org` 拉取）。

处理方式（推荐）：在 `infra/compose/.env` 配置 PyPI 镜像源后重试：

```bash
API_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUNTIME_MANAGER_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

然后重新执行脚本或直接 `docker compose build clawloops-api` 重试。

<br />

若推荐处理方式都无法解决，可尝试以下方法：
搭建VPN连接，确保服务器与公网的网络连接稳定 或者 多点几次！！！

<br />

### 六、当出现下载超时，需要执行

1、重新加载系统的管理配置

```bash
sudo systemctl daemon-reload
```

2、重启 Docker 服务，设置最开始介绍的镜像站：

```bash
sudo systemctl restart docker
```

3、执行重启后，你可以通过以下命令检查配置是否已经载入：

```bash
docker info | grep -A 5 "Registry Mirrors"
```

寻找 **`Registry Mirrors`** 这一行，确认里面显示了你刚刚添加的地址，然后再bash。

## 重要说明（安全）

- 你必须在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`，否则 LiteLLM 调用 DashScope 会返回 500。
- 不要把真实 API Key（例如 DashScope/OpenAI/Anthropic）提交到仓库；建议只在部署机的 `.env` 里配置，并限制文件权限。

### 七、如果想要重起服务，需要在infra/compose文件下

### 基础清理
docker compose down

或者

### 先清本项目
docker compose down --remove-orphans --volumes --rmi all

### 清 BuildKit/构建缓存
docker builder prune -af

