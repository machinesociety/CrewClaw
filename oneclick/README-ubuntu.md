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

- 重启 docker 服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

- 使用官方安装脚本库 + 阿里云镜像一键安装 Docker：

```bash
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
```

## 做完上述操作后，即可执行下面 A 或 B 方式的一键启动命令

### 方式 A：在仓库根目录执行（推荐）

```bash
cd /path/to/CrewClaw
bash oneclick/start-crewclaw.sh
```

### 方式 B：在任意目录执行（显式指定仓库路径）

```bash
bash /path/to/CrewClaw/oneclick/start-crewclaw.sh /path/to/CrewClaw
```

## 前置条件（重要）

- 操作系统：Ubuntu
- 需要能访问 Docker 相关源与构建依赖源
- 需要 `sudo` 权限
- 默认会占用 80 和 8080 端口
- 必须在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`

## 启动后如何访问

- 主站：`http://clawloops.<服务器IP>.nip.io`
- Traefik Dashboard：`http://<服务器IP>:8080`

## 脚本执行逻辑

- 自动检测并安装 Docker + Docker Compose plugin（Ubuntu）
- 自动启动 Docker 服务并校验可用
- 自动识别服务器主 IP，并更新 `infra/compose/.env`
- 尝试更新 `infra/traefik/dynamic/middlewares.yml` 中的旧 IP
- 执行 `docker compose up -d --build` 拉起服务

## 常见问题与排错

### 安装 Docker 时提示 GPG / NO_PUBKEY 错误

```bash
sudo rm -f /etc/apt/keyrings/docker.gpg /etc/apt/keyrings/docker.gpg.tmp
bash oneclick/start-crewclaw.sh /path/to/CrewClaw
```

### 访问主站返回 404

优先确认：

- Traefik 是否在运行
- `infra/compose/.env` 里的 `CLAWLOOPS_DOMAIN` 是否与你当前服务器 IP 一致
- `infra/traefik/dynamic/middlewares.yml` 内域名/IP 是否已被更新

### Runtime 启动失败：network not found

```bash
docker ps -a --filter label=clawloops.managed=true
docker rm -f <容器ID>
```

### 构建 clawloops-api 时 pip 超时

可在 `infra/compose/.env` 配置 PyPI 镜像：

```bash
API_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUNTIME_MANAGER_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```
