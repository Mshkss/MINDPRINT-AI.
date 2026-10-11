from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'postgresql+asyncpg://mindprint:mindprint@localhost:5432/mindprint'
    ai_provider: str = 'mock'
    demo_mode: bool = True
    seed_demo: bool = True
    demo_password: str = ''
    cookie_secure: bool = False
    allowed_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    gigachat_credentials: str = ''
    gigachat_scope: str = 'GIGACHAT_API_PERS'
    gigachat_model: str = 'GigaChat-2-Pro'
    gigachat_base_url: str = 'https://api.giga.chat/v1'
    gigachat_ca_bundle: str | None = None
    local_llm_url: str = 'http://host.docker.internal:8080/v1'
    local_llm_model: str = 'Qwen3-14B'
    ai_timeout: float = 35

@lru_cache
def settings():
    return Settings()
