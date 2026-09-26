"""Unit tests for backend.qa_engine."""

from backend.ai_client import AIClient
from backend.qa_engine import answer_question


def test_answer_question_requires_document_and_question():
    result = answer_question("", "What is the term?", ai_client=AIClient(provider="mock"))
    assert not result.grounded
    assert "provide both" in result.answer.lower()


def test_answer_question_requires_non_empty_question():
    result = answer_question("Some document text.", "", ai_client=AIClient(provider="mock"))
    assert not result.grounded


def test_answer_question_returns_source_excerpts_when_grounded():
    doc = "The term of this Agreement is 12 months from the Effective Date. " * 3
    result = answer_question(doc, "What is the term of the agreement?", ai_client=AIClient(provider="mock"))
    assert isinstance(result.source_excerpts, list)
    assert len(result.source_excerpts) >= 1


def test_answer_question_masks_pii_in_document_before_use():
    doc = "Contact jane@example.com. The term is 12 months."
    result = answer_question(doc, "What is the term?", ai_client=AIClient(provider="mock"))
    joined = " ".join(result.source_excerpts)
    assert "jane@example.com" not in joined


def test_answer_question_handles_long_document_via_chunking():
    doc = ("Clause about payment terms. " * 200) + "The termination notice period is 60 days. " + ("Filler text. " * 200)
    result = answer_question(doc, "What is the termination notice period?", ai_client=AIClient(provider="mock"))
    assert result.answer
    assert isinstance(result.grounded, bool)
