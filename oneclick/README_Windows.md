# CrewClaw 一键启动（Windows）

## 用法

1. 使用管理员模式打开 Windows 的 PowerShell
2. 进入项目目录：
   ```powershell
   cd D:\ClawLoops
   ```
3. 运行启动脚本：
   ```powershell
   .\oneclick\start-crewclaw.ps1
   ```

## 脚本做了什么

- 检查 Docker Desktop 是否已安装并运行
- 检查 WSL 服务是否已启用
- 自动识别 Windows 主机的 IP 地址，并更新 `infra/compose/.env`：
  - `CLAWLOOPS_DOMAIN=clawloops.<IP>.nip.io`
  - `RUNTIME_MANAGER_DOMAIN=runtime-manager.<IP>.nip.io`
  - `RUNTIME_PUBLIC_HOST=<IP>`
- 执行 `docker compose up -d --build` 拉起服务

## 重要说明

1. **需要下载并安装 Docker Desktop**：
   - 从 [Docker 官网](https://www.docker.com/products/docker-desktop/) 下载并安装 Docker Desktop for Windows
   - 安装完成后，确保 Docker Desktop 已启动并运行
2. **WSL 服务要求**：
   - Windows 电脑的 BIOS 需要支持硬盘虚拟化（Intel VT-x 或 AMD-V）
   - 需要启用 Windows Subsystem for Linux (WSL)
   
3. **API Key 配置**：
   - 必须在 `infra/compose/.env` 文件中填好 `DASHSCOPE_API_KEY`，否则 LiteLLM 调用 DashScope 会返回 500 错误
   - 示例：
     ```
     DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```
4. **访问方式**：
   - 服务启动后，可以通过 `http://clawloops.<IP>.nip.io` 访问 CrewClaw
   - OpenClaw 运行时通过“宿主机随机端口”暴露（例如 `:32801`）
5. **防火墙设置**：
   - 若需要从网络其他设备访问，请确保 Windows 防火墙允许 Docker 相关端口的访问


## 故障排除

- **Docker 未运行**：请确保 Docker Desktop 已启动
- **WSL 错误**：请检查 BIOS 虚拟化设置是否启用，并确保 WSL 已正确安装
- **端口冲突**：若遇到端口冲突，请检查是否有其他服务占用了 80、443 或 8080 端口
- **API Key 错误**：请确保 `DASHSCOPE_API_KEY` 已正确填写且有效

