"""LLM service for interacting with different providers."""

from typing import AsyncGenerator, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.exceptions import LLMProviderError


class LLMService:
    """Service for LLM interactions."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.model = model or settings.DEFAULT_LLM_MODEL
        self._client = self._get_client()

    def _get_client(self) -> BaseChatModel:
        """Initialize the LLM client based on provider."""
        if self.provider == "groq":
            if not settings.GROQ_API_KEY:
                raise LLMProviderError("GROQ_API_KEY not set in environment")
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=self.model,
                temperature=0.2,
                max_tokens=4096,
            )
        # Add OpenAI/Ollama later if needed
        raise LLMProviderError(f"Unsupported provider: {self.provider}")

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = await self._client.ainvoke(messages)
            return response.content
        except Exception as e:
            raise LLMProviderError(f"LLM chat failed: {str(e)}")

    def chat_sync(self, system_prompt: str, user_prompt: str) -> str:
        """Synchronous chat completion."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = self._client.invoke(messages)
            return response.content
        except Exception as e:
            raise LLMProviderError(f"LLM chat failed: {str(e)}")

    def get_client(self) -> BaseChatModel:
        """Return raw LangChain client for advanced use."""
        return self._client


# Singleton instance
llm_service = LLMService()