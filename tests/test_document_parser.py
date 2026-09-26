"""Unit tests for backend.document_parser."""

from backend.ai_client import AIClient
from backend.document_parser import parse_document, split_into_clauses


def test_split_into_clauses_handles_empty_text():
    assert split_into_clauses("") == []
    assert split_into_clauses("   ") == []


def test_split_into_clauses_splits_on_blank_lines():
    text = "Clause one text.\n\nClause two text.\n\nClause three text."
    clauses = split_into_clauses(text)
    assert len(clauses) == 3


def test_parse_document_detects_obligations():
    text = "The Vendor shall deliver the goods within 30 days.\n\nThe sky is blue."
    parsed = parse_document(text, ai_client=AIClient(provider="mock"))
    assert any("shall deliver" in ob for ob in parsed.obligations)


def test_parse_document_detects_risks():
    text = "This Agreement may be terminated immediately for breach.\n\nGeneral introduction text."
    parsed = parse_document(text, ai_client=AIClient(provider="mock"))
    assert len(parsed.risks) >= 1


def test_parse_document_masks_pii_before_parsing():
    text = "Contact john@example.com. The Client shall pay within 10 days."
    parsed = parse_document(text, ai_client=AIClient(provider="mock"))
    joined = " ".join(c.text for c in parsed.clauses)
    assert "john@example.com" not in joined
    assert "[EMAIL_REDACTED]" in joined


def test_parse_document_produces_ai_summary_in_mock_mode():
    text = "The parties agree to the following terms and conditions."
    parsed = parse_document(text, ai_client=AIClient(provider="mock"))
    assert parsed.ai_summary
    assert isinstance(parsed.ai_summary, str)


def test_parse_document_handles_empty_input_gracefully():
    parsed = parse_document("", ai_client=AIClient(provider="mock"))
    assert parsed.clauses == []
    assert parsed.obligations == []
    assert parsed.risks == []
