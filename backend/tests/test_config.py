from app.core.config import Settings, get_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.APP_ENV == "development"
    assert settings.GROQ_MODEL == "llama-3.1-70b-versatile"


def test_get_settings_returns_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
