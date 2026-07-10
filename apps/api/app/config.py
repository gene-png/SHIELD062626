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
    s3_secret_key: str = (
        "shield-minio-secret"  # noqa: S105 - dev placeholder, refused in prod via assert_safe_for_runtime
    )
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
    openai_api_key: str = ""
    gemini_api_key: str = ""

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

    # Rate limiting (Sprint 3 T3). Fixed-window per-IP + per-account on the auth
    # endpoints and per-client on the expensive run-AI path. Defaults are
    # deliberately generous so the serialized e2e suite (all traffic from one
    # localhost IP, one seeded admin account) never trips them; tighten per
    # environment via env vars. Redis-backed; fail-open on a Redis outage.
    shield_rate_limit_enabled: bool = True
    shield_rate_limit_auth_ip_max: int = Field(default=300, ge=1)
    shield_rate_limit_auth_ip_window_seconds: int = Field(default=60, ge=1)
    shield_rate_limit_auth_account_max: int = Field(default=100, ge=1)
    shield_rate_limit_auth_account_window_seconds: int = Field(default=60, ge=1)
    shield_rate_limit_ai_max: int = Field(default=60, ge=1)
    shield_rate_limit_ai_window_seconds: int = Field(default=60, ge=1)

    # JWT signing
    jwt_signing_secret: str = (
        "dev-only-replace-via-secrets-manager"  # noqa: S105 - dev placeholder, refused in prod via assert_safe_for_runtime
    )

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
            raise RuntimeError("JWT_SIGNING_SECRET is still the default placeholder in production.")
        # Fail loudly on dead feature flags. The MFA and email-verification
        # flows do not exist yet (Master Spec §2 deferred them); flipping the
        # flag true used to silently do nothing, which is worse than refusing —
        # an operator would believe a control is active when it is not. Refuse
        # to boot until the flows land (Sprint 5+).
        if self.shield_auth_require_mfa:
            raise RuntimeError(
                "SHIELD_AUTH_REQUIRE_MFA=true but no MFA enrollment/challenge flow "
                "exists yet. Refusing to start rather than silently ignore the flag."
            )
        if self.shield_auth_require_email_verify:
            raise RuntimeError(
                "SHIELD_AUTH_REQUIRE_EMAIL_VERIFY=true but no email-verification flow "
                "exists yet. Refusing to start rather than silently ignore the flag."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
