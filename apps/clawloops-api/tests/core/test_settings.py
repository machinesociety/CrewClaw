from app.core.settings import AppSettings


def test_dashscope_support_accepts_prefixed_key_for_explicit_config():
    settings = AppSettings(
        DASHSCOPE_API_KEY="dashscope:sk-example",
    )

    assert settings.has_explicit_dashscope_support() is True
    assert settings.is_provider_ready("dashscope") is True


def test_dashscope_support_rejects_explicitly_empty_key():
    settings = AppSettings(
        DASHSCOPE_API_KEY="",
    )

    assert settings.has_explicit_dashscope_support() is False
    assert settings.is_provider_ready("dashscope") is False
