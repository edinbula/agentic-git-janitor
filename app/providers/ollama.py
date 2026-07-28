"""Local Ollama structured-generation provider."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.models.provider import (
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
)


class OllamaProvider:
    """Call Ollama's local HTTP API without shell execution."""

    name = "ollama"

    def __init__(
        self,
        base_url: str,
        timeout_seconds: int,
        max_response_characters: int,
    ) -> None:
        parsed = urllib.parse.urlsplit(base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("Ollama URL must use HTTP on the local host.")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_response_characters = max_response_characters

    def health_check(self) -> ProviderStatus:
        """Check the API and list locally installed models."""
        try:
            payload = self._request("GET", "/api/tags")
            raw_models = payload.get("models", [])
            if not isinstance(raw_models, list):
                raise RuntimeError("Ollama returned an invalid model list.")
            models = [
                str(item.get("name", ""))
                for item in raw_models
                if isinstance(item, dict) and item.get("name")
            ]
            return ProviderStatus(
                provider=self.name,
                available=True,
                models=models,
                message="Local Ollama API is available.",
            )
        except RuntimeError as exc:
            return ProviderStatus(
                provider=self.name,
                available=False,
                message=str(exc),
            )

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a non-streaming response constrained by a JSON schema."""
        status = self.health_check()
        if not status.available:
            raise RuntimeError(status.message)
        if request.model not in status.models:
            raise ValueError(
                f"Ollama model '{request.model}' is not installed locally."
            )
        started = time.monotonic()
        payload = self._request(
            "POST",
            "/api/generate",
            {
                "model": request.model,
                "system": request.system_prompt,
                "prompt": request.prompt,
                "format": request.json_schema,
                "stream": False,
                "think": False,
                "options": {"temperature": 0},
            },
        )
        content = payload.get("response")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama returned an empty generation response.")
        if len(content) > self.max_response_characters:
            raise RuntimeError("Ollama response exceeded the configured size limit.")
        return GenerationResponse(
            provider=self.name,
            model=request.model,
            content=content,
            duration_seconds=time.monotonic() - started,
            prompt_tokens=self._optional_int(payload.get("prompt_eval_count")),
            completion_tokens=self._optional_int(payload.get("eval_count")),
        )

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                raw = response.read(self.max_response_characters + 1)
        except (OSError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        if len(raw) > self.max_response_characters:
            raise RuntimeError("Ollama API response exceeded the size limit.")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Ollama returned an unexpected response.")
        return payload

    @staticmethod
    def _optional_int(value: object) -> int | None:
        return value if isinstance(value, int) and value >= 0 else None
