"""OpenAI API provider adapter."""
import json
import httpx
from app.llm.base import LLMProvider
from app.config import settings
import logging

logger = logging.getLogger("knowledgevault.openai")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = settings.LLM_MODEL, base_url: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or settings.LLM_API_KEY
        self.model = model if model != "mock-expert-v1" else "gpt-4o-mini"
        self.base_url = (base_url or settings.LLM_API_BASE or "https://api.openai.com/v1").rstrip("/")

    def generate(self, prompt: str, system_prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set LLM_API_KEY in .env or choose MockProvider.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
