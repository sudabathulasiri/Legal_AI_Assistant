"""
Token-efficient chunking utilities.

Splits long documents into overlapping, size-bounded chunks so that only the
relevant portion of a document is ever sent to an AI provider, keeping
latency and token usage low.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Chunk:
    """A single contiguous slice of a source document."""

    index: int
    text: str
    start_char: int
    end_char: int


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[Chunk]:
    """
    Split `text` into a list of `Chunk` objects of at most `chunk_size`
    characters each, with `overlap` characters shared between consecutive
    chunks so context is not lost at boundaries.

    Edge cases handled: empty input returns an empty list; `chunk_size` <= 0
    or `overlap` >= `chunk_size` are corrected to safe defaults so the
    function never enters an infinite loop.
    """
    if not text:
        return []

    if chunk_size <= 0:
        chunk_size = 3000
    if overlap < 0 or overlap >= chunk_size:
        overlap = min(200, chunk_size // 4)

    chunks: List[Chunk] = []
    start = 0
    length = len(text)
    index = 0

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(Chunk(index=index, text=text[start:end], start_char=start, end_char=end))
        if end >= length:
            break
        start = end - overlap
        index += 1

    return chunks


def _score_chunk(chunk_text_value: str, query_terms: List[str]) -> int:
    """Simple, dependency-free lexical overlap score used for retrieval."""
    lowered = chunk_text_value.lower()
    return sum(lowered.count(term) for term in query_terms if term)


def top_matching_chunks(chunks: List[Chunk], query: str, top_k: int = 3) -> List[Chunk]:
    """
    Return the `top_k` chunks most lexically relevant to `query`, using a
    lightweight term-frequency heuristic. This avoids pulling in a heavy
    embeddings dependency while still keeping Q&A grounded and token-efficient.

    If `query` is empty or no chunk scores above zero, falls back to
    returning the first `top_k` chunks so callers always get *something* to
    ground their answer in.
    """
    if not chunks:
        return []

    terms = [t for t in query.lower().split() if len(t) > 2]
    scored = [(_score_chunk(c.text, terms), c) for c in chunks]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    if not terms or scored[0][0] == 0:
        return chunks[:top_k]

    return [c for _score, c in scored[:top_k]]
