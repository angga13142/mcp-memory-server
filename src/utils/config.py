"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SQLiteSettings(BaseSettings):
    """SQLite database configuration."""

    database_url: str = "sqlite+aiosqlite:///./data/memory.db"
    echo: bool = False


class ChromaSettings(BaseSettings):
    """ChromaDB configuration."""

    persist_directory: str = "./data/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    collection_name: str = "memory_embeddings"


class StorageSettings(BaseSettings):
    """Storage layer configuration."""

    sqlite: SQLiteSettings = Field(default_factory=SQLiteSettings)
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)


class HTTPSettings(BaseSettings):
    """HTTP transport configuration."""

    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: list[str] = []

    def validate_cors(self) -> None:
        """Validate CORS configuration and warn if insecure."""
        if "*" in self.cors_origins:
            import warnings

            warnings.warn(
                "CORS wildcard (*) allows all origins - this is insecure for production. "
                "Configure specific origins via MEMORY_SERVER__TRANSPORT__HTTP__CORS_ORIGINS",
                SecurityWarning,
                stacklevel=2,
            )


class TransportSettings(BaseSettings):
    """Transport layer configuration."""

    default: str = "stdio"
    http: HTTPSettings = Field(default_factory=HTTPSettings)


class FeatureSettings(BaseSettings):
    """Feature flags."""

    semantic_search: bool = True
    auto_embedding: bool = True


class MemorySettings(BaseSettings):
    """Memory retention configuration."""

    retention_days: int = 90
    max_decisions: int = 1000
    max_tasks: int = 500


class ServerSettings(BaseSettings):
    """Server configuration."""

    name: str = "memory-server"
    version: str = "1.0.0"
    log_level: str = "INFO"


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="MEMORY_SERVER_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    transport: TransportSettings = Field(default_factory=TransportSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Settings":
        """Load settings from a YAML configuration file."""
        config_path = Path(config_path)
        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            config_data: dict[str, Any] = yaml.safe_load(f) or {}

        return cls(**config_data)


@lru_cache
def get_settings(config_path: str | None = None) -> Settings:
    """Get cached settings instance."""
    if config_path:
        return Settings.from_yaml(config_path)

    # Try default config locations
    for path in ["config/config.yaml", "config.yaml", "config.yml", "../config.yaml"]:
        if Path(path).exists():
            return Settings.from_yaml(path)

    return Settings()
