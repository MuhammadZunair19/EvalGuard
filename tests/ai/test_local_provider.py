import json

import httpx
import pytest

from backend.app.core.errors import AppError
from backend.app.providers.local import OllamaLLMProvider


@pytest.mark.ai
@pytest.mark.asyncio
async def test_ollama_provider_sends_bounded_deterministic_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"response": "Grounded answer [1]."})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OllamaLLMProvider(
            "http://ollama.test", "llama3.2:3b", client=client
        )
        answer = await provider.generate("Question", "System")

    assert answer == "Grounded answer [1]."
    assert captured["model"] == "llama3.2:3b"
    assert captured["options"] == {"temperature": 0, "num_predict": 128}


@pytest.mark.regression
@pytest.mark.asyncio
async def test_ollama_connection_error_becomes_service_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OllamaLLMProvider(
            "http://host.docker.internal:11434", "llama3.2:3b", client=client
        )
        with pytest.raises(AppError) as error:
            await provider.generate("Question", "System")

    assert error.value.code == "OLLAMA_UNAVAILABLE"
    assert error.value.status_code == 503
