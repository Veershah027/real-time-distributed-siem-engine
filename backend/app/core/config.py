"""Application configuration.

All settings are environment-driven (12-factor).  Nothing sensitive is
hard-coded; local development defaults live in `.env.example`.
"""

from __future__ import annotations

import functools
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core ---
    env: Literal["development", "production", "test"] = Field("development", alias="SIEM_ENV")
    log_level: str = Field("INFO", alias="SIEM_LOG_LEVEL")
    log_json: bool = Field(True, alias="SIEM_LOG_JSON")
    service_name: str = "siem-engine"

    # --- API ---
    api_host: str = Field("0.0.0.0", alias="SIEM_API_HOST")  # noqa: S104 - containerised
    api_port: int = Field(8000, alias="SIEM_API_PORT")
    cors_origins: str = Field("http://localhost:5173", alias="SIEM_CORS_ORIGINS")
    rate_limit_per_minute: int = Field(240, alias="SIEM_RATE_LIMIT_PER_MINUTE")

    # --- PostgreSQL ---
    postgres_user: str = Field("siem", alias="POSTGRES_USER")
    postgres_password: str = Field("siem", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("siem", alias="POSTGRES_DB")
    postgres_host: str = Field("localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    database_url_override: str | None = Field(None, alias="SIEM_DATABASE_URL")

    # --- Redis ---
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")
    redis_url_override: str | None = Field(None, alias="SIEM_REDIS_URL")

    # --- Kafka / Redpanda ---
    kafka_bootstrap_servers: str = Field("localhost:19092", alias="SIEM_KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_events: str = Field("siem.events.raw", alias="SIEM_KAFKA_TOPIC_EVENTS")
    kafka_consumer_group: str = Field("siem-stream-processor", alias="SIEM_KAFKA_CONSUMER_GROUP")
    kafka_client_id: str = Field("siem", alias="SIEM_KAFKA_CLIENT_ID")

    # --- Detection thresholds ---
    rule_bruteforce_max_failures: int = Field(10, alias="SIEM_RULE_BRUTEFORCE_MAX_FAILURES")
    rule_bruteforce_window_seconds: int = Field(60, alias="SIEM_RULE_BRUTEFORCE_WINDOW_SECONDS")
    rule_portscan_unique_ports: int = Field(20, alias="SIEM_RULE_PORTSCAN_UNIQUE_PORTS")
    rule_portscan_window_seconds: int = Field(30, alias="SIEM_RULE_PORTSCAN_WINDOW_SECONDS")
    rule_spray_unique_users: int = Field(8, alias="SIEM_RULE_SPRAY_UNIQUE_USERS")
    rule_spray_window_seconds: int = Field(120, alias="SIEM_RULE_SPRAY_WINDOW_SECONDS")
    rule_exfil_bytes_threshold: int = Field(52_428_800, alias="SIEM_RULE_EXFIL_BYTES_THRESHOLD")
    rule_exfil_window_seconds: int = Field(60, alias="SIEM_RULE_EXFIL_WINDOW_SECONDS")

    # --- Anomaly detection ---
    anomaly_zscore_threshold: float = Field(3.5, alias="SIEM_ANOMALY_ZSCORE_THRESHOLD")
    anomaly_ewma_alpha: float = Field(0.3, alias="SIEM_ANOMALY_EWMA_ALPHA")
    anomaly_min_samples: int = Field(20, alias="SIEM_ANOMALY_MIN_SAMPLES")

    # --- Optional layers ---
    enable_ml: bool = Field(False, alias="SIEM_ENABLE_ML")
    enrichment_provider: Literal["synthetic", "none"] = Field(
        "synthetic", alias="SIEM_ENRICHMENT_PROVIDER"
    )
    enable_llm_assist: bool = Field(False, alias="SIEM_ENABLE_LLM_ASSIST")

    # --- Auth (dev seed only) ---
    auth_enabled: bool = Field(False, alias="SIEM_AUTH_ENABLED")
    jwt_secret: str = Field("dev_only_insecure_secret_change_me", alias="SIEM_JWT_SECRET")
    jwt_expire_minutes: int = Field(60, alias="SIEM_JWT_EXPIRE_MINUTES")
    seed_admin_username: str = Field("admin", alias="SIEM_SEED_ADMIN_USERNAME")
    seed_admin_password: str = Field("admin_dev_only_change_me", alias="SIEM_SEED_ADMIN_PASSWORD")

    # --- Simulator ---
    events_per_second: int = Field(50, alias="SIEM_EVENTS_PER_SECOND")
    simulator_scenario: str = Field("normal", alias="SIEM_SIMULATOR_SCENARIO")
    simulator_attack_ratio: float = Field(0.05, alias="SIEM_SIMULATOR_ATTACK_RATIO")
    simulator_autostart: bool = Field(False, alias="SIEM_SIMULATOR_AUTOSTART")

    # --- Pipeline tuning ---
    consumer_batch_max: int = Field(500, alias="SIEM_CONSUMER_BATCH_MAX")
    persist_batch_size: int = Field(200, alias="SIEM_PERSIST_BATCH_SIZE")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """psycopg2-style URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "+psycopg2")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        if self.redis_url_override:
            return self.redis_url_override
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.env == "production"


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
