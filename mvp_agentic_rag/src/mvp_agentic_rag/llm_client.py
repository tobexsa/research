from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any


class LLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError


@dataclass
class FakeLLMClient(LLMClient):
    responses: list[str]
    calls: list[list[dict[str, str]]] = field(default_factory=list)

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        if not self.responses:
            return ""
        if len(self.responses) == 1:
            return self.responses[0]
        return self.responses.pop(0)


@dataclass
class OpenAICompatibleClient(LLMClient):
    base_url: str
    model: str
    api_key_env: str = "OPENAI_API_KEY"
    timeout: int = 60
    temperature: float = 0.0
    max_tokens: int = 512
    disable_reasoning: bool = False

    def complete(self, messages: list[dict[str, str]]) -> str:
        api_key = os.environ.get(self.api_key_env, "")
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": prepare_messages(messages, disable_reasoning=self.disable_reasoning),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return extract_message_content(body)


def extract_message_content(payload: dict[str, Any]) -> str:
    try:
        return strip_think_blocks(str(payload["choices"][0]["message"]["content"]))
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Invalid OpenAI-compatible response: {payload}") from exc


def prepare_messages(messages: list[dict[str, str]], disable_reasoning: bool = False) -> list[dict[str, str]]:
    if not disable_reasoning:
        return messages
    prepared = [dict(message) for message in messages]
    for message in reversed(prepared):
        if message.get("role") == "user":
            content = str(message.get("content", ""))
            if not content.startswith("/no_think"):
                message["content"] = "/no_think\n" + content
            break
    return prepared


def strip_think_blocks(content: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"^<think>.*\n", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def make_llm_client(config: dict, prefix: str = "llm") -> LLMClient:
    backend = str(config.get(f"{prefix}_backend", config.get("llm_backend", ""))).lower()
    if backend == "fake_llm":
        response = str(config.get(f"{prefix}_fake_response", config.get("llm_fake_response", "")))
        return FakeLLMClient([response])
    if backend in {"openai_compatible", "openai-compatible"}:
        return OpenAICompatibleClient(
            base_url=str(config.get(f"{prefix}_base_url", config.get("llm_base_url", ""))),
            model=str(config.get(f"{prefix}_model", config.get("llm_model", ""))),
            api_key_env=str(config.get(f"{prefix}_api_key_env", config.get("llm_api_key_env", "OPENAI_API_KEY"))),
            timeout=int(config.get(f"{prefix}_timeout", config.get("llm_timeout", 60))),
            temperature=float(config.get(f"{prefix}_temperature", config.get("llm_temperature", 0.0))),
            max_tokens=int(config.get(f"{prefix}_max_tokens", config.get("llm_max_tokens", 512))),
            disable_reasoning=bool(config.get(f"{prefix}_disable_reasoning", config.get("llm_disable_reasoning", False))),
        )
    raise ValueError(f"Unknown LLM backend for {prefix}: {backend}")
