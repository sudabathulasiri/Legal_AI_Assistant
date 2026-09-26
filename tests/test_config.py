"""Unit tests for backend.config provider resolution, including Groq."""

from backend.config import Settings


def _settings(**overrides) -> Settings:
    base = dict(
        ai_provider="",
        groq_api_key="",
        groq_model="openai/gpt-oss-20b",
        anthropic_api_key="",
        anthropic_model="claude-sonnet-4-6",
        openai_api_key="",
        openai_model="gpt-4o-mini",
        max_upload_chars=200000,
        chunk_size_chars=3000,
        chunk_overlap_chars=200,
        log_level="INFO",
    )
    base.update(overrides)
    return Settings(**base)


def test_resolved_provider_defaults_to_mock_with_no_keys():
    assert _settings().resolved_provider() == "mock"


def test_resolved_provider_prefers_groq_when_key_present():
    assert _settings(groq_api_key="gsk_test").resolved_provider() == "groq"


def test_resolved_provider_groq_beats_anthropic_and_openai_in_autodetect():
    settings = _settings(groq_api_key="gsk_test", anthropic_api_key="sk-ant", openai_api_key="sk-oai")
    assert settings.resolved_provider() == "groq"


def test_resolved_provider_explicit_groq_without_key_falls_back_to_mock():
    settings = _settings(ai_provider="groq", groq_api_key="")
    assert settings.resolved_provider() == "mock"


def test_resolved_provider_explicit_groq_with_key_is_honored():
    settings = _settings(ai_provider="groq", groq_api_key="gsk_test", anthropic_api_key="sk-ant")
    assert settings.resolved_provider() == "groq"


def test_resolved_provider_falls_back_to_anthropic_without_groq_key():
    settings = _settings(anthropic_api_key="sk-ant")
    assert settings.resolved_provider() == "anthropic"
