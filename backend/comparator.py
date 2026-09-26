"""
Side-by-side agreement comparison.

Produces a structured diff between two parsed documents: obligations and
risks unique to each side, plus an AI-generated narrative highlighting the
most consequential differences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from backend.ai_client import AIClient
from backend.document_parser import ParsedDocument, parse_document


def _normalize(item: str) -> str:
    return " ".join(item.lower().split())


@dataclass
class ComparisonResult:
    """Structured result of comparing two documents."""

    only_in_a_obligations: List[str] = field(default_factory=list)
    only_in_b_obligations: List[str] = field(default_factory=list)
    shared_obligations: List[str] = field(default_factory=list)
    only_in_a_risks: List[str] = field(default_factory=list)
    only_in_b_risks: List[str] = field(default_factory=list)
    shared_risks: List[str] = field(default_factory=list)
    ai_comparison_summary: str = ""


def _diff_lists(a: List[str], b: List[str]) -> tuple[List[str], List[str], List[str]]:
    norm_a = {_normalize(x): x for x in a}
    norm_b = {_normalize(x): x for x in b}
    only_a = [norm_a[k] for k in norm_a if k not in norm_b]
    only_b = [norm_b[k] for k in norm_b if k not in norm_a]
    shared = [norm_a[k] for k in norm_a if k in norm_b]
    return only_a, only_b, shared


def compare_documents(
    text_a: str,
    text_b: str,
    ai_client: AIClient | None = None,
    parsed_a: ParsedDocument | None = None,
    parsed_b: ParsedDocument | None = None,
) -> ComparisonResult:
    """
    Parse (if not already parsed) and compare two contract texts, returning a
    structured `ComparisonResult` plus a short AI narrative of the key
    differences a reader should pay attention to.
    """
    client = ai_client or AIClient()
    doc_a = parsed_a or parse_document(text_a, ai_client=client)
    doc_b = parsed_b or parse_document(text_b, ai_client=client)

    only_a_ob, only_b_ob, shared_ob = _diff_lists(doc_a.obligations, doc_b.obligations)
    only_a_risk, only_b_risk, shared_risk = _diff_lists(doc_a.risks, doc_b.risks)

    prompt = (
        "Document A obligations count: {oa}, risks count: {ra}\n"
        "Document B obligations count: {ob}, risks count: {rb}\n"
        "Obligations only in A: {sample_a}\n"
        "Obligations only in B: {sample_b}\n"
        "In 3-5 sentences, explain the most important practical differences a "
        "non-lawyer should notice between these two agreements."
    ).format(
        oa=len(doc_a.obligations), ra=len(doc_a.risks),
        ob=len(doc_b.obligations), rb=len(doc_b.risks),
        sample_a="; ".join(only_a_ob[:3]) or "(none)",
        sample_b="; ".join(only_b_ob[:3]) or "(none)",
    )
    ai_response = client.complete(
        system=(
            "You are a careful legal-document comparison assistant for non-lawyers. "
            "Always note this is not legal advice."
        ),
        prompt=prompt,
        max_tokens=400,
    )

    return ComparisonResult(
        only_in_a_obligations=only_a_ob,
        only_in_b_obligations=only_b_ob,
        shared_obligations=shared_ob,
        only_in_a_risks=only_a_risk,
        only_in_b_risks=only_b_risk,
        shared_risks=shared_risk,
        ai_comparison_summary=ai_response.text,
    )
