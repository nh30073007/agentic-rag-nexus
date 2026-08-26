"""LLM Service - Ollama (Phi3) - Timeout & Streaming Fixed"""

import time
import logging
import asyncio
from typing import Optional, AsyncGenerator

from langchain_ollama import OllamaLLM

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.ollama_model = getattr(settings, "OLLAMA_MODEL", "phi3")
        self.ollama_base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_timeout = getattr(settings, "OLLAMA_TIMEOUT", 300)
        self.num_predict = getattr(settings, "OLLAMA_NUM_PREDICT", 512)
        self.temperature = getattr(settings, "OLLAMA_TEMPERATURE", 0.3)
        
        self.last_used_model = None
        self.last_error = None
        
        logger.info(f"🚀 LLM Service initialized")
        logger.info(f"📋 Model: {self.ollama_model}")
        logger.info(f"📋 Ollama URL: {self.ollama_base_url}")
        logger.info(f"⏱️ Timeout: {self.ollama_timeout}s")
        logger.info(f"🔢 Max Tokens: {self.num_predict}")

    def _get_ollama_client(self):
        """Ollama ক্লায়েন্ট তৈরি করুন"""
        try:
            return OllamaLLM(
                model=self.ollama_model,
                base_url=self.ollama_base_url,
                temperature=self.temperature,
                num_predict=self.num_predict,
                timeout=self.ollama_timeout,
            )
        except Exception as e:
            logger.error(f"❌ Failed to create Ollama client: {e}")
            return None

    def _truncate_prompt(self, prompt: str, max_chars: int = 2500) -> str:
        """প্রম্পট লিমিটে রাখুন (Phi3-এর জন্য আরও ছোট)"""
        if len(prompt) > max_chars:
            logger.warning(f"✂️ Prompt truncated: {len(prompt)} → {max_chars} chars")
            return prompt[:max_chars] + "\n\n[Context truncated]"
        return prompt

    def chat_sync(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> str:
        """সিঙ্ক্রোনাস উত্তর তৈরি"""
        full_prompt = self._truncate_prompt(f"{system_prompt}\n\nUser: {user_prompt}")
        logger.info(f"📝 Prompt length: {len(full_prompt)} chars")
        
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Attempt {attempt}/{max_retries}")
                
                client = self._get_ollama_client()
                if not client:
                    raise Exception("Failed to create Ollama client")
                
                response = client.invoke(full_prompt)
                
                if response and len(response.strip()) > 5:
                    self.last_used_model = self.ollama_model
                    logger.info(f"✅ Response: {len(response)} chars")
                    return response.strip()
                else:
                    logger.warning(f"⚠️ Empty/short response, retrying...")
                    if attempt < max_retries:
                        time.sleep(1)
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Attempt {attempt} failed: {str(e)[:150]}")
                if attempt < max_retries:
                    time.sleep(2)
        
        error_msg = (
            f"⚠️ Ollama couldn't generate an answer after {max_retries} tries. "
            f"Error: {str(last_error)[:200] if last_error else 'Unknown error'}. "
            f"Please check if Ollama is running: ollama run {self.ollama_model}"
        )
        logger.error(error_msg)
        return error_msg

    async def chat_async(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> str:
        """অ্যাসিঙ্ক্রোনাস wrapper"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.chat_sync, 
            system_prompt, 
            user_prompt, 
            max_retries
        )

    async def chat_stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """STREAMING: টোকেন বাই টোকেন রেসপন্স"""
        full_prompt = self._truncate_prompt(f"{system_prompt}\n\nUser: {user_prompt}")
        
        try:
            client = self._get_ollama_client()
            if not client:
                yield "❌ Ollama client failed to initialize."
                return
            
            for chunk in client.stream(full_prompt):
                if chunk:
                    yield str(chunk)
                    
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            yield f"\n\n⚠️ Error during generation: {str(e)[:150]}"

    def chat_sync_simple(self, prompt: str) -> str:
        """সরল ইন্টারফেস"""
        return self.chat_sync(
            system_prompt="You are a helpful AI assistant. Provide clear, concise, and accurate answers.",
            user_prompt=prompt
        )

    def health_check(self) -> dict:
        """Ollama রানিং কিনা চেক করুন"""
        try:
            client = self._get_ollama_client()
            if client:
                resp = client.invoke("Say 'ok'")
                return {
                    "status": "healthy",
                    "provider": "ollama",
                    "model": self.ollama_model,
                    "response": resp[:50] if resp else "No response"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "ollama",
                "model": self.ollama_model,
                "error": str(e)[:200]
            }
        return {"status": "unknown", "provider": "ollama"}

    def get_model_info(self) -> dict:
        return {
            "provider": "ollama",
            "model": self.ollama_model,
            "url": self.ollama_base_url,
            "timeout": self.ollama_timeout,
            "max_tokens": self.num_predict,
            "last_used": self.last_used_model,
            "last_error": str(self.last_error)[:200] if self.last_error else None,
        }


# Singleton
llm_service = LLMService()