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
$imageDigest = "sha256:a5a4c83b773aca85a8ba99cf155f09afa33946c0aa5cc6a9ccb6162738b5da02"
$finalTag = "ghcr.io/openclaw/openclaw:latest"

# 定义国内镜像源列表
$domesticMirrors = @(
    "ghcr.nju.edu.cn/openclaw/openclaw"
    "docker.mirrors.ustc.edu.cn/openclaw/openclaw"
    "hub-mirror.c.163.com/openclaw/openclaw"
    "mirror.baidubce.com/openclaw/openclaw"
)

# 定义超时时间（30分钟）
$timeoutMinutes = 30
$timeoutMilliseconds = $timeoutMinutes * 60 * 1000  # 转换为毫秒
Write-Host "超时时间设置为: $timeoutMinutes 分钟 ($timeoutMilliseconds 毫秒)" -ForegroundColor Cyan

# 带超时的镜像下载函数
function Download-ImageWithTimeout {
    param(
        [string]$mirror
    )
    
    Write-Host "尝试从镜像源下载: $mirror..." -ForegroundColor Cyan
    $startTime = Get-Date
    Write-Host "开始时间: $startTime" -ForegroundColor Cyan
    
    # 创建临时文件来存储输出
    $tempFile = [System.IO.Path]::GetTempFileName()
    
    try {
        # 创建一个新的PowerShell进程来执行docker pull命令
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList "-Command", "docker pull $mirror@$imageDigest 2>&1 | Out-File -FilePath '$tempFile' -Force" -PassThru -NoNewWindow
        
        # 等待进程完成或超时
        $completed = $process.WaitForExit($timeoutMilliseconds)
        
        $endTime = Get-Date
        $elapsedTime = $endTime - $startTime
        Write-Host "结束时间: $endTime" -ForegroundColor Cyan
        Write-Host "实际用时: $($elapsedTime.TotalMinutes.ToString('0.00')) 分钟" -ForegroundColor Cyan
        
        if (-not $completed) {
            # 超时，终止进程
            $process.Kill()
            Write-Host "下载超时（超过 $timeoutMinutes 分钟），切换到下一个镜像源..." -ForegroundColor Yellow
            return $false
        }
        
        # 读取命令输出
        $output = Get-Content -Path $tempFile -Raw
        
        # 显示命令输出
        Write-Host $output
        
        # 检查命令执行结果
        if ($process.ExitCode -eq 0 -or $output -match "Image is up to date") {
            Write-Host "镜像下载成功" -ForegroundColor Green
            return $true
        } else {
            Write-Host "镜像下载失败，切换到下一个镜像源..." -ForegroundColor Yellow
            return $false
        }
    } finally {
        # 清理临时文件
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        }
    }
}

# 尝试使用国内镜像源
$downloadSuccess = $false
foreach ($mirror in $domesticMirrors) {
    if (Download-ImageWithTimeout -mirror $mirror) {
        # 下载成功，获取镜像ID并进行重命名
        $imageId = docker images -q $mirror@$imageDigest
        if ($imageId) {
            $tagResult = docker tag $imageId $finalTag
            if ($LASTEXITCODE -eq 0) {
                Write-Host "镜像重命名成功" -ForegroundColor Green
                $downloadSuccess = $true
                break
            } else {
                Write-Host "镜像重命名失败，继续尝试下一个镜像源..." -ForegroundColor Yellow
            }
        } else {
            Write-Host "获取镜像ID失败，继续尝试下一个镜像源..." -ForegroundColor Yellow
        }
    }
}

# 如果所有国内镜像源都失败，尝试使用原始源
if (-not $downloadSuccess) {
    Write-Host "所有国内镜像源下载失败，尝试使用原始源..." -ForegroundColor Yellow
    try {
        if (Download-ImageWithTimeout -mirror "ghcr.io/openclaw/openclaw") {
            # 获取镜像ID并创建latest标签
            $imageId = docker images -q ghcr.io/openclaw/openclaw@$imageDigest
            if ($imageId) {
                $finalTag = "ghcr.io/openclaw/openclaw:latest"
                docker tag $imageId $finalTag 2>$null
                $downloadSuccess = $true
            }
        }
    } catch {
        Write-Host "原始源下载失败" -ForegroundColor Red
    }
}

# 如果所有镜像源都失败
if (-not $downloadSuccess) {
    Write-Host "镜像下载失败，请手动下载镜像" -ForegroundColor Red
    Write-Host "建议：修改 Docker 配置文件，添加国内镜像源" -ForegroundColor Yellow
    Write-Host "Docker 配置文件位置：C:\ProgramData\Docker\config\daemon.json" -ForegroundColor Yellow
    Write-Host "添加以下内容：" -ForegroundColor Yellow
    Write-Host '{"registry-mirrors": ["https://docker.mirrors.ustc.edu.cn", "https://hub-mirror.c.163.com", "https://mirror.baidubce.com"]}' -ForegroundColor Yellow
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
