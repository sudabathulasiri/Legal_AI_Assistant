"""Unit tests for backend.chunking."""

from backend.chunking import chunk_text, top_matching_chunks


def test_chunk_text_empty_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text(None) == []


def test_chunk_text_short_text_single_chunk():
    text = "short document"
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].text == text


def test_chunk_text_splits_long_text_with_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    # Verify overlap: end of chunk N overlaps with start of chunk N+1
    for i in range(len(chunks) - 1):
        assert chunks[i].end_char - chunks[i + 1].start_char == 50 or chunks[i + 1].start_char < chunks[i].end_char


def test_chunk_text_covers_full_text():
    text = "0123456789" * 50
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert chunks[-1].end_char == len(text)
    assert chunks[0].start_char == 0


def test_chunk_text_handles_bad_params_gracefully():
    text = "some reasonably long piece of text " * 20
    chunks = chunk_text(text, chunk_size=-5, overlap=999999)
    assert len(chunks) >= 1


def test_top_matching_chunks_returns_relevant_first():
    chunks = chunk_text(
        "Termination clause details. " * 5 + "Payment obligations section. " * 5,
        chunk_size=150,
        overlap=10,
    )
    result = top_matching_chunks(chunks, "payment obligations", top_k=1)
    assert len(result) == 1
    assert "payment" in result[0].text.lower()


def test_top_matching_chunks_empty_chunks_returns_empty():
    assert top_matching_chunks([], "anything", top_k=3) == []


def test_top_matching_chunks_no_query_terms_falls_back():
    chunks = chunk_text("some content here " * 10, chunk_size=50, overlap=5)
    result = top_matching_chunks(chunks, "", top_k=2)
    assert len(result) == 2
    assert result[0].index == chunks[0].index
