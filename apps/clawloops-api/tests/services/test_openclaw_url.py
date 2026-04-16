from app.services.openclaw_url import build_openclaw_chat_url, merge_with_existing_token


def test_build_openclaw_chat_url_with_token():
    url = build_openclaw_chat_url("http://localhost:32902", "user2-token")
    assert url == "http://localhost:32902/chat?session=main#token=user2-token"


def test_build_openclaw_chat_url_keeps_runtime_path_prefix():
    url = build_openclaw_chat_url("http://clawloops.localhost/runtime/rt-001", "user2-token")
    assert url == "http://clawloops.localhost/runtime/rt-001/chat?session=main#token=user2-token"


def test_merge_with_existing_token_keeps_token_when_runtime_manager_url_changes():
    merged = merge_with_existing_token(
        new_browser_url="http://clawloops.localhost/runtime/rt-003",
        existing_browser_url="http://clawloops.localhost/runtime/rt-002/chat?session=main#token=user2-token",
    )
    assert merged == "http://clawloops.localhost/runtime/rt-003/chat?session=main#token=user2-token"
