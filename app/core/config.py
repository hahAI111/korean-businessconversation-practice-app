"""
应用配置 —— 从 .env 加载，Pydantic Settings 验证
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Azure AI Foundry (Identity-based) ──
    AZURE_AI_ENDPOINT: str
    MODEL_DEPLOYMENT: str = "gpt-5-nano"

    # ── Foundry Agent Names (Portal 中创建的 Agent 名称) ──
    TEXT_AGENT_NAME: str = "korean-biz-coach"
    VOICE_AGENT_NAME: str = "sujin-voice"

    # ── Azure Speech (Identity-based, 用于 voice pipeline REST API) ──
    AZURE_SPEECH_REGION: str = "eastus2"
    AZURE_SPEECH_RESOURCE_ENDPOINT: str = "https://gpt522222.cognitiveservices.azure.com/"
    AZURE_SPEECH_RESOURCE_ID: str = ""

    # ── Azure Blob Storage (Speech MCP 音频文件) ──
    AZURE_STORAGE_ACCOUNT_URL: str = ""
    AZURE_STORAGE_CONTAINER: str = "speech-audio"

    # ── Cosmos DB (NoSQL API, Entra ID auth) ──
    COSMOS_ENDPOINT: str = ""
    COSMOS_DATABASE: str = "korean_biz"

    # ── PostgreSQL ──
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/korean_biz"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT Auth ──
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24h

    # ── Microsoft Entra ID (optional, enables "Sign in with Microsoft") ──
    ENTRA_TENANT_ID: str = ""
    ENTRA_CLIENT_ID: str = ""

    # ── App ──
    APP_NAME: str = "Korean Biz Coach"
    DEBUG: bool = False

    model_config = {"env_file": [".env", ".env.local"], "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
