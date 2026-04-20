#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

NON_INTERACTIVE=false
SET_PUBLIC_BASE_URL_MODE=""
REPO_DIR="$DEFAULT_REPO_DIR"
DOCKER_CMD=(docker)

usage() {
  echo "用法：0 [--non-interactive] [--set-public-base-url auto-ip] [repo_dir]"
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
        echo "未知错误：$1"
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
    echo "参数错误：--set-public-base-url 参数只能是 auto-ip"
    exit 1
  fi
}

need_cmd() { command -v "$1" >/dev/null 2>&1; }

require_cmd() {
  local cmd="$1"
  local hint="$2"
  if ! need_cmd "$cmd"; then
    echo "命令不存在：$cmd"
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

  echo "Docker daemon 未运行"
  echo "请检查 Docker 客户端是否已安装，需要 sudo 权限"
  echo "请执行以下命令："
  echo "  - sudo systemctl start docker"
  echo "  - sudo usermod -aG docker \$USER"
  exit 1
}

ensure_compose_available() {
  if ! "${DOCKER_CMD[@]}" compose version >/dev/null 2>&1; then
    echo "Docker Compose 未安装"
    echo "请检查 Docker 客户端是否已安装，需要 sudo 权限"
    echo "请执行以下命令："
    echo "  - sudo systemctl start docker"
    echo "  - sudo usermod -aG docker \$USER"
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
    echo "文件不存在：$example"
    exit 1
  fi

  cp "$example" "$env_file"
  echo "已创建文件：$env_file"
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
  local -a ips=()
  local selected_idx
  local line

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
    echo "已设置 CLAWLOOPS_DOMAIN=${ips[0]}"
    echo "已设置 RUNTIME_PUBLIC_BASE_URL=$suggestion"
    return 0
  fi

  if [[ "$NON_INTERACTIVE" == "true" ]]; then
    return 0
  fi

  echo "请选择一个 IPv4 地址："
  for i in "${!ips[@]}"; do
    printf '  %d) %s\n' "$((i + 1))" "${ips[$i]}"
  done
  echo "当前 CLAWLOOPS_DOMAIN=${current_domain:-<鏈缃?}"
  echo "当前 RUNTIME_MANAGER_DOMAIN=${current_runtime_manager_domain:-<鏈缃?}"
  echo "当前 RUNTIME_BROWSER_SCHEME=${current_scheme:-<鏈缃?}"
  echo "当前 RUNTIME_PUBLIC_BASE_URL=${current_value:-<鏈缃?}"
  echo "建议使用 $suggestion 作为 RUNTIME_PUBLIC_BASE_URL锛岄夋嫨鍚庝細鍚屾椂鏇存NEW鍏ュ彛鍜?Runtime 鍏ュ彛锛夛細"
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
      echo "请设置 $key"
      echo "请在 $env_file"
      exit 1
    fi
  done
}

print_access_summary() {
  local clawloops_domain runtime_manager_domain runtime_public_base_url
  clawloops_domain="$(read_env_value "CLAWLOOPS_DOMAIN")"
  runtime_manager_domain="$(read_env_value "RUNTIME_MANAGER_DOMAIN")"
  runtime_public_base_url="$(read_env_value "RUNTIME_PUBLIC_BASE_URL")"

  echo "访问地址：http://${clawloops_domain}"
  echo "Runtime Manager：http://${runtime_manager_domain}"
  echo "OpenClaw Runtime 示例：http://${runtime_public_base_url}/runtime/<runtimeId>/chat?session=main#token=<OpenClaw token>"
  echo "Traefik Dashboard：http://127.0.0.1:8080"
}

compose_up() {
  local compose_dir="$REPO_DIR/infra/compose"
  (
    cd "$compose_dir"
    "${DOCKER_CMD[@]}" compose up -d --build
  )
}

main() {
  require_cmd "grep" "请安装 grep"
  require_cmd "awk" "请安装 awk"
  require_cmd "docker" "请安装 Docker Engine"

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
  echo "请在 CrewClaw 项目根目录下运行 $0"
  echo "当前目录：$REPO_DIR"
  usage
  exit 1
fi

main "$@"
