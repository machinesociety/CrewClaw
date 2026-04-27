#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$DEFAULT_REPO_DIR"

SET_PUBLIC_BASE_URL_MODE="auto-ip"
MIRROR_MODE="auto"
PROXY_MODE="auto"

usage() {
  echo "用法：$0 [--set-public-base-url auto-ip|keep] [--mirror-mode auto|keep] [--proxy-mode auto|keep|off] [repo_dir]"
}

parse_args() {
  local positional=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --set-public-base-url)
        if [[ $# -lt 2 ]]; then
          echo "参数错误：--set-public-base-url 需要一个值。"
          usage
          exit 1
        fi
        SET_PUBLIC_BASE_URL_MODE="$2"
        shift 2
        ;;
      --mirror-mode)
        if [[ $# -lt 2 ]]; then
          echo "参数错误：--mirror-mode 需要一个值。"
          usage
          exit 1
        fi
        MIRROR_MODE="$2"
        shift 2
        ;;
      --proxy-mode)
        if [[ $# -lt 2 ]]; then
          echo "参数错误：--proxy-mode 需要一个值。"
          usage
          exit 1
        fi
        PROXY_MODE="$2"
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
    echo "参数错误：仅支持一个 repo_dir。"
    usage
    exit 1
  fi
  if [[ "${#positional[@]}" -eq 1 ]]; then
    REPO_DIR="${positional[0]}"
  fi

  if [[ "$SET_PUBLIC_BASE_URL_MODE" != "auto-ip" && "$SET_PUBLIC_BASE_URL_MODE" != "keep" ]]; then
    echo "不支持的 --set-public-base-url 模式：$SET_PUBLIC_BASE_URL_MODE（仅支持 auto-ip 或 keep）"
    exit 1
  fi

  if [[ "$MIRROR_MODE" != "auto" && "$MIRROR_MODE" != "keep" ]]; then
    echo "不支持的 --mirror-mode 模式：$MIRROR_MODE（仅支持 auto 或 keep）"
    exit 1
  fi

  if [[ "$PROXY_MODE" != "auto" && "$PROXY_MODE" != "keep" && "$PROXY_MODE" != "off" ]]; then
    echo "不支持的 --proxy-mode 模式：$PROXY_MODE（仅支持 auto/keep/off）"
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

  echo "错误：Docker daemon 当前不可用或权限不足。"
  echo "请确保 CI 运行环境可执行 docker（或允许 sudo -n docker）。"
  exit 1
}

ensure_compose_available() {
  if ! "${DOCKER_CMD[@]}" compose version >/dev/null 2>&1; then
    echo "错误：当前 Docker 缺少 'docker compose' 插件。"
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
    echo "错误：缺少 $env_file，且找不到模板文件 $example"
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

detect_default_ip() {
  if ! need_cmd ip; then
    return 1
  fi
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1; i<=NF; i++) if ($i=="src") {print $(i+1); exit}}'
}

apply_public_base_url() {
  if [[ "$SET_PUBLIC_BASE_URL_MODE" == "keep" ]]; then
    return 0
  fi

  local forced_ip="${FORCE_PUBLIC_IP:-}"
  local detected_ip=""

  if [[ -z "$forced_ip" ]]; then
    detected_ip="$(detect_default_ip || true)"
  fi

  local ip_value="${forced_ip:-$detected_ip}"
  if [[ -z "$ip_value" ]]; then
    echo "警告：未能自动探测到可用 IPv4，保留现有 CLAWLOOPS_DOMAIN 与 RUNTIME_PUBLIC_BASE_URL。"
    return 0
  fi

  upsert_env_value "CLAWLOOPS_DOMAIN" "${ip_value}"
  upsert_env_value "RUNTIME_PUBLIC_BASE_URL" "http://${ip_value}"
  echo "已更新 CLAWLOOPS_DOMAIN=${ip_value}"
  echo "已更新 RUNTIME_PUBLIC_BASE_URL=http://${ip_value}"
}

normalize_mirrors() {
  if [[ "$MIRROR_MODE" == "keep" ]]; then
    return 0
  fi

  local pip_candidates=(
    "https://pypi.org/simple"
    "https://mirrors.aliyun.com/pypi/simple"
    "https://pypi.tuna.tsinghua.edu.cn/simple"
  )
  local npm_candidates=(
    "https://registry.npmjs.org"
    "https://registry.npmmirror.com"
  )
  local apt_candidates=(
    "mirrors.aliyun.com"
    "mirrors.tencent.com"
    "mirrors.ustc.edu.cn"
    "mirrors.tuna.tsinghua.edu.cn"
    "deb.debian.org"
  )

  pick_first_reachable_host() {
    local port="$1"
    shift
    if ! need_cmd timeout; then
      printf '%s\n' "$1"
      return 0
    fi
    local host
    for host in "$@"; do
      if timeout 2 bash -lc "cat < /dev/null > /dev/tcp/${host}/${port}" >/dev/null 2>&1; then
        printf '%s\n' "$host"
        return 0
      fi
    done
    printf '%s\n' "$1"
  }

  url_hostname() {
    local url="$1"
    printf '%s\n' "$url" | sed -E 's|^[a-zA-Z]+://||' | cut -d/ -f1
  }

  pick_first_reachable_url() {
    local port="$1"
    shift
    if ! need_cmd timeout; then
      printf '%s\n' "$1"
      return 0
    fi
    local url host
    for url in "$@"; do
      host="$(url_hostname "$url")"
      if [[ -n "$host" ]] && timeout 2 bash -lc "cat < /dev/null > /dev/tcp/${host}/${port}" >/dev/null 2>&1; then
        printf '%s\n' "$url"
        return 0
      fi
    done
    printf '%s\n' "$1"
  }

  local api_pip runtime_mgr_pip web_npm web_pnpm api_apt
  api_pip="$(read_env_value "API_PIP_INDEX_URL" || true)"
  runtime_mgr_pip="$(read_env_value "RUNTIME_MANAGER_PIP_INDEX_URL" || true)"
  web_npm="$(read_env_value "WEB_NPM_REGISTRY" || true)"
  web_pnpm="$(read_env_value "WEB_PNPM_REGISTRY" || true)"
  api_apt="$(read_env_value "API_APT_MIRROR" || true)"

  local pip_selected npm_selected apt_selected
  pip_selected="$(pick_first_reachable_url 443 "${pip_candidates[@]}")"
  npm_selected="$(pick_first_reachable_url 443 "${npm_candidates[@]}")"
  apt_selected="$(pick_first_reachable_host 80 "${apt_candidates[@]}")"

  if [[ -z "$api_pip" ]]; then
    upsert_env_value "API_PIP_INDEX_URL" "$pip_selected"
    echo "已设置 API_PIP_INDEX_URL=$pip_selected"
  elif echo "$api_pip" | grep -qiE 'pypi\.tuna\.tsinghua\.edu\.cn'; then
    upsert_env_value "API_PIP_INDEX_URL" "$pip_selected"
    echo "已切换 API_PIP_INDEX_URL=$pip_selected"
  fi

  if [[ -z "$runtime_mgr_pip" ]]; then
    upsert_env_value "RUNTIME_MANAGER_PIP_INDEX_URL" "$pip_selected"
    echo "已设置 RUNTIME_MANAGER_PIP_INDEX_URL=$pip_selected"
  elif echo "$runtime_mgr_pip" | grep -qiE 'pypi\.tuna\.tsinghua\.edu\.cn'; then
    upsert_env_value "RUNTIME_MANAGER_PIP_INDEX_URL" "$pip_selected"
    echo "已切换 RUNTIME_MANAGER_PIP_INDEX_URL=$pip_selected"
  fi

  if [[ -z "$web_npm" ]]; then
    upsert_env_value "WEB_NPM_REGISTRY" "$npm_selected"
    echo "已设置 WEB_NPM_REGISTRY=$npm_selected"
  fi
  if [[ -z "$web_pnpm" ]]; then
    upsert_env_value "WEB_PNPM_REGISTRY" "$npm_selected"
    echo "已设置 WEB_PNPM_REGISTRY=$npm_selected"
  fi

  if [[ -z "$api_apt" ]]; then
    upsert_env_value "API_APT_MIRROR" "$apt_selected"
    echo "已设置 API_APT_MIRROR=$apt_selected"
  elif [[ "$api_apt" == "deb.debian.org" ]]; then
    upsert_env_value "API_APT_MIRROR" "$apt_selected"
    echo "已切换 API_APT_MIRROR=$apt_selected"
  fi
}

docker_host_gateway_ip() {
  if need_cmd ip; then
    local gw
    gw="$(ip -4 addr show docker0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n 1 || true)"
    if [[ -n "$gw" ]]; then
      printf '%s\n' "$gw"
      return 0
    fi
  fi
  printf '%s\n' "172.17.0.1"
}

rewrite_proxy_url_if_localhost() {
  local url="$1"
  local host_gw="$2"
  if [[ -z "$url" ]]; then
    printf '%s\n' ""
    return 0
  fi
  printf '%s\n' "$url" \
    | sed -E "s#^([a-zA-Z0-9+.-]+://)(127\\.0\\.0\\.1|localhost)(:([0-9]+))?#\\1${host_gw}\\3#g"
}

prepare_proxy_env() {
  if [[ "$PROXY_MODE" == "off" ]]; then
    export HTTP_PROXY="" http_proxy="" HTTPS_PROXY="" https_proxy="" ALL_PROXY="" all_proxy="" NO_PROXY="${NO_PROXY:-}" no_proxy="${no_proxy:-${NO_PROXY:-}}"
    return 0
  fi

  if [[ "$PROXY_MODE" == "keep" ]]; then
    return 0
  fi

  local host_gw
  host_gw="$(docker_host_gateway_ip)"

  local hp="${HTTP_PROXY:-${http_proxy:-}}"
  local hsp="${HTTPS_PROXY:-${https_proxy:-}}"
  local ap="${ALL_PROXY:-${all_proxy:-}}"

  local new_hp new_hsp new_ap
  new_hp="$(rewrite_proxy_url_if_localhost "$hp" "$host_gw")"
  new_hsp="$(rewrite_proxy_url_if_localhost "$hsp" "$host_gw")"
  new_ap="$(rewrite_proxy_url_if_localhost "$ap" "$host_gw")"

  if [[ "$hp" != "$new_hp" || "$hsp" != "$new_hsp" || "$ap" != "$new_ap" ]]; then
    echo "检测到代理指向 localhost，已改写为 Docker 宿主网关：$host_gw"
  fi

  if [[ -n "$new_hp" ]]; then export HTTP_PROXY="$new_hp" http_proxy="$new_hp"; fi
  if [[ -n "$new_hsp" ]]; then export HTTPS_PROXY="$new_hsp" https_proxy="$new_hsp"; fi
  if [[ -n "$new_ap" ]]; then export ALL_PROXY="$new_ap" all_proxy="$new_ap"; fi

  local base_no_proxy="localhost,127.0.0.1,::1,litellm,ollama,traefik,clawloops-api,clawloops-web,runtime-manager"
  if [[ -n "${NO_PROXY:-}" ]]; then
    export NO_PROXY="${NO_PROXY},${base_no_proxy}"
  else
    export NO_PROXY="${base_no_proxy}"
  fi
  if [[ -n "${no_proxy:-}" ]]; then
    export no_proxy="${no_proxy},${base_no_proxy}"
  else
    export no_proxy="${NO_PROXY}"
  fi
}

validate_env_file() {
  local required_keys=(
    "CLAWLOOPS_DOMAIN"
    "RUNTIME_PUBLIC_BASE_URL"
    "RUNTIME_BROWSER_SCHEME"
  )
  local key value
  for key in "${required_keys[@]}"; do
    value="$(read_env_value "$key" || true)"
    if [[ -z "$value" ]]; then
      echo "配置缺失：$key"
      echo "请在 CI 环境中写入 $REPO_DIR/infra/compose/.env 或在流水线中注入变量。"
      exit 1
    fi
  done
}

compose_up() {
  local compose_dir="$REPO_DIR/infra/compose"
  (
    cd "$compose_dir"
    "${DOCKER_CMD[@]}" compose up -d --build
  )
}

print_access_summary() {
  local clawloops_domain runtime_public_base_url
  clawloops_domain="$(read_env_value "CLAWLOOPS_DOMAIN")"
  runtime_public_base_url="$(read_env_value "RUNTIME_PUBLIC_BASE_URL")"
  echo "启动完成。"
  echo "主站：http://${clawloops_domain}"
  echo "Runtime Manager：http://${clawloops_domain}/runtime-manager"
  echo "OpenClaw Runtime 示例：${runtime_public_base_url}/runtime/<runtimeId>/chat?session=main#token=<OpenClaw token>"
}

main() {
  require_cmd "grep" "请先安装 grep。"
  require_cmd "awk" "请先安装 awk。"
  require_cmd "docker" "请先安装 Docker Engine。"
  init_docker_cmd
  ensure_compose_available
  ensure_env_file
  apply_public_base_url
  normalize_mirrors
  prepare_proxy_env
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
