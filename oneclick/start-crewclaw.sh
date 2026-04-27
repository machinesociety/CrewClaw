#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

NON_INTERACTIVE=false
SET_PUBLIC_BASE_URL_MODE=""
REPO_DIR="$DEFAULT_REPO_DIR"

DOCKER_CMD=(docker)
usage() {
  echo "用法：$0 [--non-interactive] [--set-public-base-url auto-ip] [repo_dir]"
}

parse_args() {
  local positional=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --non-interactive)
        NON_INTERACTIVE=true
        shift
        ;;
      --set-public-base-url)
        if [[ $# -lt 2 ]]; then
          echo "参数错误：--set-public-base-url 需要一个参数"
          usage
          exit 1
        fi
        SET_PUBLIC_BASE_URL_MODE="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      --*)
        echo "未知参数：$1"
        usage
        exit 1
        ;;
      *)
        positional+=("$1")
        shift
        ;;
    esac
  done

  if [[ "${#positional[@]}" -gt 1 ]]; then
    echo "参数错误：只能指定一个repo_dir参数"
    usage
    exit 1
  fi
  if [[ "${#positional[@]}" -eq 1 ]]; then
    REPO_DIR="${positional[0]}"
  fi

  if [[ -n "$SET_PUBLIC_BASE_URL_MODE" && "$SET_PUBLIC_BASE_URL_MODE" != "auto-ip" ]]; then
    echo "不支持的 --set-public-base-url 模式：$SET_PUBLIC_BASE_URL_MODE（仅支持 auto-ip）"
    exit 1
  fi
}

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

# sudo_ok() {
#   if [[ "$(id -u)" -eq 0 ]]; then
#     return 0
#   fi
#   if ! need_cmd sudo; then
#     return 1
#   fi
#   sudo -n true >/dev/null 2>&1
# }

# init_docker_cmd() {
#   if docker info >/dev/null 2>&1; then
#     DOCKER_CMD=(docker)
#     return 0
#   fi

#   if sudo_ok && sudo docker info >/dev/null 2>&1; then
#     DOCKER_CMD=(sudo docker)
#     return 0
#   fi

#   echo "Docker daemon 当前不可用。"
#   echo "请先确认 Docker 已安装并启动，且当前用户可执行 'docker info'，或允许 sudo 执行 Docker。"
#   echo "常见排查："
#   echo "  - 启动服务：sudo systemctl start docker"
#   echo "  - 加入 docker 组后重新登录：sudo usermod -aG docker \$USER"
#   exit 1
# }

sudo_ok() {
  # 1. 如果已经是 root，直接 OK
  if [[ "$(id -u)" -eq 0 ]]; then
    return 0
  fi
  
  # 2. 检查是否有 sudo 命令
  if ! need_cmd sudo; then
    return 1
  fi

  # 3. 关键点：使用 -n (non-interactive) 模式测试 sudo
  # 如果不需要密码就能执行，则返回 0
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi

  # 4. 如果是在 CI 等非交互环境下，且 sudo 需要密码，直接返回失败，不再尝试触发交互
  if [[ "$NON_INTERACTIVE" == "true" ]] || [[ ! -t 0 ]]; then
    return 1
  fi

  # 5. 只有在交互模式下才允许 sudo 尝试请求密码
  sudo true >/dev/null 2>&1
}

init_docker_cmd() {
  # 尝试 1: 直接运行 docker
  if docker info >/dev/null 2>&1; then
    DOCKER_CMD=(docker)
    return 0
  fi

  # 尝试 2: 如果直接运行失败，检测当前用户是否在 docker 组但未生效
  if groups | grep -q "\bdocker\b"; then
    echo "警告：当前用户已在 docker 组，但权限未生效。尝试使用 newgrp 运行可能失败，建议重启服务或重新登录。"
  fi

  # 尝试 3: 检查是否可以用免密 sudo 运行
  if sudo_ok; then
    if sudo docker info >/dev/null 2>&1; then
      DOCKER_CMD=(sudo docker)
      return 0
    fi
  fi

  # 自动解决尝试：如果是 CI 环境且失败了，给出针对 GitLab Runner 的修复建议
  echo "----------------------------------------------------"
  echo "错误：Docker 权限不足或服务未启动。"
  if [[ ! -t 0 ]]; then
     echo "检测到正在非交互（CI/CD）环境下运行。"
     echo "请在宿主机执行以下命令修复权限："
     echo "  sudo usermod -aG docker gitlab-runner && sudo systemctl restart gitlab-runner"
     echo "或者配置免密 sudo: 'gitlab-runner ALL=(ALL) NOPASSWD: ALL' 写入 /etc/sudoers"
  fi
  echo "----------------------------------------------------"
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

upsert_env_value() {
  local key="$1"
  local value="$2"
  local env_file="$REPO_DIR/infra/compose/.env"
  local tmp_file
  tmp_file="$(mktemp)"
  awk -v k="$key" -v v="$value" '
    BEGIN { found = 0 }
    $0 ~ ("^" k "=") { print k "=" v; found = 1; next }
    { print }
    END { if (!found) print k "=" v }
  ' "$env_file" >"$tmp_file"
  mv "$tmp_file" "$env_file"
}

collect_ip_candidates() {
  if ! need_cmd ip; then
    return 0
  fi

  local default_ip all_ips
  default_ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1; i<=NF; i++) if ($i=="src") {print $(i+1); exit}}' || true)"
  all_ips="$({
    ip -4 addr show scope global up 2>/dev/null \
      | awk '{
          for (i = 1; i <= NF; i++) {
            if ($i == "inet" && (i + 1) <= NF) {
              split($(i + 1), a, "/")
              print a[1]
            }
          }
        }'
  } || true)"

  if [[ -n "$default_ip" ]]; then
    printf '%s\n' "$default_ip"
  fi
  if [[ -n "$all_ips" ]]; then
    printf '%s\n' "$all_ips"
  fi
}

suggest_runtime_public_base_url() {
  local suggestion current_value current_domain current_runtime_manager_domain current_scheme selected_ip
  local env_file="$REPO_DIR/infra/compose/.env"
  local -a ips=()
  local selected_idx selected_ip
  local i line

  while IFS= read -r line; do
    [[ -n "$line" ]] && ips+=("$line")
  done < <(collect_ip_candidates | awk '!seen[$0]++')

  if [[ "${#ips[@]}" -eq 0 ]]; then
    return 0
  fi

  suggestion="http://${ips[0]}"
  current_value="$(read_env_value "RUNTIME_PUBLIC_BASE_URL" || true)"
  current_domain="$(read_env_value "CLAWLOOPS_DOMAIN" || true)"
  current_runtime_manager_domain="$(read_env_value "RUNTIME_MANAGER_DOMAIN" || true)"
  current_scheme="$(read_env_value "RUNTIME_BROWSER_SCHEME" || true)"

  if [[ "$SET_PUBLIC_BASE_URL_MODE" == "auto-ip" ]]; then
    upsert_env_value "CLAWLOOPS_DOMAIN" "clawloops.${ips[0]}"
    upsert_env_value "RUNTIME_MANAGER_DOMAIN" "runtime-manager.${ips[0]}"
    upsert_env_value "RUNTIME_PUBLIC_HOST" "${ips[0]}"
    upsert_env_value "RUNTIME_BROWSER_SCHEME" "http"
    upsert_env_value "RUNTIME_PUBLIC_BASE_URL" "$suggestion"
    echo "已按 auto-ip 更新 CLAWLOOPS_DOMAIN=clawloops.${ips[0]}"
    echo "已按 auto-ip 更新 RUNTIME_MANAGER_DOMAIN=runtime-manager.${ips[0]}"
    echo "已按 auto-ip 更新 RUNTIME_PUBLIC_HOST=${ips[0]}"
    echo "已按 auto-ip 更新 RUNTIME_PUBLIC_BASE_URL=$suggestion"
    return 0
  fi

  if [[ "$NON_INTERACTIVE" == "true" ]]; then
    return 0
  fi

  echo "检测到本机可用 IPv4（按推荐顺序）："
  for i in "${!ips[@]}"; do
    printf '  %d) %s\n' "$((i + 1))" "${ips[$i]}"
  done
  echo "当前 CLAWLOOPS_DOMAIN=${current_domain:-<未设置>}"
  echo "当前 RUNTIME_MANAGER_DOMAIN=${current_runtime_manager_domain:-<未设置>}"
  echo "当前 RUNTIME_BROWSER_SCHEME=${current_scheme:-<未设置>}"
  echo "当前 RUNTIME_PUBLIC_BASE_URL=${current_value:-<未设置>}"
  echo "建议值：$suggestion"
  while true; do
    echo "输入编号选择 IP（直接回车默认选择 1；选择后会同时更新主站入口和 Runtime 入口）："
    read -r selected_idx
    selected_idx="${selected_idx:-1}"

    if [[ "$selected_idx" == "0" ]]; then
      echo "请选择一个 IPv4 地址：1-${#ips[@]}"
      continue
    fi

    if ! [[ "$selected_idx" =~ ^[0-9]+$ ]] || (( selected_idx < 1 || selected_idx > ${#ips[@]} )); then
      echo "请选择一个 IPv4 地址：1-${#ips[@]}"   
      continue
    fi
    break
  done

  selected_ip="${ips[$((selected_idx - 1))]}"
  upsert_env_value "CLAWLOOPS_DOMAIN" "clawloops.${selected_ip}"
  upsert_env_value "RUNTIME_MANAGER_DOMAIN" "runtime-manager.${selected_ip}"
  upsert_env_value "RUNTIME_PUBLIC_HOST" "${selected_ip}"
  upsert_env_value "RUNTIME_BROWSER_SCHEME" "http"
  upsert_env_value "RUNTIME_PUBLIC_BASE_URL" "http://${selected_ip}"
  echo "已设置 CLAWLOOPS_DOMAIN=clawloops.${selected_ip}"
  echo "已设置 RUNTIME_MANAGER_DOMAIN=runtime-manager.${selected_ip}"
  echo "已设置 RUNTIME_PUBLIC_HOST=${selected_ip}"
  echo "已设置 RUNTIME_PUBLIC_BASE_URL=http://${selected_ip}"
}

validate_env_file() {
  local env_file="$REPO_DIR/infra/compose/.env"
  local required_keys=(
    "CLAWLOOPS_DOMAIN"
    "RUNTIME_PUBLIC_BASE_URL"
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
  local clawloops_domain runtime_manager_domain runtime_public_base_url
  clawloops_domain="$(read_env_value "CLAWLOOPS_DOMAIN")"
  runtime_manager_domain="$(read_env_value "RUNTIME_MANAGER_DOMAIN")"
  runtime_public_base_url="$(read_env_value "RUNTIME_PUBLIC_BASE_URL")"
  echo "启动完成。"
  echo "主站：http://${clawloops_domain}"
  echo "Runtime Manager：http://${runtime_manager_domain}"
  echo "OpenClaw Runtime 示例：${runtime_public_base_url}/runtime/<runtimeId>/chat?session=main#token=<OpenClaw token>"
  echo "Traefik Dashboard：http://127.0.0.1:8080"
  if [[ "$clawloops_domain" == *.localhost ]]; then
    echo
    echo "如果浏览器无法解析 .localhost，可在 hosts 中加入："
    echo "127.0.0.1 ${clawloops_domain}"
  elif [[ "$runtime_public_base_url" != "http://${clawloops_domain}" && "$runtime_public_base_url" != "https://${clawloops_domain}" ]]; then
    echo
    echo "注意：当前主站入口与 Runtime 对外入口不一致。"
    echo "局域网访问时，通常应让 CLAWLOOPS_DOMAIN 与 RUNTIME_PUBLIC_BASE_URL 指向同一台机器。"
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
  require_cmd "awk" "请先安装 awk。"
  require_cmd "docker" "请先安装 Docker Engine。脚本不再自动安装 Docker，以避免发行版耦合。"

  init_docker_cmd
  ensure_compose_available
  ensure_env_file
  suggest_runtime_public_base_url
  validate_env_file
  compose_up
  print_access_summary
}

parse_args "$@"
if [[ ! -f "$REPO_DIR/infra/compose/docker-compose.yml" ]]; then
  echo "未找到 CrewClaw 仓库：$REPO_DIR"
  usage
  exit 1
fi

main "$@"
