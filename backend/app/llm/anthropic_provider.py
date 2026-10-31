"""Anthropic Claude API provider adapter."""
import json
import httpx
from app.llm.base import LLMProvider
from app.config import settings
import logging

logger = logging.getLogger("knowledgevault.anthropic")


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = settings.LLM_MODEL):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY or settings.LLM_API_KEY
        self.model = model if model != "mock-expert-v1" else "claude-3-5-sonnet-20241022"
        self.base_url = "https://api.anthropic.com/v1"

    def generate(self, prompt: str, system_prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing. Set LLM_API_KEY in .env.")

        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data["content"][0]["text"]
