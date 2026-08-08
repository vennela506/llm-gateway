import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.schemas import ChatRequest, Message
from app.providers.openai import OpenAIProvider


@pytest.fixture
def chat_request():
    return ChatRequest(
        messages=[Message(role="user", content="Hello!")],
        model="gpt-3.5-turbo",
        max_tokens=50,
        temperature=0.5,
    )


async def test_openai_provider_generate(chat_request, mocker):
    # 1. Mock the OpenAI SDK Client
    mock_client_instance = AsyncMock()

    # Setup the fake response structure that OpenAI normally returns
    mock_choice = MagicMock()
    mock_choice.message.content = "Hi there!"
    mock_response = MagicMock()
    mock_response.id = "chatcmpl-123"
    mock_response.model = "gpt-3.5-turbo"
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15

    # Make the async create method return our fake response
    mock_client_instance.chat.completions.create.return_value = mock_response

    # Patch the AsyncOpenAI class in our openai.py file
    mocker.patch("app.providers.openai.AsyncOpenAI", return_value=mock_client_instance)

    # 2. Initialize our provider (it will use the mocked client)
    provider = OpenAIProvider()

    # 3. Call the generate method
    response = await provider.generate(chat_request)

    # 4. Assert our Adapter did its job translating!
    assert response.provider == "openai"
    assert response.content == "Hi there!"
    assert response.prompt_tokens == 10
    assert response.total_tokens == 15
