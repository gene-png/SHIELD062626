"""Settings safety checks."""

from __future__ import annotations

import pytest
from app.config import Settings


@pytest.mark.unit
def test_production_rejects_redaction_off() -> None:
    s = Settings(environment="production", shield_redaction_mode="off", jwt_signing_secret="x" * 64)
    with pytest.raises(RuntimeError, match="SHIELD_REDACTION_MODE"):
        s.assert_safe_for_runtime()


@pytest.mark.unit
def test_production_rejects_placeholder_jwt_secret() -> None:
    s = Settings(environment="production", shield_redaction_mode="strict")
    with pytest.raises(RuntimeError, match="JWT_SIGNING_SECRET"):
        s.assert_safe_for_runtime()


@pytest.mark.unit
def test_development_permits_loose_config() -> None:
    s = Settings(environment="development", shield_redaction_mode="off")
    s.assert_safe_for_runtime()
