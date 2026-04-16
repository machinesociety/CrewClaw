from __future__ import annotations

from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse


def build_openclaw_chat_url(browser_url: str | None, gateway_token: str | None) -> str | None:
    """
    标准化 OpenClaw 入口地址，统一为 /chat?session=main[#token=...]。
    """
    if not browser_url:
        return None

    parsed = urlparse(browser_url)
    base_path = parsed.path.rstrip("/")
    if base_path.endswith("/chat"):
        chat_path = base_path
    elif not base_path:
        chat_path = "/chat"
    else:
        chat_path = f"{base_path}/chat"
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["session"] = query.get("session") or "main"
    token = gateway_token.strip() if gateway_token else ""

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            chat_path,
            parsed.params,
            urlencode(query),
            f"token={quote(token, safe='')}" if token else "",
        )
    )


def extract_gateway_token_from_url(browser_url: str | None) -> str | None:
    if not browser_url:
        return None
    parsed = urlparse(browser_url)
    if parsed.fragment.startswith("token="):
        return parsed.fragment[6:] or None
    return None


def merge_with_existing_token(new_browser_url: str | None, existing_browser_url: str | None) -> str | None:
    """
    当 runtime-manager 返回不带 token 的 browserUrl 时，保留现有 token。
    """
    existing_token = extract_gateway_token_from_url(existing_browser_url)
    return build_openclaw_chat_url(new_browser_url, existing_token)


def replace_openclaw_path(browser_url: str | None, new_path: str) -> str | None:
    if not browser_url:
        return None
    parsed = urlparse(browser_url)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            new_path,
            parsed.params,
            "",
            parsed.fragment,
        )
    )
