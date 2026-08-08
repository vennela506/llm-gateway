import pytest
from unittest.mock import AsyncMock
from fakeredis.aioredis import FakeRedis

from app.core.router import FallbackRouter
from app.models.schemas import ChatRequest, Message, LLMResponse
from app.core import circuit_breaker


@pytest.fixture
async def router(mocker):
    # Set up our fake Redis for the circuit breaker
    fake_redis = FakeRedis(decode_responses=True)
    mocker.patch.object(circuit_breaker, "redis_client", fake_redis)

    # Initialize the router
    return FallbackRouter()


async def test_fallback_routing_on_failure(router, mocker):
    # 1. Create a dummy request
    request = ChatRequest(messages=[Message(role="user", content="Test")])

    # 2. Mock OpenAI to CRASH (Raise an Exception)
    mock_openai_generate = AsyncMock(side_effect=Exception("OpenAI is down!"))
    mocker.patch.object(router.providers["openai"], "generate", mock_openai_generate)

    # 3. Mock Anthropic to SUCCEED
    success_response = LLMResponse(
        id="ant-123",
        content="Anthropic answer",
        provider="anthropic",
        model="claude",
        total_tokens=10,
    )
    mock_anthropic_generate = AsyncMock(return_value=success_response)
    mocker.patch.object(
        router.providers["anthropic"], "generate", mock_anthropic_generate
    )

    # 4. Route the request!
    response = await router.route_request(request)

    # 5. Assertions to prove it worked:
    # Did it return the Anthropic response?
    assert response.provider == "anthropic"
    assert response.content == "Anthropic answer"

    # Did it actually try OpenAI first?
    mock_openai_generate.assert_called_once()

    # Did it record a failure for OpenAI in the circuit breaker?
    failures = await circuit_breaker.redis_client.get("cb:failures:openai")
    assert int(failures) == 1
