#!/usr/bin/env powershell

# CrewClaw 一键启动脚本（Windows版本）

param(
    [string]$RepoPath = $PWD.Path
)

# 设置错误时停止执行
$ErrorActionPreference = "Stop"

Write-Host "=== CrewClaw 一键启动脚本（Windows） ==="
Write-Host ""

# 检查 Docker Desktop 是否已安装并运行
Write-Host "1. 检查 Docker Desktop 状态..."
try {
    $dockerVersion = docker --version
    Write-Host "   ✅ Docker 已安装: $dockerVersion"
    
    # 检查 Docker 服务是否运行
    $dockerInfo = docker info
    Write-Host "   ✅ Docker 服务已运行"
} catch {
    Write-Host "   ❌ Docker 未安装或未运行"
    Write-Host "   请从 https://www.docker.com/products/docker-desktop/ 下载并安装 Docker Desktop for Windows"
    Write-Host "   安装完成后，请启动 Docker Desktop 并再次运行此脚本"
    exit 1
}

# 检查 WSL 服务是否已启用
Write-Host "2. 检查 WSL 服务状态..."
try {
    $wslStatus = wsl --status
    Write-Host "   ✅ WSL 服务已启用"
} catch {
    Write-Host "   ❌ WSL 服务未启用"
    Write-Host "   请运行以下命令启用 WSL:"
    Write-Host "   wsl --install"
    Write-Host "   启用后请重新启动电脑并再次运行此脚本"
    exit 1
}

# 进入仓库目录
Write-Host "3. 进入仓库目录..."
Write-Host "   仓库路径: $RepoPath"
Set-Location -Path $RepoPath

# 自动识别 Windows 主机的 IP 地址
Write-Host "4. 识别主机 IP 地址..."
try {
    $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*", "Wi-Fi*" | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress
    if (-not $ipAddress) {
        $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress
    }
    if (-not $ipAddress) {
        throw "无法识别主机 IP 地址"
    }
    Write-Host "   ✅ 识别到 IP 地址: $ipAddress"
} catch {
    Write-Host "   ❌ 无法识别主机 IP 地址: $($_.Exception.Message)"
    exit 1
}

# 更新 infra/compose/.env 文件
Write-Host "5. 更新配置文件..."
$envFile = "$RepoPath\infra\compose\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    
    # 更新 DOMAIN 配置
    $envContent = $envContent -replace "CLAWLOOPS_DOMAIN=.*", "CLAWLOOPS_DOMAIN=clawloops.$ipAddress.nip.io"
    $envContent = $envContent -replace "RUNTIME_MANAGER_DOMAIN=.*", "RUNTIME_MANAGER_DOMAIN=runtime-manager.$ipAddress.nip.io"
    $envContent = $envContent -replace "RUNTIME_PUBLIC_HOST=.*", "RUNTIME_PUBLIC_HOST=$ipAddress"
    
    Set-Content -Path $envFile -Value $envContent
    Write-Host "   ✅ 已更新 $envFile"
    
    # 检查 DASHSCOPE_API_KEY 是否已配置
    if ($envContent -notmatch "DASHSCOPE_API_KEY=sk-") {
        Write-Host "   ⚠️  警告: DASHSCOPE_API_KEY 未配置"
        Write-Host "   请在 $envFile 文件中添加 DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        Write-Host "   否则 LiteLLM 调用 DashScope 会返回 500 错误"
    } else {
        Write-Host "   ✅ DASHSCOPE_API_KEY 已配置"
    }
} else {
    Write-Host "   ❌ 配置文件不存在: $envFile"
    exit 1
}

# 执行 docker compose 命令
Write-Host "6. 启动服务..."
try {
    Set-Location -Path "$RepoPath\infra\compose"
    Write-Host "   执行: docker compose up -d --build"
    docker compose up -d --build
    Write-Host ""
    Write-Host "   ✅ 服务启动成功!"
    Write-Host ""
    Write-Host "   访问地址: http://clawloops.$ipAddress.nip.io"
    Write-Host ""
} catch {
    Write-Host "   ❌ 服务启动失败: $($_.Exception.Message)"
    exit 1
}

Write-Host "=== 启动完成 ==="