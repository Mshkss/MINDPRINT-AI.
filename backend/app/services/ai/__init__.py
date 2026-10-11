from app.core.config import settings
from app.services.ai.base import ProviderError
from app.services.ai.mock import MockProvider
from app.services.ai.gigachat import GigaChatProvider
from app.services.ai.local import LocalLLMProvider


def provider():
    providers = {
        "mock": MockProvider,
        "gigachat": GigaChatProvider,
        "local": LocalLLMProvider,
    }
    if settings().ai_provider not in providers:
        raise ProviderError("Неизвестный AI_PROVIDER")
    return providers[settings().ai_provider]()
