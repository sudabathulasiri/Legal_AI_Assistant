"""
Context-grounded legal Q&A engine.

Retrieves the most relevant chunks of a source document for a given
question, then asks the AI backend to answer strictly from that retrieved
context — refusing to answer when the document does not contain the
information, rather than hallucinating.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.ai_client import AIClient
from backend.chunking import chunk_text, top_matching_chunks
from backend.security import mask_pii, sanitize_text

REFUSAL_MARKER = "NOT_FOUND_IN_DOCUMENT"


@dataclass(frozen=True)
class QAAnswer:
    """Result of a grounded Q&A query."""

    answer: str
    grounded: bool
    source_excerpts: List[str]


def answer_question(
    document_text: str,
    question: str,
    ai_client: AIClient | None = None,
    top_k: int = 3,
    chunk_size: int = 3000,
    overlap: int = 200,
) -> QAAnswer:
    """
    Answer `question` using only content retrieved from `document_text`.

    If the question is empty or the document is empty, returns a clear,
    non-grounded refusal rather than calling the AI provider.
    """
    clean_doc = mask_pii(sanitize_text(document_text))
    clean_question = sanitize_text(question, max_len=2000)

    if not clean_doc.strip() or not clean_question.strip():
        return QAAnswer(
            answer="Please provide both a document and a question before asking.",
            grounded=False,
            source_excerpts=[],
        )

    chunks = chunk_text(clean_doc, chunk_size=chunk_size, overlap=overlap)
    relevant = top_matching_chunks(chunks, clean_question, top_k=top_k)
    context = "\n\n---\n\n".join(c.text for c in relevant)

    client = ai_client or AIClient()
    system = (
        "You are a legal-document Q&A assistant. Answer ONLY using the provided "
        f"context. If the answer is not present in the context, reply with exactly "
        f"'{REFUSAL_MARKER}' and nothing else. Never invent facts not in the context. "
        "This is not legal advice."
    )
    prompt = f"CONTEXT:\n{context}\n\nQUESTION: {clean_question}\n\nANSWER:"

    response = client.complete(system=system, prompt=prompt, max_tokens=400)
    grounded = REFUSAL_MARKER not in response.text

    final_answer = response.text
    if not grounded:
        final_answer = (
            "I couldn't find an answer to that question in the provided document. "
            "Please check the document or rephrase your question. "
            "This tool cannot provide legal advice."
        )

    return QAAnswer(
        answer=final_answer,
        grounded=grounded,
        source_excerpts=[c.text for c in relevant],
    )
