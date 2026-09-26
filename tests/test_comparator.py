"""Unit tests for backend.comparator."""

from backend.ai_client import AIClient
from backend.comparator import compare_documents


def test_compare_documents_identifies_unique_obligations():
    doc_a = "The Vendor shall deliver goods within 30 days.\n\nGeneral clause A."
    doc_b = "The Vendor shall provide monthly reports.\n\nGeneral clause B."
    result = compare_documents(doc_a, doc_b, ai_client=AIClient(provider="mock"))
    assert any("30 days" in ob for ob in result.only_in_a_obligations)
    assert any("monthly reports" in ob for ob in result.only_in_b_obligations)


def test_compare_documents_identifies_shared_obligations():
    shared_clause = "The Client shall pay invoices within 15 days."
    doc_a = f"{shared_clause}\n\nUnique A clause here."
    doc_b = f"{shared_clause}\n\nUnique B clause here."
    result = compare_documents(doc_a, doc_b, ai_client=AIClient(provider="mock"))
    assert any("pay invoices" in ob for ob in result.shared_obligations)


def test_compare_documents_produces_ai_summary():
    result = compare_documents(
        "The Vendor shall deliver goods.",
        "The Vendor shall provide services.",
        ai_client=AIClient(provider="mock"),
    )
    assert result.ai_comparison_summary
    assert isinstance(result.ai_comparison_summary, str)


def test_compare_documents_handles_identical_documents():
    text = "The parties shall cooperate in good faith."
    result = compare_documents(text, text, ai_client=AIClient(provider="mock"))
    assert result.only_in_a_obligations == []
    assert result.only_in_b_obligations == []
    assert len(result.shared_obligations) >= 1
