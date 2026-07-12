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

# Model ids that were once shipped as defaults but are not valid at any live
# provider. Booting live against one of these guarantees a 404 on the first
# real call (D-026), so the preflight refuses rather than fail on first use.
_KNOWN_PLACEHOLDER_MODELS = frozenset({"claude-opus-4-7"})


def _anthropic_sdk_importable() -> bool:
    """True if the ``anthropic`` SDK can be imported without importing it.

    Isolated as a module-level helper so the live-mode boot preflight can be
    unit-tested by monkeypatching it (the SDK is installed in the api image but
    absent from some tool environments)."""
    from importlib.util import find_spec

    return find_spec("anthropic") is not None


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
    shield_llm_model: str = "claude-sonnet-5"
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
    # Short-lived token issued after the password factor when MFA is enrolled;
    # exchanged for the full pair by POST /auth/mfa/verify-login (Sprint 6 T4).
    jwt_mfa_pending_ttl_seconds: int = Field(default=300, ge=60)
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

    def live_llm_readiness(self) -> tuple[bool, str]:
        """Whether a live provider call will actually succeed (D-026).

        Returns ``(ready, human_detail)`` and never raises — the single source
        of truth shared by the boot preflight (which wraps a false result in a
        loud ``RuntimeError``) and ``GET /admin/ai-status`` (which surfaces the
        detail to an operator). Mirrors the ``_build_provider`` branch logic in
        ``app/ai/llm.py``: anthropic needs its key AND an importable SDK;
        openai/gemini are httpx adapters that need only their key; every other
        provider value has no live adapter yet.
        """
        provider = self.shield_llm_provider
        if provider == "anthropic":
            if not self.anthropic_api_key:
                return False, "Live mode is on but ANTHROPIC_API_KEY is not set."
            if not _anthropic_sdk_importable():
                return (
                    False,
                    "Live mode is on but the 'anthropic' SDK is not importable — add it "
                    "to apps/api dependencies and rebuild the api image.",
                )
        elif provider == "openai":
            if not self.openai_api_key:
                return False, "Live mode is on but OPENAI_API_KEY is not set."
        elif provider == "gemini":
            if not self.gemini_api_key:
                return False, "Live mode is on but GEMINI_API_KEY is not set."
        else:
            return (
                False,
                f"Live mode is on but provider {provider!r} has no live adapter yet "
                "(use anthropic, openai, or gemini, or switch SHIELD_LLM_MODE to fixture).",
            )
        if self.shield_llm_model in _KNOWN_PLACEHOLDER_MODELS:
            return (
                False,
                f"Live mode is on but SHIELD_LLM_MODEL={self.shield_llm_model!r} is a "
                "known-invalid placeholder — set a current model id.",
            )
        if not self.shield_llm_model.strip():
            return False, "Live mode is on but SHIELD_LLM_MODEL is empty."
        return True, f"Live AI configured ({provider}/{self.shield_llm_model})."

    def assert_safe_for_runtime(self) -> None:
        """Reject obviously unsafe configurations at startup."""
        if self.is_production() and self.shield_redaction_mode == "off":
            raise RuntimeError(
                "SHIELD_REDACTION_MODE=off is forbidden when ENVIRONMENT=production "
                "(Master Spec §12)."
            )
        if self.is_production() and self.jwt_signing_secret.startswith("dev-only"):
            raise RuntimeError("JWT_SIGNING_SECRET is still the default placeholder in production.")
        # Fail loudly on dead feature flags. Email verification does not exist
        # yet (Master Spec §2 deferred it); flipping the flag true would silently
        # do nothing, which is worse than refusing — an operator would believe a
        # control is active when it is not. Refuse to boot until the flow lands
        # (T5). NOTE: shield_auth_require_mfa is NO LONGER a boot refusal as of
        # Sprint 6 T4 (D-027) — the TOTP enroll/verify/login-challenge flow now
        # exists, so the flag GATES enforcement (require enrollment at login) in
        # routes/auth.py rather than refusing to start.
        if self.shield_auth_require_email_verify:
            raise RuntimeError(
                "SHIELD_AUTH_REQUIRE_EMAIL_VERIFY=true but no email-verification flow "
                "exists yet. Refusing to start rather than silently ignore the flag."
            )
        # Live-AI boot preflight (D-026): refuse to start in live mode unless a
        # real provider call would actually succeed, rather than degrade to a
        # 500/404 on the first Run-AI. Fixture mode is unaffected.
        if self.shield_llm_mode == "live":
            ready, detail = self.live_llm_readiness()
            if not ready:
                raise RuntimeError(f"SHIELD_LLM_MODE=live is not runnable: {detail}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
