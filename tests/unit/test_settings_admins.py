from app.config.settings import Settings


def test_admin_ids_are_parsed_from_environment_value() -> None:
    settings = Settings(telegram_bot_token="test-token", telegram_admin_ids="1001, 1002")
    assert settings.admin_ids == frozenset({1001, 1002})
