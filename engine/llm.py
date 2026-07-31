import os
import time
import json
import requests
from typing import Generator, Tuple, Optional

from engine.prompts import RAG_SYSTEM_PROMPT


class GroqClient:
    """Native Groq REST API client — direct HTTP, no SDK / no LangChain."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    @classmethod
    def _resolve_key(cls, api_key: Optional[str] = None) -> str:
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key or not key.strip():
            raise ValueError("Groq API key is missing. Add it in Settings or your .env file.")
        return key.strip()

    @classmethod
    def generate(
        cls,
        model_name: str,
        query: str,
        context: str,
        api_key: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Tuple[str, float]:
        """Synchronous, non-streamed generation. Returns (answer_text, latency_ms)."""
        key = cls._resolve_key(api_key)
        prompt = RAG_SYSTEM_PROMPT.format(context=context, question=query)

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        start = time.time()
        resp = requests.post(cls.API_URL, headers=headers, json=payload, timeout=30)
        latency_ms = (time.time() - start) * 1000.0

        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        return answer, latency_ms

    @classmethod
    def stream(
        cls,
        model_name: str,
        query: str,
        context: str,
        api_key: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Generator[str, None, None]:
        """Stream response tokens directly from the Groq API."""
        key = cls._resolve_key(api_key)
        prompt = RAG_SYSTEM_PROMPT.format(context=context, question=query)

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True,
        }

        resp = requests.post(cls.API_URL, headers=headers, json=payload, stream=True, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error ({resp.status_code}): {resp.text}")

        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: ") and decoded != "data: [DONE]":
                try:
                    chunk = json.loads(decoded[6:])
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]
                except Exception:
                    continue
