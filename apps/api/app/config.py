"""Settings loaded from environment. Master Spec §4.4-§4.5; AI Prompt §6.14.

No setting may be hardcoded. Every external service and security knob is here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]
RedactionMode = Literal["strict", "standard", "off"]
LLMProvider = Literal["anthropic", "openai", "azure_openai", "bedrock", "gemini", "local"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Runtime
    environment: Environment = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+psycopg://shield:shield@db:5432/shield"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Object storage
    s3_endpoint_url: str = "http://minio:9000"
    s3_bucket: str = "shield-artifacts"
    s3_access_key: str = "shield-minio"
    s3_secret_key: str = "shield-minio-secret"
    s3_kms_key_id: str = "dev-stub-key"

    # OIDC (Keycloak)
    keycloak_issuer: str = "http://keycloak:8080/realms/shield"
    keycloak_audience: str = "shield-api"
    keycloak_client_id: str = "shield-web"

    # LLM (Master Spec §4.4 - never hardcoded)
    shield_llm_provider: LLMProvider = "anthropic"
    shield_llm_model: str = "claude-opus-4-7"
    shield_llm_mode: Literal["fixture", "live"] = "fixture"
    anthropic_api_key: str = ""

    # Feature flags (Master Spec §2 - deferred for v1)
    shield_auth_require_mfa: bool = False
    shield_auth_require_email_verify: bool = False
    shield_email_delivery_enabled: bool = False

    # Redaction (Master Spec §12)
    shield_redaction_mode: RedactionMode = "strict"

    # Session security (Master Spec §4.5)
    jwt_access_ttl_seconds: int = Field(default=900, ge=60)
    jwt_refresh_ttl_seconds: int = Field(default=1800, ge=300)
    shield_account_lockout_max_attempts: int = Field(default=10, ge=1)
    shield_account_lockout_window_seconds: int = Field(default=900, ge=60)
    shield_idle_timeout_seconds: int = Field(default=1800, ge=60)
    shield_forced_reauth_seconds: int = Field(default=86400, ge=300)

    # JWT signing
    jwt_signing_secret: str = "dev-only-replace-via-secrets-manager"

    # Mail (MailHog in dev)
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_from: str = "no-reply@shield.local"

    def is_production(self) -> bool:
        return self.environment == "production"

    def assert_safe_for_runtime(self) -> None:
        """Reject obviously unsafe configurations at startup."""
        if self.is_production() and self.shield_redaction_mode == "off":
            raise RuntimeError(
                "SHIELD_REDACTION_MODE=off is forbidden when ENVIRONMENT=production "
                "(Master Spec §12)."
            )
        if self.is_production() and self.jwt_signing_secret.startswith("dev-only"):
            raise RuntimeError(
                "JWT_SIGNING_SECRET is still the default placeholder in production."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
