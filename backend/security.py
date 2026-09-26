"""
Security utilities: input sanitization and PII-masking simulation.

Every piece of user-supplied text passes through `sanitize_text()` and
`mask_pii()` before it is parsed, summarized, sent to an AI provider, or
rendered back into the UI. This module has zero external dependencies so it
can be unit-tested in complete isolation.
"""

from __future__ import annotations

import re

# --- Sanitization -----------------------------------------------------------

_TAG_BLOCK_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1>", flags=re.IGNORECASE | re.DOTALL
)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_WHITESPACE_RE = re.compile(r"[ \t]{3,}")


def sanitize_text(raw: str, max_len: int = 200_000) -> str:
    """
    Strip script/style blocks, all remaining HTML tags, and control
    characters from `raw`; collapse excessive whitespace; enforce a hard
    length cap to prevent resource-exhaustion / prompt-flooding attacks.

    Returns a plain-text string safe to display, parse, or forward to an AI
    provider.
    """
    if raw is None:
        return ""
    text = str(raw)
    text = _TAG_BLOCK_RE.sub(" ", text)
    text = _ANY_TAG_RE.sub(" ", text)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _MULTI_WHITESPACE_RE.sub("  ", text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len]
    return text


# --- PII masking simulation --------------------------------------------------

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?<!\d)(\+?\d{1,3}[\s.-]?)?(\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
)
_SSN_RE = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def mask_pii(text: str) -> str:
    """
    Simulate PII redaction by replacing detected emails, phone numbers,
    SSN-like sequences, and long card-like digit sequences with typed
    placeholders. This is a heuristic, defense-in-depth measure — not a
    certified PII-detection product — applied before any text is sent to a
    third-party AI provider.
    """
    if not text:
        return text
    masked = text
    masked = _SSN_RE.sub("[SSN_REDACTED]", masked)
    masked = _CARD_RE.sub("[CARD_NUMBER_REDACTED]", masked)
    masked = _EMAIL_RE.sub("[EMAIL_REDACTED]", masked)
    masked = _PHONE_RE.sub("[PHONE_REDACTED]", masked)
    return masked


def safe_error_message(_exc: Exception) -> str:
    """
    Convert any exception into a generic, user-safe error string. Full
    exception details are intentionally discarded here (never included in
    the returned string) to avoid stack-trace / internal-path leakage to end
    users; a caller may separately log `_exc` for local diagnostics.
    """
    return (
        "Something went wrong while processing your request. "
        "No document content was sent anywhere unexpectedly, and no "
        "internal details are shown for security reasons. Please try again."
    )
