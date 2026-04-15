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
    docker pull ghcr.io/openclaw/openclaw@sha256:a5a4c83b773aca85a8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02
} catch {
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
            $envContent[2] = "RUNTIME_ROUTE_HOST_SUFFIX=rt.clawloops.$localIP.nip.io"
            $envContent[3] = "RUNTIME_BROWSER_SCHEME=http"
            Set-Content $envFile -Value $envContent
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
