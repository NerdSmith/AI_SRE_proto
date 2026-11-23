import json
import os
import time
from dataclasses import dataclass

import httpx
from pydantic import BaseModel


@dataclass
class Completion:
    data: dict
    prompt_tokens: int
    completion_tokens: int
    seconds: float


class LlmClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("LLM_URL", "http://localhost:8080/v1")).rstrip("/")

    def complete(self, system: str, user: str, schema: type[BaseModel]) -> Completion:
        payload = {
            "model": "local",
            "temperature": 0,
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
            },
            "chat_template_kwargs": {"enable_thinking": False},
        }
        started = time.monotonic()
        response = httpx.post(f"{self.base_url}/chat/completions", json=payload, timeout=900)
        if response.is_error:
            raise RuntimeError(f"llm error {response.status_code}: {response.text[:500]}")
        body = response.json()
        usage = body.get("usage", {})
        return Completion(
            data=json.loads(body["choices"][0]["message"]["content"]),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            seconds=time.monotonic() - started,
        )
