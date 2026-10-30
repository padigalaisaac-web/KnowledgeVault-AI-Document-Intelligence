"""Ollama local model provider adapter."""
import json
import httpx
from app.llm.base import LLMProvider
from app.config import settings
import logging

logger = logging.getLogger("knowledgevault.ollama")


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = None, model: str = settings.LLM_MODEL):
        self.base_url = (base_url or settings.LLM_API_BASE or "http://localhost:11434").rstrip("/")
        self.model = model if model != "mock-expert-v1" else "llama3.2"

    def generate(self, prompt: str, system_prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }

        with httpx.Client(timeout=120.0) as client:
            res = client.post(url, json=payload)
            res.raise_for_status()
            return res.json().get("response", "")
