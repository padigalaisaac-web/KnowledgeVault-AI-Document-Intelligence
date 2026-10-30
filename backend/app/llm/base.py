"""Abstract base class for LLM providers."""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Generic interface for LLM model providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate full completion string."""
        pass
