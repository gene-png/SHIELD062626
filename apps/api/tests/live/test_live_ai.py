"""Opt-in live-AI integration test (Sprint 6 T1 / D-026).

This makes a REAL provider call. It is marked ``@pytest.mark.live`` ONLY (never
``unit``), so the default ``pytest -m unit`` gate deselects it and CI — which
runs ``pytest -m unit tests/unit`` — never even collects it (this module lives
outside ``tests/unit``). It self-skips unless ``SHIELD_LLM_MODE=live`` and a
runnable provider key are present, so a keyless loop/CI stays green.

Run it deliberately, with a key, from the api container:
  docker compose exec -T \
    -e SHIELD_LLM_MODE=live -e ANTHROPIC_API_KEY=sk-ant-... \
    api pytest -m live tests/live -q

It asserts the same contract the manual 2026-07-12 smoke proved — real
non-empty response, an ``llm_calls`` row with provider/model/mode=live/
status=completed/tokens, populated ``redacted_counts`` when PII is present,
a null ``error_message``, and NO PII in the response — reusing the canonical
PII payload from ``scripts.smoke_live_ai`` so the automated and manual paths
cannot drift.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from scripts.smoke_live_ai import (
    EXPECTED_REDACTED_COUNTS,
    PII_STRINGS,
    build_csf_pii_inputs,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.ai.engine import run_job
from app.ai.llm import LLMClient
from app.config import get_settings
from app.models.llm_call import LLMCallMode, LLMCallStatus
from app.models.user import User, UserRole


def _live_ready() -> tuple[bool, str]:
    settings = get_settings()
    if settings.shield_llm_mode != "live":
        return False, "SHIELD_LLM_MODE is not 'live'"
    return settings.live_llm_readiness()


_READY, _WHY = _live_ready()

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not _READY, reason=f"live AI not configured: {_WHY}"),
]


@pytest.fixture()
def db_factory(tmp_path) -> Iterator[sessionmaker]:
    db_path = tmp_path / "shield-live.db"
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url, future=True)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _new_admin(db: Session) -> User:
    user = User(
        email="live-smoke@kentro.example",
        password_hash="x" * 64,
        role=UserRole.ADMIN,
        display_name="Live Smoke",
    )
    db.add(user)
    db.flush()
    return user


def test_live_csf_run_ai_contract(db_factory) -> None:
    """One real CSF run: redaction stripped PII, the audit row is complete,
    and no raw PII survived into the model's response."""
    inputs, client_org_name, name_hints = build_csf_pii_inputs()
    client = LLMClient.from_settings(get_settings())

    with db_factory() as db:
        admin = _new_admin(db)
        result = run_job(
            db,
            client,
            "csf_score",
            inputs=inputs,
            requested_by=admin.id,
            client_org_name=client_org_name,
            name_hints=name_hints,
        )
        db.commit()
        row = result.llm_call

        # A real, live, completed call — not a fixture, not an error.
        assert row.mode == LLMCallMode.LIVE
        assert row.status == LLMCallStatus.COMPLETED
        assert row.error_message is None
        assert row.provider and row.model
        assert row.input_tokens and row.input_tokens > 0
        assert row.output_tokens and row.output_tokens > 0
        assert row.duration_ms is not None and row.duration_ms >= 0

        # Redaction actually ran on the PII we planted.
        assert row.redacted_counts == EXPECTED_REDACTED_COUNTS

        # The response is real and non-empty, and carries none of the raw PII.
        rendered = str(result.data)
        assert rendered.strip()
        for pii in PII_STRINGS:
            assert pii not in rendered
