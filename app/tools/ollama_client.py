from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = self.settings.enable_llm_synthesis

    def health(self) -> str:
        try:
            response = httpx.get(f"{self.settings.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            return "ok"
        except Exception as exc:
            logger.warning("Ollama health check failed: %s", exc)
            return "down"

    def chat(self, prompt: str, model: str | None = None) -> str | None:
        if not self.enabled:
            return None
        payload = {
            "model": model or self.settings.default_model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = httpx.post(
                f"{self.settings.ollama_url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            body = response.json()
            return body.get("message", {}).get("content")
        except Exception as exc:
            logger.warning("Ollama chat failed: %s", exc)
            return None
