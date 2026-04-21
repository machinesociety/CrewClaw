# CrewClaw 一键启动（Windows）

## 用法

1. 以管理员身份打开 PowerShell
2. 进入项目目录：
   ```powershell
   cd D:\ClawLoops
   ```
3. 运行启动脚本：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\oneclick\start-crewclaw.ps1
   ```

## 脚本会做什么

- 检查 Docker Desktop 是否已安装并运行
- 检查 WSL 是否可用
- **询问用户是否需要更新OpenClaw镜像（Y/N）**
- 自动将 `infra/compose/.env` 设为本地默认值：
  - `CLAWLOOPS_DOMAIN=clawloops.192.168.0.96`
  - `RUNTIME_MANAGER_DOMAIN=runtime-manager.192.168.0.96`
  - `RUNTIME_PUBLIC_HOST=192.168.0.96`
  - `RUNTIME_PUBLIC_BASE_URL=http://192.168.0.96`
  - `RUNTIME_BROWSER_SCHEME=http`
- 执行 `docker compose up -d --build`

## 说明

1. 需要先安装并启动 Docker Desktop
2. 仍然需要在 `infra/compose/.env` 里填好 `DASHSCOPE_API_KEY`
3. **OpenClaw镜像更新选项**：
   - 运行脚本时会询问："是否需要更新OpenClaw镜像？(Y/N)"
   - 选择 **Y**：会检查并下载最新版本的OpenClaw镜像，更新相关配置文件，然后重新构建服务
   - 选择 **N**：会跳过镜像更新，直接使用本地已有的镜像启动服务
4. 启动后默认访问地址是 `http://clawloops.192.168.0.96`
5. Runtime Manager 默认访问地址是 `http://runtime-manager.192.168.0.96`
6. OpenClaw 运行时会通过宿主机随机端口暴露，例如 `http://localhost:32801`

