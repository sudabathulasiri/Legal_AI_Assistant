"""
Configuration loader.

Reads settings from environment variables (optionally via a local .env file)
and exposes a single, validated `Settings` object. No secret ever has a
non-empty default, so a missing .env simply results in Mock mode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)  # loads the project .env regardless of cwd


def _get_value(name: str, default: str = "") -> str:
    """Read a setting from the environment or Streamlit Secrets."""
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        secret_value = st.secrets.get(name, "")
    except (ImportError, FileNotFoundError, RuntimeError, AttributeError):
        secret_value = ""
    return str(secret_value).strip() or default


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back safely on bad input."""
    raw = _get_value(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable application settings, loaded once at import time."""

    ai_provider: str
    groq_api_key: str
    groq_model: str
    anthropic_api_key: str
    anthropic_model: str
    openai_api_key: str
    openai_model: str
    max_upload_chars: int
    chunk_size_chars: int
    chunk_overlap_chars: int
    log_level: str

    def resolved_provider(self) -> str:
        """Determine which provider to actually use, with safe auto-fallback."""
        requested = (self.ai_provider or "").strip().lower()
        if requested in ("groq", "anthropic", "openai", "mock"):
            if requested == "groq" and not self.groq_api_key:
                return "mock"
            if requested == "anthropic" and not self.anthropic_api_key:
                return "mock"
            if requested == "openai" and not self.openai_api_key:
                return "mock"
            return requested
        # auto-detect, preferring Groq (fast + generous free tier)
        if self.groq_api_key:
            return "groq"
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "mock"


def load_settings() -> Settings:
    """Build a Settings instance from the current environment."""
    return Settings(
        ai_provider=_get_value("AI_PROVIDER", "mock"),
        groq_api_key=_get_value("GROQ_API_KEY"),
        groq_model=_get_value("GROQ_MODEL", "openai/gpt-oss-20b"),
        anthropic_api_key=_get_value("ANTHROPIC_API_KEY"),
        anthropic_model=_get_value("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        openai_api_key=_get_value("OPENAI_API_KEY"),
        openai_model=_get_value("OPENAI_MODEL", "gpt-4o-mini"),
        max_upload_chars=_get_int("MAX_UPLOAD_CHARS", 200_000),
        chunk_size_chars=_get_int("CHUNK_SIZE_CHARS", 3_000),
        chunk_overlap_chars=_get_int("CHUNK_OVERLAP_CHARS", 200),
        log_level=_get_value("LOG_LEVEL", "INFO").upper(),
    )


SETTINGS = load_settings()
