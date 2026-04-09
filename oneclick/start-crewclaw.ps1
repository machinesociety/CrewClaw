try {
    wsl --update --web-download
} catch {
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    exit 1
}

# ----------------------------
# 3. 下载工作台镜像
# ----------------------------
try {
    Write-Host "尝试使用国内镜像源下载工作台镜像..." -ForegroundColor Cyan
    # 首先尝试使用国内镜像源
    docker pull ghcr.nju.edu.cn/openclaw/openclaw@sha256:a5a4c83b773aca85a8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02
    
    # 如果成功拉取，进行重命名
    docker tag ghcr.nju.edu.cn/openclaw/openclaw@sha256:a5a4c83b773aca85a8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02 ghcr.io/openclaw/openclaw@sha256:a5a4c83b773aca85a8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02
    Write-Host "使用国内镜像源下载成功" -ForegroundColor Green
} catch {
    Write-Host "国内镜像源下载失败，尝试使用原始源..." -ForegroundColor Yellow
    # 如果国内镜像源失败，尝试使用原始源
    try {
        docker pull ghcr.io/openclaw/openclaw@sha256:a5a4c83b773aca85a8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02
        Write-Host "使用原始源下载成功" -ForegroundColor Green
    } catch {
        Write-Host "镜像下载失败，请手动下载镜像" -ForegroundColor Red
        Write-Host "建议：修改 Docker 配置文件，添加国内镜像源" -ForegroundColor Yellow
        Write-Host "Docker 配置文件位置：C:\ProgramData\Docker\config\daemon.json" -ForegroundColor Yellow
        Write-Host "添加以下内容：" -ForegroundColor Yellow
        Write-Host '{"registry-mirrors": ["https://docker.mirrors.ustc.edu.cn", "https://hub-mirror.c.163.com"]}' -ForegroundColor Yellow
    }
}


try {
    # 获取以太网适配器的 IPv4 地址
    # 优先选择 "以太网" 适配器的 IP 地址
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.InterfaceAlias -eq "以太网" -and 
        $_.IPAddress -notlike "169.254.*"
    }).IPAddress | Select-Object -First 1
    
    # 如果没有找到以太网适配器的 IP，再尝试获取 192.168 网段的 IP
    if (-not $localIP) {
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
            $_.InterfaceAlias -ne "Loopback Pseudo-Interface 1" -and 
            $_.IPAddress -notlike "169.254.*" -and
            $_.IPAddress -like "192.168.*"
        }).IPAddress | Select-Object -First 1
    }
    
    # 如果仍然没有找到，再尝试获取其他网段的 IP
    if (-not $localIP) {
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
            $_.InterfaceAlias -ne "Loopback Pseudo-Interface 1" -and 
            $_.IPAddress -notlike "169.254.*"
        }).IPAddress | Select-Object -First 1
    }
    
    if ($localIP) {
        # 1. 更新 .env 文件
        $envFile = "infra\compose\.env"
        if (Test-Path $envFile) {
            $envContent = Get-Content $envFile
            $envContent[0] = "CLAWLOOPS_DOMAIN=clawloops.$localIP.nip.io"
            $envContent[1] = "RUNTIME_MANAGER_DOMAIN=runtime-manager.$localIP.nip.io"
            $envContent[2] = "RUNTIME_PUBLIC_HOST=$localIP"
            Set-Content $envFile -Value $envContent
        }
        
        # 2. 更新 Traefik 动态配置文件
        $traefikConfigFile = "infra\traefik\dynamic\middlewares.yml"
        if (Test-Path $traefikConfigFile) {
            $traefikContent = Get-Content $traefikConfigFile -Raw
            # 替换所有 IPv4 地址格式为本地 IP
            # 匹配 IPv4 地址格式 (xxx.xxx.xxx.xxx)
            $traefikContent = $traefikContent -replace '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', $localIP
            # 替换 $localIP 变量为实际的本地 IP
            $traefikContent = $traefikContent -replace "\$localIP", $localIP
            Set-Content $traefikConfigFile -Value $traefikContent
        }
    }
} catch {
}

# ----------------------------
# 5. 启动服务
# ----------------------------
try {
    # 切换到 compose 目录执行命令
    $composeDir = "infra\compose"
    Set-Location $composeDir
    
    # 执行启动命令
    docker compose up -d
    
    # 切换回项目根目录
    Set-Location ..\..
} catch {
    # 确保切换回项目根目录
    Set-Location ..\.. -ErrorAction SilentlyContinue
    exit 1
}

# ----------------------------
# 6. 显示服务状态
# ----------------------------
try {
    # 切换到 compose 目录执行命令
    $composeDir = "infra\compose"
    Set-Location $composeDir
    
    # 执行状态检查命令
    docker compose ps
    
    # 切换回项目根目录
    Set-Location ..\..
} catch {
    # 确保切换回项目根目录
    Set-Location ..\.. -ErrorAction SilentlyContinue
}

# ----------------------------
# 7. 自动打开浏览器
# ----------------------------
try {
    # 读取更新后的 .env 文件，获取实际的访问地址
    $envFile = "infra\compose\.env"
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        $clawloopsDomain = $envContent[0].Split('=')[1]
        $accessUrl = "http://$clawloopsDomain"
        
        Start-Process $accessUrl
    }
} catch {
}
