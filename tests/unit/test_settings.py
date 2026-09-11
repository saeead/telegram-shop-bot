from app.config.settings import Settings


def test_settings_validate_required_bot_token():
    settings = Settings(telegram_bot_token="test-token")
    assert settings.telegram_bot_token == "test-token"
    assert settings.app_env == "development"


def test_settings_reject_missing_bot_token():
    try:
        Settings()
    except Exception as exc:
        assert "telegram_bot_token" in str(exc)
    else:
        raise AssertionError("Settings must reject a missing Telegram bot token")
