"""Unit tests for backend.security: sanitization and PII masking."""

from backend.security import mask_pii, safe_error_message, sanitize_text


def test_sanitize_strips_script_tags():
    raw = "Hello <script>alert('xss')</script> world"
    result = sanitize_text(raw)
    assert "<script>" not in result
    assert "alert" not in result
    assert "Hello" in result and "world" in result


def test_sanitize_strips_generic_html_tags():
    raw = "<b>Important</b> clause <div class='x'>here</div>"
    result = sanitize_text(raw)
    assert "<b>" not in result
    assert "<div" not in result
    assert "Important" in result
    assert "here" in result


def test_sanitize_removes_control_characters():
    raw = "Line1\x00\x01Line2"
    result = sanitize_text(raw)
    assert "\x00" not in result
    assert "\x01" not in result


def test_sanitize_enforces_max_length():
    raw = "a" * 1000
    result = sanitize_text(raw, max_len=50)
    assert len(result) == 50


def test_sanitize_handles_none_and_empty():
    assert sanitize_text(None) == ""
    assert sanitize_text("") == ""


def test_mask_pii_redacts_email():
    text = "Contact me at john.doe@example.com for details."
    masked = mask_pii(text)
    assert "john.doe@example.com" not in masked
    assert "[EMAIL_REDACTED]" in masked


def test_mask_pii_redacts_phone_number():
    text = "Call us at 415-555-1234 tomorrow."
    masked = mask_pii(text)
    assert "415-555-1234" not in masked
    assert "[PHONE_REDACTED]" in masked


def test_mask_pii_redacts_ssn():
    text = "SSN on file: 123-45-6789."
    masked = mask_pii(text)
    assert "123-45-6789" not in masked
    assert "[SSN_REDACTED]" in masked


def test_mask_pii_redacts_card_like_number():
    text = "Card number 4111 1111 1111 1111 was used."
    masked = mask_pii(text)
    assert "4111 1111 1111 1111" not in masked
    assert "[CARD_NUMBER_REDACTED]" in masked


def test_mask_pii_leaves_normal_text_untouched():
    text = "This agreement is entered into by both parties."
    assert mask_pii(text) == text


def test_safe_error_message_never_leaks_exception_details():
    exc = ValueError("secret internal path /etc/passwd traceback line 42")
    message = safe_error_message(exc)
    assert "/etc/passwd" not in message
    assert "traceback" not in message.lower()
    assert isinstance(message, str) and len(message) > 0
