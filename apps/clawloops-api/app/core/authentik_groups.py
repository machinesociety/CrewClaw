"""Authentik ForwardAuth 组头解析与应用角色映射。"""

import base64
import json

from app.domain.users import UserRole


def parse_authentik_groups(header_value: str) -> list[str]:
    """将 X-Authentik-Groups 拆成组名列表（逗号分隔、去空白、去空项）。"""
    parts = header_value.split(",")
    return [p.strip() for p in parts if p.strip()]


def parse_admin_group_slugs(config_value: str) -> set[str]:
    """解析 CLAWLOOPS_AUTH_ADMIN_GROUP_SLUGS 配置（逗号分隔）。"""
    return {p.strip() for p in config_value.split(",") if p.strip()}


def effective_role_from_groups(group_names: list[str], admin_slugs: set[str]) -> UserRole:
    """若组名与管理员 slug 有交集则为 ADMIN，否则 USER。"""
    if admin_slugs and set(group_names) & admin_slugs:
        return UserRole.ADMIN
    return UserRole.USER


def parse_group_names_from_authentik_jwt(jwt_token: str) -> list[str] | None:
    """
    从 Outpost 下发的 X-authentik-jwt 中解析 `groups`（不校验签名，仅读 payload）。

    - 返回 None：无法解析、或 payload 中无 `groups` 键（与「应跳过同步」一致）。
    - 返回 []：明确无组，与空 X-Authentik-Groups 行为一致，可同步为 USER。
    - groups 元素可为字符串，或带 `name`/`pk` 的字典（与 Authentik 变体兼容）。
    """
    if not jwt_token or jwt_token.count(".") < 2:
        return None
    try:
        part = jwt_token.split(".")[1]
        pad = (-len(part)) % 4
        if pad:
            part += "=" * pad
        raw = base64.urlsafe_b64decode(part)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    if "groups" not in payload:
        return None

    raw_groups = payload["groups"]
    if raw_groups is None:
        return []
    if not isinstance(raw_groups, list):
        return None

    names: list[str] = []
    for item in raw_groups:
        if isinstance(item, str):
            names.append(item.strip())
        elif isinstance(item, dict):
            n = item.get("name")
            if n is not None:
                names.append(str(n).strip())
            else:
                pk = item.get("pk")
                if pk is not None:
                    names.append(str(pk).strip())
    return [n for n in names if n]
