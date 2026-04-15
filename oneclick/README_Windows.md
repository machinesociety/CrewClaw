# CrewClaw 一键启动（Windows）

## 用法

在仓库目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File oneclick\start-crewclaw.ps1
```

或指定仓库路径：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\path\to\CrewClaw\oneclick\start-crewclaw.ps1" "C:\path\to\CrewClaw"
```

## 脚本做了什么

- 检查 Docker Desktop 是否已安装并运行
- 检查 `docker compose` 是否可用
- 若 `infra/compose/.env` 不存在，则从 `.env.example` 创建
- 校验当前方案必需的配置项：
  - `CLAWLOOPS_DOMAIN`
  - `RUNTIME_PUBLIC_BASE_URL`
  - `RUNTIME_BROWSER_SCHEME`
  - `DASHSCOPE_API_KEY`
- 执行 `docker compose up -d --build` 拉起服务
- 输出与当前 `.env` 一致的访问地址

## 重要说明

1. **需要下载并安装 Docker Desktop**：
   - 从 [Docker 官网](https://www.docker.com/products/docker-desktop/) 下载并安装 Docker Desktop for Windows
   - 安装完成后，确保 Docker Desktop 已启动并运行

2. **配置策略**：
   - 脚本不会改写你的域名配置，也不会使用 `nip.io`
   - 它会直接沿用 `infra/compose/.env` 中的配置
   - 默认示例配置使用：
     ```
     CLAWLOOPS_DOMAIN=clawloops.localhost
     RUNTIME_PUBLIC_BASE_URL=http://clawloops.localhost
     ```

3. **API Key 配置**：
   - 必须在 `infra/compose/.env` 文件中填好 `DASHSCOPE_API_KEY`，否则 LiteLLM 调用 DashScope 会返回 500 错误
   - 示例：
     ```
     DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```

4. **访问方式**：
   - 服务启动后，可以通过 `http://<CLAWLOOPS_DOMAIN>` 访问 CrewClaw
   - Runtime Manager 通过 `http://<CLAWLOOPS_DOMAIN>/runtime-manager` 访问
   - OpenClaw 运行时通过路径暴露，例如 `http://<CLAWLOOPS_DOMAIN>/runtime/<runtimeId>/chat?session=main#token=<OpenClaw token>`

5. **防火墙设置**：
   - 若需要从网络其他设备访问，请确保 Windows 防火墙允许 Docker 相关端口的访问

## 故障排除

- **Docker 未运行**：请确保 Docker Desktop 已启动
- **WSL 错误**：请检查 BIOS 虚拟化设置是否启用，并确保 WSL 已正确安装
- **端口冲突**：若遇到端口冲突，请检查是否有其他服务占用了 80、443 或 8080 端口
- **API Key 错误**：请确保 `DASHSCOPE_API_KEY` 已正确填写且有效
