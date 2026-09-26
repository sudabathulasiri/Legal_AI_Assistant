"""Unit tests for backend.summarizer."""

from backend.ai_client import AIClient
from backend.summarizer import DISCLAIMER, build_summary, summary_to_markdown


def test_build_summary_includes_disclaimer():
    summary = build_summary("The parties shall act in good faith.", ai_client=AIClient(provider="mock"))
    assert summary.disclaimer == DISCLAIMER
    assert "not legal advice" in summary.disclaimer.lower()


def test_build_summary_populates_checklist_and_risks():
    text = (
        "The Vendor shall deliver the product within 10 days.\n\n"
        "This Agreement may be terminated for breach without notice."
    )
    summary = build_summary(text, ai_client=AIClient(provider="mock"))
    assert len(summary.obligations_checklist) >= 1
    assert len(summary.risk_flags) >= 1
    assert summary.clause_count >= 2


def test_summary_to_markdown_contains_all_sections():
    text = "The Client shall pay all invoices within 30 days."
    summary = build_summary(text, ai_client=AIClient(provider="mock"))
    markdown = summary_to_markdown(summary)
    assert "# Document Summary" in markdown
    assert "## Obligations Checklist" in markdown
    assert "## Flagged Risks" in markdown
    assert "not legal advice" in markdown.lower() or "Not legal advice" in markdown


def test_summary_to_markdown_handles_no_obligations_or_risks():
    text = "The sky is blue. The grass is green."
    summary = build_summary(text, ai_client=AIClient(provider="mock"))
    markdown = summary_to_markdown(summary)
    assert "No explicit obligations detected" in markdown
    assert "No high-risk clauses detected" in markdown
