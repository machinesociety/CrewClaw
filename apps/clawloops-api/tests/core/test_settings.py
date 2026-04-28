from app.core.settings import AppSettings


def test_dashscope_support_accepts_prefixed_key_for_explicit_config():
    settings = AppSettings(
        DASHSCOPE_API_KEY="dashscope:sk-example",
    )

    assert settings.has_explicit_dashscope_support() is True
    assert settings.is_provider_ready("dashscope") is True


def test_dashscope_support_accepts_non_prefixed_key_for_explicit_config():
    settings = AppSettings(
        DASHSCOPE_API_KEY="f0d73b20db924eebb61ea0a339bb2c23",
    )

    assert settings.has_explicit_dashscope_support() is True
    assert settings.is_provider_ready("dashscope") is True


def test_dashscope_support_rejects_explicitly_empty_key():
    settings = AppSettings(
        DASHSCOPE_API_KEY="",
    )

    assert settings.has_explicit_dashscope_support() is False
    assert settings.is_provider_ready("dashscope") is False


def test_openrouter_support_rejects_explicitly_empty_key():
    settings = AppSettings(
        OPENROUTER_API_KEY="",
    )

    assert settings.has_explicit_openrouter_support() is False
    assert settings.is_provider_ready("openrouter") is False
