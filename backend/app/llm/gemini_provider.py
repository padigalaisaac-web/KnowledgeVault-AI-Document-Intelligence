"""Google Gemini API provider adapter."""
import json
import httpx
from app.llm.base import LLMProvider
from app.config import settings
import logging

logger = logging.getLogger("knowledgevault.gemini")


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = settings.LLM_MODEL):
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.LLM_API_KEY
        self.model = model if model != "mock-expert-v1" else "gemini-1.5-flash"

    def generate(self, prompt: str, system_prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is missing. Set LLM_API_KEY in .env.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
