# ⚖️ Legal AI Assistant

A lightweight, production-ready GenAI application that makes legal documents
understandable. It simplifies dense legal text, extracts clauses/obligations/
risks, compares two agreements side-by-side, answers grounded legal Q&A, and
produces structured summaries and checklists — all with clear
**"Not legal advice"** disclaimers throughout.

> **Disclaimer:** This tool provides general informational assistance only.
> It does **not** constitute legal advice and does **not** create an
> attorney-client relationship. Always consult a licensed attorney for advice
> on your specific situation.

---

## 1. Architecture

```
legal_ai_assistant/
├── app.py                     # Streamlit UI entry point (single-command run)
├── backend/
│   ├── __init__.py
│   ├── config.py               # Environment/config loader (pydantic)
│   ├── ai_client.py             # Provider-agnostic AI interface (Claude/OpenAI/Mock)
│   ├── chunking.py              # Token-efficient text chunking utilities
│   ├── security.py              # Input sanitization + PII masking simulation
│   ├── document_parser.py       # Clause/obligation/risk extraction logic
│   ├── comparator.py            # Side-by-side agreement comparison
│   ├── qa_engine.py              # Context-grounded legal Q&A (retrieval + prompt)
│   └── summarizer.py            # Structured summaries & checklists
├── frontend/
│   └── styles.py                 # WCAG 2.1 AA accessible CSS injected into Streamlit
├── tests/
│   ├── __init__.py
│   ├── test_security.py
│   ├── test_chunking.py
│   ├── test_document_parser.py
│   ├── test_comparator.py
│   ├── test_qa_engine.py
│   └── test_summarizer.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Design principles

- **Provider-agnostic AI layer** (`backend/ai_client.py`): a single
  `AIClient` interface with four interchangeable backends — **Groq**
  (Llama models, OpenAI-compatible API, fast + free-tier-friendly),
  Anthropic Claude, OpenAI, and a deterministic **Mock** engine. If no API
  key is configured, the app automatically falls back to Mock mode so it is
  fully functional out of the box, with no external calls and no cost.
  Auto-detection order when `AI_PROVIDER` is left unset: Groq → Anthropic →
  OpenAI → Mock, based on whichever key is present in `.env`.
- **Security-first**: all user input passes through `backend/security.py`
  before touching the AI layer or being rendered back to the screen —
  sanitizing HTML/script injection attempts and simulating PII masking
  (emails, phone numbers, SSN-like numbers, card numbers) before any text is
  sent to a third-party model.
- **Token efficiency**: `backend/chunking.py` splits long documents into
  overlapping chunks sized for the model's context window, only sending the
  chunks relevant to a task (e.g., top-matching chunks for Q&A) rather than
  the entire document every time.
- **Accessibility**: `frontend/styles.py` injects a high-contrast,
  keyboard-navigable, semantic-HTML-friendly theme; every Streamlit widget
  used includes a proper `label`/`help` string (never `label_visibility="collapsed"`
  without an accessible alternative), and focus states are preserved.

---

## 2. Quickstart

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) configure an AI provider
cp .env.example .env
# edit .env and set GROQ_API_KEY (recommended — get one free at
# https://console.groq.com/keys), or ANTHROPIC_API_KEY / OPENAI_API_KEY
# — or leave everything blank to run fully offline in Mock mode

# 4. Run the app (single command)
streamlit run app.py
```

The app opens at `http://localhost:8501`. Without any API key configured, it
runs in **Mock mode**: fully functional, deterministic, offline responses
useful for demos, grading, and CI — no network calls are made.

---

## 3. Using the app

The sidebar lets you pick a mode:

1. **📄 Simplify & Summarize** — paste or upload a contract; get a plain-English
   summary, a clause-by-clause breakdown, an obligations checklist, and a
   flagged risk list.
2. **⚖️ Compare Agreements** — paste two documents (e.g., two vendor
   contracts); get a structured, side-by-side diff of clauses, obligations,
   and risk differences.
3. **💬 Ask a Question (Grounded Q&A)** — upload/paste a document, then ask
   questions; answers are grounded strictly in the document's retrieved
   chunks, with citations back to the source excerpt, and a refusal path
   when the document does not contain the answer.

Every screen displays a persistent **"⚠️ Not legal advice"** banner.

---

## 4. API guide (`backend/ai_client.py`)

```python
from backend.ai_client import AIClient

client = AIClient()                      # auto-detects provider from .env
reply = client.complete(
    system="You are a careful legal-document analysis assistant.",
    prompt="Summarize the key obligations in this clause: ...",
    max_tokens=500,
)
print(reply.text)
print(reply.provider)   # "groq" | "anthropic" | "openai" | "mock"
```

### Using Groq

1. Create a free key at [console.groq.com/keys](https://console.groq.com/keys).
2. In `.env`, set:
   ```
   AI_PROVIDER=groq
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   ```
   Check [console.groq.com/docs/models](https://console.groq.com/docs/models)
   for the current model list before choosing `GROQ_MODEL` — Groq
   periodically moves models (e.g. Llama 3.x) behind an Enterprise-only
   plan, which shows up as a `NotFoundError` on a standard developer key if
   you request one of those. `openai/gpt-oss-20b` and `openai/gpt-oss-120b`
   are available on a standard developer key as of late 2026.
3. Run `streamlit run app.py` — no other changes needed. Groq is called
   through the OpenAI-compatible `openai` Python SDK pointed at Groq's
   endpoint (`https://api.groq.com/openai/v1`), so no extra dependency is
   required beyond what's already in `requirements.txt`.

`AIClient.complete()` returns an `AIResponse` (a small dataclass with
`text`, `provider`, and `used_mock` fields) and never raises a raw provider
exception to callers — network/auth errors are caught and converted into a
safe, user-facing message plus automatic fallback to Mock mode, so the UI
never crashes and no stack traces leak to the user.

---

## 5. Security notes

- **Input sanitization**: `security.sanitize_text()` strips HTML tags,
  script/style blocks, and control characters from all pasted/uploaded text
  before it is parsed, summarized, or displayed.
- **PII masking simulation**: `security.mask_pii()` detects and redacts
  emails, phone numbers, SSN-like sequences, and 13–19 digit card-like
  numbers, replacing them with typed placeholders (e.g., `[EMAIL_REDACTED]`)
  before any text leaves the process boundary to a third-party AI provider.
- **No stack leakage**: all provider/network calls are wrapped in
  `try/except`, and only a generic, user-safe error string is ever surfaced;
  full details are captured only in local logs (`LOG_LEVEL` in `.env`).
- **Secrets**: API keys are read from environment variables, local `.env`, or
  Streamlit Secrets; `.env` is git-ignored, and `.env.example` ships with
  empty placeholders only.
- **Bounded requests and uploads**: provider calls use a 30-second timeout,
  input text is capped by `MAX_UPLOAD_CHARS`, and Streamlit uploads are capped
  at 10 MB with XSRF protection enabled.
- **OWASP alignment**: covers A03 (Injection) via sanitization, A02
  (Cryptographic/Sensitive Data Exposure) via PII masking + no key logging,
  A05 (Security Misconfiguration) via safe defaults (Mock mode with no
  network access unless explicitly configured), and A09 (Logging failures)
  via structured, leak-free error handling.

---

## 6. Testing

```bash
pytest -v --cov=backend tests/
```

The suite covers: input sanitization and PII masking (`test_security.py`),
chunking correctness/edge cases (`test_chunking.py`), clause/obligation/risk
parsing (`test_document_parser.py`), document comparison logic
(`test_comparator.py`), grounded Q&A retrieval and refusal behavior
(`test_qa_engine.py`), and structured summary/checklist generation
(`test_summarizer.py`). All tests run fully offline against Mock-mode
responses — no API key or network access is required in CI.

---

## 7. Efficiency

- Repository footprint is source-only (no vendored binaries/models) — well
  under 10 MB.
- Chunking (`CHUNK_SIZE_CHARS` / `CHUNK_OVERLAP_CHARS` in `.env`) keeps
  prompts small; Q&A only sends the top-matching chunks, not the full
  document, minimizing token usage and latency.
- The Mock provider is deterministic and instant, so demos and tests never
  wait on network latency.
- Production installs contain runtime dependencies only, while GitHub Actions
  runs `pip-audit` on every push and pull request.

---

## 8. Legal disclaimer

This project is an educational/demonstration tool. It is **not** a
substitute for professional legal advice. Always consult a qualified
attorney licensed in your jurisdiction before acting on any output produced
by this application.
