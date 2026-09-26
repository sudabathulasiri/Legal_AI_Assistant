"""
Provider-agnostic AI interface.

Exposes a single `AIClient.complete()` method backed interchangeably by
Anthropic Claude, OpenAI, or a fully offline, deterministic Mock engine.
Network/auth failures are always caught and converted into a safe fallback
response — callers never see a raw provider exception or stack trace.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

import requests

from backend.config import load_settings
from backend.security import safe_error_message

logger = logging.getLogger("legal_ai_assistant.ai_client")


@dataclass(frozen=True)
class AIResponse:
    """Normalized response returned by every provider backend."""

    text: str
    provider: str
    used_mock: bool


class AIClient:
    """
    Thin, provider-agnostic facade. Construct once and call `.complete()`
    with a system prompt and a user prompt; the correct backend is chosen
    automatically from configuration, with graceful fallback to Mock mode
    on any error.
    """

    def __init__(self, provider: str | None = None):
        self.settings = load_settings()
        logger.setLevel(self.settings.log_level)
        self.provider = (provider or self.settings.resolved_provider()).lower()

    def complete(self, system: str, prompt: str, max_tokens: int = 800) -> AIResponse:
        """Generate a completion using the configured provider, with safe fallback."""
        if self.provider == "groq":
            try:
                return self._complete_groq(system, prompt, max_tokens)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Groq call failed, falling back to mock: %s", type(exc).__name__)
                return self._complete_mock(system, prompt, max_tokens, note=safe_error_message(exc))

        if self.provider == "anthropic":
            try:
                return self._complete_anthropic(system, prompt, max_tokens)
            except Exception as exc:  # noqa: BLE001 - intentional broad catch at the boundary
                logger.warning("Anthropic call failed, falling back to mock: %s", type(exc).__name__)
                return self._complete_mock(system, prompt, max_tokens, note=safe_error_message(exc))

        if self.provider == "openai":
            try:
                return self._complete_openai(system, prompt, max_tokens)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OpenAI call failed, falling back to mock: %s", type(exc).__name__)
                return self._complete_mock(system, prompt, max_tokens, note=safe_error_message(exc))

        return self._complete_mock(system, prompt, max_tokens)

    # -- Real providers -------------------------------------------------

    def _complete_groq(self, system: str, prompt: str, max_tokens: int) -> AIResponse:
        """
        Groq exposes an OpenAI-compatible chat-completions API. We call it
        directly here instead of going through the `openai` SDK because the
        SDK's transitive HTTP client stack can mismatch the local environment
        and fail before the request is sent.
        """
        payload = {
            "model": self.settings.groq_model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.groq_api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "LegalAIAssistant/1.0",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as exc:
            response = exc.response
            detail = ""
            if response is not None:
                detail = response.text[:500]
            raise RuntimeError(f"Groq HTTP error {response.status_code if response else 'unknown'}: {detail or str(exc)}") from exc

        message = data["choices"][0]["message"]
        text = (message.get("content") or message.get("reasoning") or "").strip()
        return AIResponse(text=text, provider="groq", used_mock=False)

    def _complete_anthropic(self, system: str, prompt: str, max_tokens: int) -> AIResponse:
        import anthropic

        client = anthropic.Anthropic(
            api_key=self.settings.anthropic_api_key,
            timeout=30.0,
        )
        response = client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text_parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return AIResponse(text="\n".join(text_parts).strip(), provider="anthropic", used_mock=False)

    def _complete_openai(self, system: str, prompt: str, max_tokens: int) -> AIResponse:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key, timeout=30.0)
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        return AIResponse(text=text, provider="openai", used_mock=False)

    # -- Mock provider ----------------------------------------------------

    def _complete_mock(self, system: str, prompt: str, max_tokens: int, note: str = "") -> AIResponse:
        """
        Deterministic, offline, zero-cost mock generator. Produces
        structured, plausible legal-analysis-style text derived from the
        prompt so the whole app is fully demonstrable without any API key.
        """
        digest = hashlib.sha256((system + prompt).encode("utf-8")).hexdigest()[:8]
        excerpt = prompt.strip().replace("\n", " ")
        excerpt = excerpt[:220] + ("..." if len(excerpt) > 220 else "")

        body = (
            f"[MOCK MODE — offline deterministic response, ref {digest}]\n"
            f"Based on the supplied text, here is a general-purpose structured analysis:\n\n"
            f"- Key topic detected from input: \"{excerpt}\"\n"
            "- Obligations: the parties appear to owe each other performance, payment, "
            "and/or confidentiality duties as described in the source text.\n"
            "- Risks: watch for auto-renewal, liability, indemnification, and termination "
            "clauses, which commonly carry the most risk in agreements of this kind.\n"
            "- Recommendation: review flagged clauses with a licensed attorney before "
            "signing or relying on this document.\n\n"
            "This is not legal advice. Configure GROQ_API_KEY (recommended), "
            "ANTHROPIC_API_KEY, or OPENAI_API_KEY in your .env file for live, "
            "model-generated analysis."
        )
        if note:
            body = f"{note}\n\n{body}"
        return AIResponse(text=body[: max_tokens * 6], provider="mock", used_mock=True)
