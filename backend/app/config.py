"""Central configuration via pydantic-settings.

All secrets live in environment variables only (see ``.env.example``). The app
is designed for *graceful degradation*: heavy ML/inference dependencies and
external services are optional, and deterministic local fallbacks keep every
feature runnable with zero setup.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    app_name: str = "Sentinel AI"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_prefix: str = ""

    # --- Database ---
    # SQLite default => zero-setup local runs. docker-compose / Supabase set a
    # Postgres URL and pgvector is used automatically when the driver allows.
    database_url: str = Field(
        default="sqlite+aiosqlite:///./sentinel.db",
        description="Async SQLAlchemy URL. Postgres enables pgvector.",
    )

    # --- Auth ---
    jwt_secret: str = Field(default="dev-insecure-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # --- Secret encryption at rest ---
    # Used to Fernet-encrypt live-target endpoint headers (API keys) in the DB.
    # Blank => derived from jwt_secret (still encrypted). Set a dedicated key in prod.
    header_encryption_key: str = Field(default="")

    # --- Security middleware ---
    # Comma-separated allowed Host header values. "*" disables the check (default
    # for zero-config local dev). Set to your real hostnames in production.
    trusted_hosts: List[str] = Field(default=["*"])
    max_request_bytes: int = Field(default=1_000_000)  # 1 MB request body cap
    security_headers_enabled: bool = Field(default=True)

    # --- CORS ---
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- LLM providers ---
    # If groq_api_key is empty AND ollama is unreachable, the deterministic mock
    # engine is used so the platform always works.
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")
    ollama_base_url: str = Field(default="")  # e.g. http://localhost:11434
    ollama_model: str = Field(default="llama3.1:8b")
    llm_request_timeout: int = 45
    force_mock_llm: bool = Field(default=False)

    # --- ML / RAG ---
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_dim: int = 384
    reranker_model: str = Field(default="BAAI/bge-reranker-base")
    injection_model: str = Field(
        default="protectai/deberta-v3-base-prompt-injection-v2"
    )
    enable_heavy_ml: bool = Field(
        default=False,
        description="Load transformers/sentence-transformers if True. "
        "When False, deterministic fallbacks are used (fast boot).",
    )
    injection_threshold: float = Field(default=0.5)

    # --- Guardrail proxy ---
    proxy_block_threshold: float = Field(default=0.5)
    prompt_leak_similarity: float = Field(default=0.55)

    # --- Rate limiting ---
    rate_limit_per_minute: int = Field(default=120)
    # When set (e.g. redis://host:6379/0), rate limiting is distributed across
    # instances via Redis; otherwise a per-process in-memory window is used.
    redis_url: str = Field(default="")

    # --- Observability ---
    langfuse_public_key: str = Field(default="")
    langfuse_secret_key: str = Field(default="")
    langfuse_host: str = Field(default="https://cloud.langfuse.com")

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, v):
        # Managed hosts (Render/Supabase/Heroku) hand out bare postgres URLs.
        # Rewrite to the async driver our engine expects.
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = "postgresql+asyncpg://" + v[len("postgres://"):]
            elif v.startswith("postgresql://"):
                v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
