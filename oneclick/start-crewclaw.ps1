try {
    wsl --update --web-download
} catch {
}

# 检查Docker是否可用
Write-Host "正在检查 Docker 是否可用..." -ForegroundColor Cyan
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker 连接失败"
    }
    Write-Host "Docker 连接成功" -ForegroundColor Green
} catch {
    Write-Host "无法连接到 Docker，请检查 Docker Desktop 是否已启动" -ForegroundColor Red
    Write-Host "请按以下步骤操作：" -ForegroundColor Yellow
    Write-Host "1. 打开 Docker Desktop" -ForegroundColor Yellow
    Write-Host "2. 等待 Docker Desktop 完全启动（状态栏显示 Docker is running）" -ForegroundColor Yellow
    Write-Host "3. 重新运行此脚本" -ForegroundColor Yellow
    exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "未找到 Docker 命令，请确保 Docker Desktop 已正确安装" -ForegroundColor Red
    exit 1
}

function Set-OrAppendEnvValue {
    param(
        [string]$FilePath,
        [string]$Key,
        [string]$Value
    )

    $prefix = "$Key="
    $lines = @()
    if (Test-Path $FilePath) {
        $lines = Get-Content $FilePath
    }

    $updated = $false
    $result = foreach ($line in $lines) {
        if ($line -like "$prefix*") {
            $updated = $true
            "$prefix$Value"
        } else {
            $line
        }
    }

    if (-not $updated) {
        $result += "$prefix$Value"
    }

    Set-Content $FilePath -Value $result
}

function Sync-UserFilesPathEnv {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $projectRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
    $userFilesPath = Join-Path $projectRoot "user-files"

    if (-not (Test-Path $userFilesPath)) {
        New-Item -ItemType Directory -Path $userFilesPath -Force | Out-Null
    }

    $windowsPath = (Resolve-Path $userFilesPath).Path
    $composeUserFilesPath = $windowsPath -replace '\\', '/'
    $runtimeUserFilesPath = $composeUserFilesPath

    if ($windowsPath -match '^([A-Za-z]):\\(.*)$') {
        $drive = $matches[1].ToLower()
        $rest = ($matches[2] -replace '\\', '/')
        $runtimeUserFilesPath = "/run/desktop/mnt/host/$drive/$rest"
    }

    $envFile = Join-Path $projectRoot "infra\\compose\\.env"
    Set-OrAppendEnvValue -FilePath $envFile -Key "USER_FILES_HOST_PATH" -Value $composeUserFilesPath
    Set-OrAppendEnvValue -FilePath $envFile -Key "RUNTIME_USER_FILES_HOST_PATH" -Value $runtimeUserFilesPath
}

Sync-UserFilesPathEnv

# 询问用户是否更新OpenClaw镜像
Write-Host "是否需要更新OpenClaw镜像？(Y/N):" -ForegroundColor Cyan
$updateChoice = Read-Host

# 验证用户输入
while ($updateChoice -notmatch '^[YNyn]$') {
    Write-Host "请输入 Y 或 N:" -ForegroundColor Yellow
    $updateChoice = Read-Host
}

# ----------------------------
# 3. 下载工作台镜像
# ----------------------------
$finalTag = "ghcr.io/openclaw/openclaw:latest"

# 直接启动Docker服务（不更新镜像）
function Start-DockerServices {
    Write-Host "直接启动Docker服务，使用现有镜像..." -ForegroundColor Cyan
    
    try {
        # 切换到compose目录
        $composeDir = "infra\compose"
        Set-Location $composeDir
        
        # 构建并启动容器
        Write-Host "构建并启动容器..." -ForegroundColor Cyan
        & docker compose up -d --build
        
        # 切换回项目根目录
        Set-Location ..\..
        
        Write-Host "Docker服务启动成功，使用的是现有版本的镜像" -ForegroundColor Green
    } catch {
        Write-Host "启动Docker服务时出错: $($_.Exception.Message)" -ForegroundColor Red
        # 确保切换回项目根目录
        Set-Location ..\.. -ErrorAction SilentlyContinue
    }
}

# 获取最新版本的openclaw镜像的digest
function Get-LatestOpenClawDigest {
    Write-Host "正在获取最新版本的openclaw镜像信息..." -ForegroundColor Cyan
    try {
        # 方法1：尝试直接拉取latest标签，然后获取其digest
        Write-Host "尝试拉取最新版本的openclaw镜像..." -ForegroundColor Cyan
        # 直接执行docker pull命令，显示原始进度条
        & docker pull ghcr.io/openclaw/openclaw:latest 2>&1
        
        # 检查是否拉取成功
        if ($LASTEXITCODE -eq 0) {
            # 获取镜像的digest
            $imageInfo = docker images ghcr.io/openclaw/openclaw:latest --format "{{.Digest}}"
            if ($imageInfo) {
                Write-Host "获取到最新版本的openclaw镜像digest: $imageInfo" -ForegroundColor Green
                return $imageInfo
            }
        } else {
            Write-Host "拉取镜像时出错" -ForegroundColor Yellow
        }
        
        # 如果无法获取最新版本，使用默认的digest
        Write-Host "无法获取最新版本的openclaw镜像信息，使用默认版本..." -ForegroundColor Yellow
        return "sha256:a5a4c83b773aca8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02"
    } catch {
        Write-Host "获取镜像信息时出错: $($_.Exception.Message)，使用默认版本..." -ForegroundColor Red
        return "sha256:a5a4c83b773aca8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02"
    }
}

# 更新文件中的镜像digest
function Update-ImageDigest {
    param(
        [string]$digest
    )
    
    Write-Host "更新文件中的镜像digest..." -ForegroundColor Cyan
    
    # 确保digest格式正确
    $cleanDigest = $digest -replace '.*(sha256:[a-f0-9]+).*', '$1'
    
    # 更新docker-compose.yml文件
    $dockerComposeFile = "infra\compose\docker-compose.yml"
    if (Test-Path $dockerComposeFile) {
        Write-Host "更新 $dockerComposeFile 文件..." -ForegroundColor Cyan
        $content = Get-Content $dockerComposeFile -Raw
        $newContent = $content -replace 'ghcr\.io/openclaw/openclaw@sha256:[a-f0-9]+', "ghcr.io/openclaw/openclaw@$cleanDigest"
        Set-Content $dockerComposeFile -Value $newContent
        Write-Host "$dockerComposeFile 文件更新成功" -ForegroundColor Green
    } else {
        Write-Host "$dockerComposeFile 文件不存在" -ForegroundColor Red
    }
    
    # 更新settings.py文件
    $settingsFile = "services\runtime-manager\app\core\settings.py"
    if (Test-Path $settingsFile) {
        Write-Host "更新 $settingsFile 文件..." -ForegroundColor Cyan
        $content = Get-Content $settingsFile -Raw
        # 替换任何格式的镜像引用，使用单行格式避免语法错误
        $replacement = 'runtime_openclaw_image_ref: str = "ghcr.io/openclaw/openclaw@' + $cleanDigest + '"'
        $newContent = $content -replace 'runtime_openclaw_image_ref: str = "[^"]+"', $replacement
        $newContent = $newContent -replace 'runtime_openclaw_image_ref: str = \([^)]+\)', $replacement
        Set-Content $settingsFile -Value $newContent
        Write-Host "$settingsFile 文件更新成功" -ForegroundColor Green
    } else {
        Write-Host "$settingsFile 文件不存在" -ForegroundColor Red
    }
}

# 重新构建docker服务
function Rebuild-DockerServices {
    Write-Host "重新构建docker服务..." -ForegroundColor Cyan
    
    try {
        # 切换到compose目录
        $composeDir = "infra\compose"
        Set-Location $composeDir
        
        # 停止并移除旧容器
        Write-Host "停止并移除旧容器..." -ForegroundColor Cyan
        & docker compose down
        
        # 确保使用最新版本的镜像
        Write-Host "确保使用最新版本的镜像..." -ForegroundColor Cyan
        & docker pull ghcr.io/openclaw/openclaw:latest
        
        # 构建并启动新容器
        Write-Host "构建并启动新容器..." -ForegroundColor Cyan
        & docker compose up -d --build
        
        # 切换回项目根目录
        Set-Location ..\..
        
        Write-Host "Docker服务重新构建成功，使用的是最新版本的镜像" -ForegroundColor Green
    } catch {
        Write-Host "重新构建Docker服务时出错: $($_.Exception.Message)" -ForegroundColor Red
        # 确保切换回项目根目录
        Set-Location ..\.. -ErrorAction SilentlyContinue
    }
}

# 根据用户选择执行不同操作
if ($updateChoice -match '^[Yy]$') {
    # 用户选择更新
    # 获取最新版本的镜像digest
    $imageDigest = Get-LatestOpenClawDigest

    # 定义尝试次数
    $maxAttempts = 4

    # 尝试使用原始源下载
    $downloadSuccess = $false
    Write-Host "尝试使用原始源下载..." -ForegroundColor Cyan

    for ($i = 1; $i -le $maxAttempts; $i++) {
        Write-Host "尝试次数: $i/$maxAttempts" -ForegroundColor Cyan
        $startTime = Get-Date
        Write-Host "开始时间: $startTime" -ForegroundColor Cyan
        
        # 直接执行docker pull命令
        & docker pull ghcr.io/openclaw/openclaw:latest 2>&1
        
        # 检查命令执行结果
        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $elapsedTime = $endTime - $startTime
            Write-Host "结束时间: $endTime" -ForegroundColor Cyan
            Write-Host "实际用时: $($elapsedTime.TotalMinutes.ToString('0.00')) 分钟" -ForegroundColor Cyan
            Write-Host "镜像下载成功" -ForegroundColor Green
            $downloadSuccess = $true
            break
        } else {
            $endTime = Get-Date
            $elapsedTime = $endTime - $startTime
            Write-Host "结束时间: $endTime" -ForegroundColor Cyan
            Write-Host "实际用时: $($elapsedTime.TotalMinutes.ToString('0.00')) 分钟" -ForegroundColor Cyan
            Write-Host "镜像下载失败，准备重试..." -ForegroundColor Yellow
        }
    }

    # 如果所有镜像源都失败
    if (-not $downloadSuccess) {
        Write-Host "镜像下载失败，退出脚本" -ForegroundColor Red
        Write-Host "请在 Docker Desktop 的设置中修改 Docker Engine 配置：" -ForegroundColor Yellow
        Write-Host "1. 打开 Docker Desktop"
        Write-Host "2. 点击 Settings"
        Write-Host "3. 点击 Docker Engine"
        Write-Host "4. 将配置修改为：" -ForegroundColor Yellow
        Write-Host '{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.m.daocloud.io"
  ]
}' -ForegroundColor Yellow
        Write-Host "5. 点击 Apply & Restart" -ForegroundColor Yellow
        exit 1
    } else {
        # 更新文件中的镜像digest
        Update-ImageDigest -digest $imageDigest
        
        # 重新构建docker服务
        Rebuild-DockerServices
    }
} else {
    # 用户选择不更新，直接启动服务
    Start-DockerServices
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
