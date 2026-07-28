"""Tests for model-provider contracts and Ollama HTTP handling."""

import io
import json
from typing import Any, Self

import pytest
from app.models.provider import GenerationRequest
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider


class FakeResponse:
    """Minimal context-managed HTTP response."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.buffer = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, amount: int) -> bytes:
        """Read bounded response bytes."""
        return self.buffer.read(amount)


def request() -> GenerationRequest:
    """Return a bounded structured-generation request."""
    return GenerationRequest(
        model="coder:latest",
        system_prompt="Return JSON.",
        prompt="Draft a bounded change.",
        json_schema={"type": "object"},
    )


def test_mock_provider_is_deterministic() -> None:
    provider = MockProvider('{"ready":true}')

    assert provider.health_check().available
    assert provider.generate(request()).content == '{"ready":true}'


def test_unavailable_mock_provider_fails() -> None:
    provider = MockProvider("", available=False)

    assert not provider.health_check().available
    with pytest.raises(RuntimeError, match="unavailable"):
        provider.generate(request())


def test_ollama_health_and_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            {"models": [{"name": "coder:latest"}]},
            {"models": [{"name": "coder:latest"}]},
            {
                "response": '{"task_id":"PLAN-001","changes":[]}',
                "prompt_eval_count": 12,
                "eval_count": 7,
            },
        ]
    )

    def fake_urlopen(*_: object, **__: object) -> FakeResponse:
        return FakeResponse(next(responses))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = OllamaProvider("http://localhost:11434", 2, 10_000)

    assert provider.health_check().models == ["coder:latest"]
    result = provider.generate(request())
    assert result.provider == "ollama"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 7


def test_ollama_rejects_missing_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse({"models": []}),
    )
    provider = OllamaProvider("http://localhost:11434", 2, 10_000)

    with pytest.raises(ValueError, match="not installed"):
        provider.generate(request())


def test_ollama_rejects_remote_endpoint() -> None:
    with pytest.raises(ValueError, match="local host"):
        OllamaProvider("https://example.com", 2, 10_000)
