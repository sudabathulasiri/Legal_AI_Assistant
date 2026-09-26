"""
Clause / obligation / risk extraction.

Combines lightweight rule-based structuring (fast, deterministic, works
offline) with an AI-generated narrative summary, so the app remains useful
and testable even without any AI provider configured.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from backend.ai_client import AIClient
from backend.chunking import chunk_text
from backend.security import mask_pii, sanitize_text

RISK_KEYWORDS = [
    "indemnif", "liquidated damages", "penalty", "terminate", "termination",
    "auto-renew", "automatic renewal", "non-compete", "exclusiv", "waiver",
    "unlimited liability", "arbitration", "governing law", "confidential",
    "breach", "default", "forfeit",
]

OBLIGATION_MARKERS = ["shall", "must", "agrees to", "is required to", "will provide", "responsible for"]

_CLAUSE_SPLIT_RE = re.compile(r"(?:\n\s*\n)|(?:\n(?=\d+[.)]\s))|(?:\n(?=[A-Z][A-Za-z ]{3,60}:\n))")


@dataclass
class Clause:
    """A single structured clause extracted from a document."""

    index: int
    text: str
    is_obligation: bool
    is_risk: bool


@dataclass
class ParsedDocument:
    """Full structured output of parsing one legal document."""

    clauses: List[Clause] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    ai_summary: str = ""


def split_into_clauses(text: str) -> List[str]:
    """Split cleaned document text into clause-sized segments."""
    if not text.strip():
        return []
    raw_parts = _CLAUSE_SPLIT_RE.split(text)
    parts = [p.strip() for p in raw_parts if p and p.strip()]
    return parts if parts else [text.strip()]


def _is_obligation(clause: str) -> bool:
    lowered = clause.lower()
    return any(marker in lowered for marker in OBLIGATION_MARKERS)


def _is_risk(clause: str) -> bool:
    lowered = clause.lower()
    return any(keyword in lowered for keyword in RISK_KEYWORDS)


def parse_document(raw_text: str, ai_client: AIClient | None = None) -> ParsedDocument:
    """
    Sanitize, mask PII, and structurally parse `raw_text` into clauses,
    obligations, and risks, plus a short AI-generated plain-language summary.
    """
    clean = mask_pii(sanitize_text(raw_text))
    clause_texts = split_into_clauses(clean)

    clauses: List[Clause] = []
    obligations: List[str] = []
    risks: List[str] = []

    for i, ctext in enumerate(clause_texts):
        obligation = _is_obligation(ctext)
        risk = _is_risk(ctext)
        clauses.append(Clause(index=i, text=ctext, is_obligation=obligation, is_risk=risk))
        if obligation:
            obligations.append(ctext)
        if risk:
            risks.append(ctext)

    client = ai_client or AIClient()
    lead_chunk = chunk_text(clean, chunk_size=3000, overlap=200)
    sample_text = lead_chunk[0].text if lead_chunk else clean
    ai_response = client.complete(
        system=(
            "You are a careful legal-document analysis assistant. Explain contracts in "
            "plain English for a non-lawyer. Always note this is not legal advice."
        ),
        prompt=f"Summarize the following contract text in plain English:\n\n{sample_text}",
        max_tokens=500,
    )

    return ParsedDocument(
        clauses=clauses,
        obligations=obligations,
        risks=risks,
        ai_summary=ai_response.text,
    )
