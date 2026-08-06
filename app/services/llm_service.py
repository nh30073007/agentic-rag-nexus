"""LLM Service with rate limit handling."""

import time
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings


class LLMService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            api_key = settings.GROQ_API_KEY or "dummy"
            self._client = ChatGroq(
                api_key=api_key,
                model_name=settings.DEFAULT_LLM_MODEL,
                temperature=0.3,
                max_retries=3,  # Built-in retry
            )
        return self._client

    def chat_sync(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """
        Call LLM with rate limit retry (exponential backoff).
        """
        client = self._get_client()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        for attempt in range(1, max_retries + 1):
            try:
                response = client.invoke(messages)
                return response.content
            except Exception as e:
                error_str = str(e).lower()
                
                # Rate limit detected
                if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                    wait_time = attempt * 3  # 3s, 6s, 9s
                    if attempt < max_retries:
                        print(f"⏳ Rate limited (attempt {attempt}/{max_retries}). Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Last attempt failed
                if attempt == max_retries:
                    raise Exception(f"LLM chat failed after {max_retries} attempts: {str(e)}")
                
                # Other error, retry once
                time.sleep(1)

        return "Error: All retries exhausted"


# Singleton
llm_service = LLMService()