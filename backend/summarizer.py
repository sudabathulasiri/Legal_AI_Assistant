"""
Structured summaries and checklists.

Turns a parsed document into a compact, structured summary object suitable
for direct rendering in the UI (or export), always paired with a
"not legal advice" disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from backend.ai_client import AIClient
from backend.document_parser import ParsedDocument, parse_document

DISCLAIMER = (
    "⚠️ This summary is generated for informational purposes only and is NOT "
    "legal advice. Consult a licensed attorney before relying on it."
)


@dataclass
class StructuredSummary:
    """A ready-to-render structured summary of a legal document."""

    plain_summary: str
    obligations_checklist: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    clause_count: int = 0
    disclaimer: str = DISCLAIMER


def build_summary(
    raw_text: str,
    ai_client: AIClient | None = None,
    parsed: ParsedDocument | None = None,
) -> StructuredSummary:
    """Build a `StructuredSummary` from raw document text (or a pre-parsed document)."""
    client = ai_client or AIClient()
    doc = parsed or parse_document(raw_text, ai_client=client)

    return StructuredSummary(
        plain_summary=doc.ai_summary,
        obligations_checklist=doc.obligations,
        risk_flags=doc.risks,
        clause_count=len(doc.clauses),
    )


def summary_to_markdown(summary: StructuredSummary) -> str:
    """Render a `StructuredSummary` as a clean Markdown document for export/copy."""
    lines = ["# Document Summary", "", summary.disclaimer, "", "## Plain-Language Summary", summary.plain_summary, ""]

    lines.append("## Obligations Checklist")
    if summary.obligations_checklist:
        lines.extend(f"- [ ] {item}" for item in summary.obligations_checklist)
    else:
        lines.append("_No explicit obligations detected._")
    lines.append("")

    lines.append("## Flagged Risks")
    if summary.risk_flags:
        lines.extend(f"- ⚠️ {item}" for item in summary.risk_flags)
    else:
        lines.append("_No high-risk clauses detected by keyword screening._")
    lines.append("")
    lines.append(f"_Total clauses analyzed: {summary.clause_count}_")

    return "\n".join(lines)
