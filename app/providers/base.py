from abc import ABC, abstractmethod
from app.models.schemas import ChatRequest, LLMResponse


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Every provider must implement the generate method.
    """

    # We define the provider name as a class attribute
    provider_name: str

    @abstractmethod
    async def generate(self, request: ChatRequest) -> LLMResponse:
        """
        Takes a standardized ChatRequest and returns a standardized LLMResponse.
        """
        pass
