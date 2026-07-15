from __future__ import annotations

import json
import http.client
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    finish_reason: str = ""
    response_format_requested: bool = False
    response_format_applied: bool = False


class LLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    def complete_with_metadata(self, messages: list[dict[str, str]]) -> LLMCompletion:
        return LLMCompletion(content=self.complete(messages))


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
    response_format: str = ""
    response_format_fallback: bool = True
    retry_attempts: int = 2
    retry_backoff_seconds: float = 0.5

    def complete(self, messages: list[dict[str, str]]) -> str:
        return self.complete_with_metadata(messages).content

    def complete_with_metadata(self, messages: list[dict[str, str]]) -> LLMCompletion:
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
        response_format_requested = bool(self.response_format)
        if response_format_requested:
            payload["response_format"] = {"type": self.response_format}
        response_format_applied = response_format_requested
        try:
            body = self._post_completion(url, api_key, payload)
        except urllib.error.HTTPError as exc:
            if not (
                response_format_requested
                and self.response_format_fallback
                and _response_format_is_unsupported(exc)
            ):
                raise
            payload.pop("response_format", None)
            response_format_applied = False
            body = self._post_completion(url, api_key, payload)
        return LLMCompletion(
            content=extract_message_content(body),
            finish_reason=extract_finish_reason(body),
            response_format_requested=response_format_requested,
            response_format_applied=response_format_applied,
        )

    def _post_completion(self, url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        attempts = max(0, int(self.retry_attempts)) + 1
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                if attempt >= attempts - 1 or not _is_transient_transport_error(exc):
                    raise
                delay = max(0.0, float(self.retry_backoff_seconds)) * (2**attempt)
                if delay:
                    time.sleep(delay)


def extract_message_content(payload: dict[str, Any]) -> str:
    try:
        return strip_think_blocks(str(payload["choices"][0]["message"]["content"]))
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Invalid OpenAI-compatible response: {payload}") from exc


def extract_finish_reason(payload: dict[str, Any]) -> str:
    try:
        return str(payload["choices"][0].get("finish_reason") or "")
    except (KeyError, IndexError, TypeError, AttributeError):
        return ""


def _response_format_is_unsupported(exc: urllib.error.HTTPError) -> bool:
    if exc.code not in {400, 422}:
        return False
    try:
        body = exc.read().decode("utf-8", errors="replace").lower()
    except Exception:
        return False
    format_named = "response_format" in body or "json_object" in body
    unsupported = any(term in body for term in ("not supported", "unsupported", "unknown", "invalid"))
    return format_named and unsupported


def _is_transient_transport_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, http.client.RemoteDisconnected, ConnectionError)):
        return True
    if isinstance(exc, urllib.error.URLError):
        return isinstance(exc.reason, (TimeoutError, ConnectionError, OSError))
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code == 429 or 500 <= exc.code < 600
    return False


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
            response_format=str(config.get(f"{prefix}_response_format", config.get("llm_response_format", ""))),
            response_format_fallback=bool(
                config.get(
                    f"{prefix}_response_format_fallback",
                    config.get("llm_response_format_fallback", True),
                )
            ),
            retry_attempts=int(config.get(f"{prefix}_retry_attempts", config.get("llm_retry_attempts", 2))),
            retry_backoff_seconds=float(
                config.get(f"{prefix}_retry_backoff_seconds", config.get("llm_retry_backoff_seconds", 0.5))
            ),
        )
    raise ValueError(f"Unknown LLM backend for {prefix}: {backend}")
