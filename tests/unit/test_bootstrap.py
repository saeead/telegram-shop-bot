from app.config.settings import get_settings
from app.main import main


def test_main_bootstrap(monkeypatch, caplog):
    get_settings.cache_clear()
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("APP_ENV", "test")

    with caplog.at_level("INFO"):
        main()

    assert "Application configuration validated" in caplog.text
    assert "Starting telegram-file-store in test mode" in caplog.text
