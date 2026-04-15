$repoDir = if ($args.Count -gt 0) { $args[0] } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$composeDir = Join-Path $repoDir "infra\compose"
$envFile = Join-Path $composeDir ".env"
$envExample = Join-Path $composeDir ".env.example"
$composeFile = Join-Path $composeDir "docker-compose.yml"

if (-not (Test-Path $composeFile)) {
    Write-Error "未找到 CrewClaw 仓库：$repoDir"
    exit 1
}

function Get-EnvValue {
    param (
        [string]$Key
    )

    if (-not (Test-Path $envFile)) {
        return $null
    }

    $line = Get-Content $envFile | Where-Object { $_ -match "^$Key=" } | Select-Object -Last 1
    if (-not $line) {
        return $null
    }

    return $line.Split("=", 2)[1]
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "缺少命令：docker。请先安装并启动 Docker Desktop。"
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-Error "Docker daemon 当前不可用，请先启动 Docker Desktop。"
    exit 1
}

try {
    docker compose version | Out-Null
} catch {
    Write-Error "当前 Docker 缺少 'docker compose'。请确认 Docker Desktop 已正确安装 Compose。"
    exit 1
}

if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $envExample)) {
        Write-Error "缺少 $envFile，且找不到模板文件 $envExample"
        exit 1
    }

    Copy-Item $envExample $envFile
    Write-Host "已创建默认配置：$envFile"
}

$requiredKeys = @(
    "CLAWLOOPS_DOMAIN",
    "RUNTIME_PUBLIC_BASE_URL",
    "RUNTIME_BROWSER_SCHEME",
    "DASHSCOPE_API_KEY"
)

foreach ($key in $requiredKeys) {
    $value = Get-EnvValue -Key $key
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Error "配置缺失：$key。请编辑 $envFile 后重试。"
        exit 1
    }
}

Push-Location $composeDir
try {
    docker compose up -d --build
    docker compose ps
} catch {
    Pop-Location
    throw
}
Pop-Location

$clawloopsDomain = Get-EnvValue -Key "CLAWLOOPS_DOMAIN"
$runtimePublicBaseUrl = Get-EnvValue -Key "RUNTIME_PUBLIC_BASE_URL"

Write-Host ""
Write-Host "启动完成。"
Write-Host "主站：http://$clawloopsDomain"
Write-Host "Runtime Manager：http://$clawloopsDomain/runtime-manager"
Write-Host "OpenClaw Runtime 示例：$runtimePublicBaseUrl/runtime/<runtimeId>/chat?session=main#token=<OpenClaw token>"
Write-Host "Traefik Dashboard：http://127.0.0.1:8080"

try {
    Start-Process "http://$clawloopsDomain" | Out-Null
} catch {
}
