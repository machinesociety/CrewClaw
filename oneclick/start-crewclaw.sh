#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

REPO_DIR="${1:-$DEFAULT_REPO_DIR}"
if [[ ! -f "$REPO_DIR/infra/compose/docker-compose.yml" ]]; then
  echo "未找到 CrewClaw 仓库：$REPO_DIR"
  echo "用法：$0 [repo_dir]"
  exit 1
fi

need_cmd() { command -v "$1" >/dev/null 2>&1; }

require_cmd() {
  local cmd="$1"
  local hint="$2"
  if ! need_cmd "$cmd"; then
    echo "缺少命令：$cmd"
    echo "$hint"
    exit 1
  fi
}

sudo_ok() {
  if [[ "$(id -u)" -eq 0 ]]; then
    return 0
  fi
  if ! need_cmd sudo; then
    return 1
  fi
  sudo -n true >/dev/null 2>&1
}

init_docker_cmd() {
  if docker info >/dev/null 2>&1; then
    DOCKER_CMD=(docker)
    return 0
  fi

  if sudo_ok && sudo docker info >/dev/null 2>&1; then
    DOCKER_CMD=(sudo docker)
    return 0
  fi

  echo "Docker daemon 当前不可用。"
  echo "请先确认 Docker 已安装并启动，且当前用户可执行 'docker info'，或允许 sudo 执行 Docker。"
  echo "常见排查："
  echo "  - 启动服务：sudo systemctl start docker"
  echo "  - 加入 docker 组后重新登录：sudo usermod -aG docker \$USER"
  exit 1
}

ensure_compose_available() {
  if ! "${DOCKER_CMD[@]}" compose version >/dev/null 2>&1; then
    echo "当前 Docker 缺少 'docker compose' 插件。"
    echo "请按你的发行版安装 Docker Compose plugin 后重试。"
    exit 1
  fi
}

ensure_env_file() {
  local env_dir="$REPO_DIR/infra/compose"
  local env_file="$env_dir/.env"
  local example="$env_dir/.env.example"

  if [[ -f "$env_file" ]]; then
    return 0
  fi

  if [[ ! -f "$example" ]]; then
    echo "缺少 $env_file，且找不到模板文件 $example"
    exit 1
  fi

  cp "$example" "$env_file"
  echo "已创建默认配置：$env_file"
}

read_env_value() {
  local key="$1"
  local env_file="$REPO_DIR/infra/compose/.env"
  local line

  line="$(grep -E "^${key}=" "$env_file" | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    return 1
  fi

  printf '%s\n' "${line#*=}"
}

validate_env_file() {
  local env_file="$REPO_DIR/infra/compose/.env"
  local required_keys=(
    "CLAWLOOPS_DOMAIN"
    "RUNTIME_MANAGER_DOMAIN"
    "RUNTIME_ROUTE_HOST_SUFFIX"
    "RUNTIME_BROWSER_SCHEME"
    "DASHSCOPE_API_KEY"
  )

  local key value
  for key in "${required_keys[@]}"; do
    value="$(read_env_value "$key" || true)"
    if [[ -z "$value" ]]; then
      echo "配置缺失：$key"
      echo "请编辑 $env_file 后重试。"
      exit 1
    fi
  done
}

print_access_summary() {
  local clawloops_domain runtime_manager_domain runtime_route_suffix runtime_browser_scheme

  clawloops_domain="$(read_env_value "CLAWLOOPS_DOMAIN")"
  runtime_manager_domain="$(read_env_value "RUNTIME_MANAGER_DOMAIN")"
  runtime_route_suffix="$(read_env_value "RUNTIME_ROUTE_HOST_SUFFIX")"
  runtime_browser_scheme="$(read_env_value "RUNTIME_BROWSER_SCHEME")"

  echo "启动完成。"
  echo "主站：http://${clawloops_domain}"
  echo "Runtime Manager：http://${runtime_manager_domain}"
  echo "OpenClaw Runtime 示例：${runtime_browser_scheme}://<runtimeId>.${runtime_route_suffix}/chat?session=main#token=<OpenClaw token>"
  echo "Traefik Dashboard：http://127.0.0.1:8080"

  if [[ "$clawloops_domain" == *.localhost || "$runtime_manager_domain" == *.localhost ]]; then
    echo
    echo "如果浏览器无法解析 .localhost，可在 hosts 中加入："
    echo "127.0.0.1 ${clawloops_domain} ${runtime_manager_domain}"
  fi
}

compose_up() {
  local compose_dir="$REPO_DIR/infra/compose"
  (
    cd "$compose_dir"
    "${DOCKER_CMD[@]}" compose up -d --build
  )
}

main() {
  require_cmd "grep" "请先安装基础文本工具（通常系统默认自带 grep）。"
  require_cmd "docker" "请先安装 Docker Engine。脚本不再自动安装 Docker，以避免发行版耦合。"

  init_docker_cmd
  ensure_compose_available
  ensure_env_file
  validate_env_file
  compose_up
  print_access_summary
}

main "$@"
