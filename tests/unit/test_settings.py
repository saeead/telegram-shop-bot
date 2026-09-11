from pydantic import ValidationError

from app.config.settings import Settings


def test_settings_validate_required_bot_token(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    settings = Settings(telegram_bot_token="test-token")
    assert settings.telegram_bot_token == "test-token"
    assert settings.app_env == "development"


def test_settings_reject_missing_bot_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    try:
        Settings()
    except ValidationError as exc:
        assert "telegram_bot_token" in str(exc)
    else:
        raise AssertionError("Settings must reject a missing Telegram bot token")
