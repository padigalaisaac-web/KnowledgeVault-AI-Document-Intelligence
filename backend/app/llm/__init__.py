"""LLM provider factory."""
from typing import Optional
from app.config import settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.ollama_provider import OllamaProvider


def get_llm_provider(name: Optional[str] = None) -> LLMProvider:
    """Return configured LLM provider instance with intelligent environment key detection."""
    provider_name = (name or settings.LLM_PROVIDER or "").lower()

    # If provider is mock or unset, check if user provided an external API key on Render
    if not provider_name or provider_name == "mock":
        if settings.GEMINI_API_KEY:
            provider_name = "gemini"
        elif settings.OPENAI_API_KEY:
            provider_name = "openai"
        elif settings.ANTHROPIC_API_KEY:
            provider_name = "anthropic"
        else:
            provider_name = "mock"

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "ollama":
        return OllamaProvider()
    else:
        return MockProvider()
