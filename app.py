"""
Legal AI Assistant — Streamlit entry point.

Run with:  streamlit run app.py

Provides three accessible modes: Simplify & Summarize, Compare Agreements,
and grounded Q&A — all clearly marked as NOT legal advice.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from backend.ai_client import AIClient
from backend.comparator import compare_documents
from backend.document_parser import parse_document
from backend.qa_engine import answer_question
from backend.security import sanitize_text
from backend.summarizer import build_summary, summary_to_markdown
from frontend.styles import ACCESSIBLE_CSS

st.set_page_config(page_title="Legal AI Assistant", page_icon="⚖️", layout="wide")
st.markdown(ACCESSIBLE_CSS, unsafe_allow_html=True)

_ENV_PATH = Path(__file__).resolve().with_name(".env")

DISCLAIMER_HTML = (
    '<div class="lai-disclaimer" role="alert">'
    "⚠️ <strong>Not legal advice.</strong> This tool provides general informational "
    "assistance only and does not create an attorney-client relationship. "
    "Consult a licensed attorney for advice about your specific situation."
    "</div>"
)


@st.cache_resource
def get_ai_client(env_signature: int) -> AIClient:
    """Cache a single AIClient instance across reruns within a session."""
    return AIClient()


def get_env_signature() -> int:
    """Return a stable signature that changes when the local .env file changes."""
    try:
        stat = _ENV_PATH.stat()
        return int(stat.st_mtime_ns ^ stat.st_size)
    except FileNotFoundError:
        return 0


def read_uploaded_or_pasted(uploaded_file, pasted_text: str) -> str:
    """Prefer an uploaded .txt file's content; fall back to pasted text."""
    if uploaded_file is not None:
        try:
            raw_bytes = uploaded_file.read()
            return raw_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return pasted_text
    return pasted_text


def main() -> None:
    st.title("⚖️ Legal AI Assistant")
    st.markdown(DISCLAIMER_HTML, unsafe_allow_html=True)

    client = get_ai_client(get_env_signature())
    provider_label = {
        "groq": "Groq (Llama)",
        "anthropic": "Anthropic Claude",
        "openai": "OpenAI",
        "mock": "Offline Mock Mode",
    }
    st.caption(f"AI backend: **{provider_label.get(client.provider, client.provider)}**")

    mode = st.sidebar.radio(
        "Choose a task",
        ["📄 Simplify & Summarize", "⚖️ Compare Agreements", "💬 Ask a Question (Grounded Q&A)"],
        help="Select which legal-assistance task you want to perform.",
    )

    if mode == "📄 Simplify & Summarize":
        render_simplify_tab(client)
    elif mode == "⚖️ Compare Agreements":
        render_compare_tab(client)
    else:
        render_qa_tab(client)


def render_simplify_tab(client: AIClient) -> None:
    st.markdown('<div class="lai-section">', unsafe_allow_html=True)
    st.header("Simplify & Summarize a Document")
    st.markdown("</div>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload a plain-text contract (.txt)",
        type=["txt"],
        help="Upload a .txt file containing the agreement you want analyzed.",
        key="simplify_uploader",
    )
    pasted = st.text_area(
        "Or paste the contract text here",
        height=240,
        help="Paste the full text of the agreement you want simplified.",
        key="simplify_textarea",
    )

    if st.button("Analyze document", key="simplify_button"):
        raw_text = read_uploaded_or_pasted(uploaded, pasted)
        clean = sanitize_text(raw_text)
        if not clean.strip():
            st.warning("Please upload or paste some document text first.")
            return

        with st.spinner("Analyzing document..."):
            parsed = parse_document(clean, ai_client=client)
            summary = build_summary(clean, ai_client=client, parsed=parsed)

        st.subheader("Plain-Language Summary")
        st.write(summary.plain_summary)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="lai-section">', unsafe_allow_html=True)
            st.subheader("✅ Obligations Checklist")
            if summary.obligations_checklist:
                for item in summary.obligations_checklist:
                    st.checkbox(item, key=f"ob_{hash(item)}")
            else:
                st.write("No explicit obligations detected.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="lai-section">', unsafe_allow_html=True)
            st.subheader("⚠️ Flagged Risks")
            if summary.risk_flags:
                for item in summary.risk_flags:
                    st.markdown(f'<p class="lai-risk">⚠️ {item}</p>', unsafe_allow_html=True)
            else:
                st.write("No high-risk clauses detected by keyword screening.")
            st.markdown("</div>", unsafe_allow_html=True)

        markdown_export = summary_to_markdown(summary)
        st.download_button(
            "Download summary as Markdown",
            data=markdown_export,
            file_name="legal_summary.md",
            mime="text/markdown",
            help="Download the structured summary, checklist, and risk flags as a Markdown file.",
        )


def render_compare_tab(client: AIClient) -> None:
    st.markdown('<div class="lai-section">', unsafe_allow_html=True)
    st.header("Compare Two Agreements Side-by-Side")
    st.markdown("</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        text_a = st.text_area("Agreement A", height=220, help="Paste the first agreement's text.", key="compare_a")
    with col_b:
        text_b = st.text_area("Agreement B", height=220, help="Paste the second agreement's text.", key="compare_b")

    if st.button("Compare agreements", key="compare_button"):
        clean_a = sanitize_text(text_a)
        clean_b = sanitize_text(text_b)
        if not clean_a.strip() or not clean_b.strip():
            st.warning("Please provide text for both Agreement A and Agreement B.")
            return

        with st.spinner("Comparing documents..."):
            result = compare_documents(clean_a, clean_b, ai_client=client)

        st.subheader("Key Differences")
        st.write(result.ai_comparison_summary)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="lai-section">', unsafe_allow_html=True)
            st.markdown('<p class="lai-obligation">Obligations only in Agreement A</p>', unsafe_allow_html=True)
            st.write(result.only_in_a_obligations or "None")
            st.markdown('<p class="lai-risk">Risks only in Agreement A</p>', unsafe_allow_html=True)
            st.write(result.only_in_a_risks or "None")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="lai-section">', unsafe_allow_html=True)
            st.markdown('<p class="lai-obligation">Obligations only in Agreement B</p>', unsafe_allow_html=True)
            st.write(result.only_in_b_obligations or "None")
            st.markdown('<p class="lai-risk">Risks only in Agreement B</p>', unsafe_allow_html=True)
            st.write(result.only_in_b_risks or "None")
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Shared Obligations & Risks")
        st.write({"shared_obligations": result.shared_obligations, "shared_risks": result.shared_risks})


def render_qa_tab(client: AIClient) -> None:
    st.markdown('<div class="lai-section">', unsafe_allow_html=True)
    st.header("Ask a Question About Your Document")
    st.markdown("</div>", unsafe_allow_html=True)

    doc_text = st.text_area(
        "Paste the document to ask questions about",
        height=220,
        help="Paste the agreement or legal text you want to ask questions about.",
        key="qa_doc",
    )
    question = st.text_input(
        "Your question",
        help="Ask a specific question about the document above. Answers are grounded strictly in this text.",
        key="qa_question",
    )

    if st.button("Get grounded answer", key="qa_button"):
        clean_doc = sanitize_text(doc_text)
        clean_question = sanitize_text(question, max_len=2000)
        if not clean_doc.strip() or not clean_question.strip():
            st.warning("Please provide both a document and a question.")
            return

        with st.spinner("Retrieving relevant context and answering..."):
            result = answer_question(clean_doc, clean_question, ai_client=client)

        st.subheader("Answer")
        if result.grounded:
            st.success(result.answer)
        else:
            st.info(result.answer)

        if result.source_excerpts:
            with st.expander("View source excerpts used to ground this answer"):
                for i, excerpt in enumerate(result.source_excerpts, start=1):
                    st.markdown(f"**Excerpt {i}:**")
                    st.write(excerpt)


if __name__ == "__main__":
    main()
