"""LLM Service with rate limit handling + fallback model."""

import time
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings


class LLMService:
    def __init__(self):
        self._client = None
        # ✅ HARDCODED: Use smaller model with higher rate limits
        self.primary_model = "llama-3.1-8b-instant"
        self.fallback_model = "gemma2-9b-it"  # Fallback if primary rate limited

    def _get_client(self, model_name: Optional[str] = None):
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key == "dummy":
            raise Exception("GROQ_API_KEY not set in Render Environment")
        
        model = model_name or self.primary_model
        
        return ChatGroq(
            api_key=api_key,
            model_name=model,
            temperature=0.3,
            max_tokens=2048,
        )

    def chat_sync(self, system_prompt: str, user_prompt: str, max_retries: int = 5) -> str:
        """
        Call LLM with rate limit retry + model fallback.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Try primary model first
        for attempt in range(1, max_retries + 1):
            try:
                client = self._get_client(self.primary_model)
                response = client.invoke(messages)
                return response.content
            except Exception as e:
                error_str = str(e).lower()
                
                if "429" in error_str or "rate limit" in error_str:
                    wait_time = attempt * 4  # 4s, 8s, 12s, 16s, 20s
                    if attempt < max_retries:
                        print(f"⏳ Rate limited (attempt {attempt}/{max_retries}). Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Last attempt on primary failed
                if attempt == max_retries:
                    break
                time.sleep(2)

        # ✅ FALLBACK: Try different model
        print(f"🔄 Switching to fallback model: {self.fallback_model}")
        try:
            client = self._get_client(self.fallback_model)
            response = client.invoke(messages)
            return response.content
        except Exception as e:
            # If fallback also fails, return error
            return f"Sorry, I couldn't generate an answer. Error: {str(e)[:200]}"

    def chat_sync_simple(self, prompt: str, max_retries: int = 3) -> str:
        """Simpler interface for quick calls."""
        return self.chat_sync(
            "You are a helpful AI assistant.",
            prompt,
            max_retries=max_retries
        )


# Singleton
llm_service = LLMService()