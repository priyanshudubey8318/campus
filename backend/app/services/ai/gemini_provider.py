"""Google Gemini AI provider implementation using HTTP REST API."""

import logging
import time
from typing import List, Optional
import httpx

from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.protocols import AIProviderProtocol, AIResponse

logger = logging.getLogger(__name__)


class GeminiProvider(AIProviderProtocol):
    """Production AI provider interacting with Google Gemini models via REST."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        embedding_model: str = "text-embedding-004",
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.provider_name = "gemini"
        self._fallback = MockAIProvider(model_name=f"fallback-{model_name}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate 768-dimensional embedding vector using text-embedding-004."""
        if not self.api_key:
            logger.debug("No GEMINI_API_KEY configured; using deterministic mock embedding")
            return self._fallback.generate_embedding(text)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.embedding_model}",
            "content": {"parts": [{"text": text}]},
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    values = data.get("embedding", {}).get("values", [])
                    if values and len(values) == 768:
                        return values
                    logger.warning("Gemini embedding returned unexpected dimension; falling back")
                else:
                    logger.warning("Gemini embedding API returned status %d: %s", res.status_code, res.text)
        except Exception as e:
            logger.warning("Gemini embedding failed with error: %s; using fallback", str(e))

        return self._fallback.generate_embedding(text)

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Generate completion using Gemini generateContent."""
        if not self.api_key:
            logger.debug("No GEMINI_API_KEY configured; using deterministic mock response")
            return self._fallback.generate_response(prompt, system_prompt, temperature, max_tokens)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in text_parts)
                        usage = data.get("usageMetadata", {})
                        return AIResponse(
                            text=text,
                            prompt_tokens=usage.get("promptTokenCount", len(prompt) // 4),
                            completion_tokens=usage.get("candidatesTokenCount", len(text) // 4),
                            latency_ms=latency_ms,
                            model_name=self.model_name,
                            provider_name=self.provider_name,
                        )
                    logger.warning("Gemini returned no candidates; using fallback")
                else:
                    logger.warning("Gemini generation API returned status %d: %s", res.status_code, res.text)
        except Exception as e:
            logger.warning("Gemini generation failed with error: %s; using fallback", str(e))

        return self._fallback.generate_response(prompt, system_prompt, temperature, max_tokens)
