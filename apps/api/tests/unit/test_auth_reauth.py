"""Auth compensating-controls tests (Sprint 3 T2; grace semantics D-034).

Covers the honest versions of the controls README/BUILD_REPORT claimed:
  (a) daily forced re-auth ceiling honored at /auth/refresh (typed 401
      reason=reauth_required past shield_forced_reauth_seconds);
  (b) refresh-token rotation — a token two or more rotations old is rejected;
  (b2) one-step ANCHORED reuse grace (D-034): replaying the immediately-prior
      refresh token within jwt_refresh_reuse_grace_seconds of its rotation
      mints a fresh pair instead of force-ending the session — this is what
      stops the ~15-minute sign-out storm caused by concurrent web-side
      refreshes and post-restart stale cookies. The window is anchored at
      rotation time (grace hits do not re-arm it), a two-generations-old
      replay is always rejected, grace=0 restores strict rotation, and the
      forced-reauth ceiling always wins;
  (b3) an EXPIRED refresh token returns the typed reason=refresh_expired so
      the web layer can route idle-timeout to a clean sign-in redirect
      instead of silently 401ing every proxy call;
  (c) dead feature flags fail loudly at startup rather than silently doing
      nothing (the MFA / email-verify flows don't exist yet).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def app_client(tmp_path) -> Iterator[TestClient]:
    db_path = tmp_path / "shield-reauth.db"
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url

    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    test_engine = create_engine(url, future=True)
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    from app.db.session import get_db
    from app.main import create_app

    def override_get_db() -> Iterator[Session]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str = "first@example.com") -> dict:
    r = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple!",
            "display_name": "Test User",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# -----------------------------------------------------------------------------
# (a) Forced re-auth ceiling
# -----------------------------------------------------------------------------


@pytest.mark.unit
def test_refresh_past_forced_reauth_returns_typed_401(app_client: TestClient) -> None:
    from app.config import get_settings
    from app.security.jwt import issue_token

    body = _register(app_client)
    user_id = body["user"]["id"]
    settings = get_settings()

    # Mint a refresh token whose original auth time is older than the forced
    # re-auth ceiling. The ceiling is checked before rotation, so the jti need
    # not match the stored one.
    stale_auth_time = datetime.now(UTC) - timedelta(
        seconds=settings.shield_forced_reauth_seconds + 3600
    )
    import uuid as _uuid

    stale_token, _ = issue_token(
        subject=_uuid.UUID(user_id),
        role="admin",
        typ="refresh",
        auth_time=stale_auth_time,
    )

    r = app_client.post("/auth/refresh", json={"refresh_token": stale_token})
    assert r.status_code == 401, r.text
    assert r.json()["error"]["reason"] == "reauth_required"


@pytest.mark.unit
def test_refresh_within_window_carries_auth_time_forward(app_client: TestClient) -> None:
    from app.security.jwt import verify_token

    body = _register(app_client)
    original = verify_token(body["tokens"]["refresh_token"], expected_type="refresh")

    r = app_client.post("/auth/refresh", json={"refresh_token": body["tokens"]["refresh_token"]})
    assert r.status_code == 200, r.text
    rotated = verify_token(r.json()["refresh_token"], expected_type="refresh")

    # The original auth-time claim rides forward unchanged so the forced-reauth
    # ceiling is anchored to the original login, not reset on every refresh.
    assert rotated.auth_time is not None
    assert original.auth_time is not None
    assert rotated.auth_time == original.auth_time


# -----------------------------------------------------------------------------
# (b) Refresh-token rotation
# -----------------------------------------------------------------------------


@pytest.mark.unit
def test_reused_refresh_token_two_generations_old_rejected(app_client: TestClient) -> None:
    # RE-CONTRACTED for D-034 (hotfix fix/auth-refresh-reuse-storm). The old
    # test pinned strict single-jti rotation: replaying the immediately-prior
    # token was a 401. That exact strictness was force-signing-out every active
    # user ~15 min in (concurrent web-side refreshes / post-restart stale
    # cookies replay the prior token benignly), so D-034 deliberately relaxes
    # it to a one-step ANCHORED grace — see the (b2) tests below. The theft
    # boundary this test pins now sits one generation deeper: a refresh token
    # TWO rotations old is always rejected, grace or no grace.
    body = _register(app_client)
    gen0 = body["tokens"]["refresh_token"]

    first = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert first.status_code == 200, first.text
    gen1 = first.json()["refresh_token"]

    second = app_client.post("/auth/refresh", json={"refresh_token": gen1})
    assert second.status_code == 200, second.text
    gen2 = second.json()["refresh_token"]

    reused = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert reused.status_code == 401, reused.text
    assert reused.json()["error"]["reason"] == "refresh_reused"

    # The freshly rotated token still works.
    ok = app_client.post("/auth/refresh", json={"refresh_token": gen2})
    assert ok.status_code == 200, ok.text


# -----------------------------------------------------------------------------
# (b2) One-step anchored reuse grace (D-034)
# -----------------------------------------------------------------------------


def _backdate_rotation(user_id: str, *, seconds: int) -> None:
    """Shift the user's refresh_rotated_at into the past by `seconds`.

    Direct DB poke so the anchored-window tests don't sleep. Uses its own
    engine over the fixture's DATABASE_URL (the app holds no state between
    requests, so a parallel session is safe here).
    """
    import uuid as _uuid

    import sqlalchemy as sa

    from app.models.user import User

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with Session(engine) as db:
        row = db.get(User, _uuid.UUID(user_id))
        assert row is not None
        assert row.refresh_rotated_at is not None, "rotation should have stamped the anchor"
        row.refresh_rotated_at = row.refresh_rotated_at - timedelta(seconds=seconds)
        db.execute(
            sa.update(User)
            .where(User.id == _uuid.UUID(user_id))
            .values(refresh_rotated_at=row.refresh_rotated_at)
        )
        db.commit()


@pytest.mark.unit
def test_refresh_reuse_within_grace_returns_new_valid_pair(app_client: TestClient) -> None:
    # The bug test: a benign replay of the immediately-prior refresh token
    # (concurrent web refresh, stale post-restart cookie) must mint a fresh
    # usable pair, not kill the session.
    body = _register(app_client)
    gen0 = body["tokens"]["refresh_token"]

    first = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert first.status_code == 200, first.text

    graced = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert graced.status_code == 200, graced.text
    grace_pair = graced.json()

    # The grace-minted pair is a real, continuing session: it refreshes again.
    ok = app_client.post("/auth/refresh", json={"refresh_token": grace_pair["refresh_token"]})
    assert ok.status_code == 200, ok.text


@pytest.mark.unit
def test_refresh_reuse_grace_is_anchored_not_sliding(app_client: TestClient) -> None:
    from app.config import get_settings

    body = _register(app_client)
    user_id = body["user"]["id"]
    gen0 = body["tokens"]["refresh_token"]

    first = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert first.status_code == 200, first.text

    # A grace hit inside the window succeeds but must NOT re-arm the window
    # (prev jti and the rotation anchor stay untouched).
    graced = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert graced.status_code == 200, graced.text

    # Push the anchor past the grace horizon: the same prior token now dies.
    grace = get_settings().jwt_refresh_reuse_grace_seconds
    _backdate_rotation(user_id, seconds=grace + 60)

    replay = app_client.post("/auth/refresh", json={"refresh_token": gen0})
    assert replay.status_code == 401, replay.text
    assert replay.json()["error"]["reason"] == "refresh_reused"


@pytest.mark.unit
def test_refresh_grace_zero_restores_strict_rotation(
    app_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import get_settings

    monkeypatch.setenv("JWT_REFRESH_REUSE_GRACE_SECONDS", "0")
    get_settings.cache_clear()
    try:
        body = _register(app_client)
        gen0 = body["tokens"]["refresh_token"]

        first = app_client.post("/auth/refresh", json={"refresh_token": gen0})
        assert first.status_code == 200, first.text

        reused = app_client.post("/auth/refresh", json={"refresh_token": gen0})
        assert reused.status_code == 401, reused.text
        assert reused.json()["error"]["reason"] == "refresh_reused"
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


@pytest.mark.unit
def test_grace_does_not_override_reauth_ceiling(app_client: TestClient) -> None:
    # Even a token that would qualify for the reuse grace is rejected when the
    # forced-reauth ceiling has passed — the ceiling is checked first and is
    # absolute.
    import uuid as _uuid

    import sqlalchemy as sa

    from app.config import get_settings
    from app.models.user import User
    from app.security.jwt import issue_token

    body = _register(app_client)
    user_id = body["user"]["id"]
    settings = get_settings()

    stale_auth_time = datetime.now(UTC) - timedelta(
        seconds=settings.shield_forced_reauth_seconds + 3600
    )
    stale_token, stale_payload = issue_token(
        subject=_uuid.UUID(user_id),
        role="admin",
        typ="refresh",
        auth_time=stale_auth_time,
    )

    # Make the stale token the graceable prev: fresh anchor, matching prev jti.
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with Session(engine) as db:
        db.execute(
            sa.update(User)
            .where(User.id == _uuid.UUID(user_id))
            .values(
                prev_refresh_jti=str(stale_payload.jti),
                refresh_rotated_at=datetime.now(UTC),
            )
        )
        db.commit()

    r = app_client.post("/auth/refresh", json={"refresh_token": stale_token})
    assert r.status_code == 401, r.text
    assert r.json()["error"]["reason"] == "reauth_required"


# -----------------------------------------------------------------------------
# (b3) Typed idle expiry
# -----------------------------------------------------------------------------


@pytest.mark.unit
def test_expired_refresh_returns_typed_refresh_expired(app_client: TestClient) -> None:
    # An idle session whose refresh token has lapsed must yield a typed reason
    # the web layer can map to a clean sign-in redirect — not the generic
    # string detail that leaves every proxy call silently 401ing.
    import uuid as _uuid

    from app.security.jwt import issue_token

    body = _register(app_client)
    expired_exp = int((datetime.now(UTC) - timedelta(seconds=60)).timestamp())
    expired_token, _ = issue_token(
        subject=_uuid.UUID(body["user"]["id"]),
        role="admin",
        typ="refresh",
        additional_claims={"exp": expired_exp},
    )

    r = app_client.post("/auth/refresh", json={"refresh_token": expired_token})
    assert r.status_code == 401, r.text
    assert r.json()["error"]["reason"] == "refresh_expired"


# -----------------------------------------------------------------------------
# (c) Dead feature flags fail loudly at startup
# -----------------------------------------------------------------------------


@pytest.mark.unit
def test_startup_no_longer_refuses_when_require_mfa_true() -> None:
    # Sprint 6 T4 / D-027: the TOTP enroll/verify/login-challenge flow now
    # exists, so SHIELD_AUTH_REQUIRE_MFA GATES enforcement in routes/auth.py
    # rather than refusing to boot. Booting with the flag on must NOT raise.
    from app.config import Settings

    settings = Settings(shield_auth_require_mfa=True)
    settings.assert_safe_for_runtime()  # does not raise


@pytest.mark.unit
def test_startup_no_longer_refuses_when_require_email_verify_true() -> None:
    # Sprint 6 T5 / D-028: the email-verification flow now exists, so
    # SHIELD_AUTH_REQUIRE_EMAIL_VERIFY GATES login enforcement in routes/auth.py
    # rather than refusing to boot. Booting with the flag on must NOT raise.
    from app.config import Settings

    settings = Settings(shield_auth_require_email_verify=True)
    settings.assert_safe_for_runtime()  # does not raise


@pytest.mark.unit
def test_startup_raises_when_email_delivery_enabled_without_host() -> None:
    # D-028: enabling delivery without an SMTP host would silently drop every
    # verification / reset email — refuse to boot rather than swallow it.
    from app.config import Settings

    settings = Settings(shield_email_delivery_enabled=True, smtp_host="")
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        settings.assert_safe_for_runtime()
