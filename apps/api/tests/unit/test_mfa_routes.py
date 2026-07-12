"""End-to-end MFA route tests (enroll -> verify -> login challenge -> complete).

Sprint 6 T4 / D-027. Runs against an ephemeral SQLite + FastAPI TestClient,
mirroring test_auth_routes.py. The TOTP code is derived from the real secret
the enroll endpoint hands back, so the flow exercises the actual crypto.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.security import totp


@pytest.fixture()
def app_client(tmp_path) -> Iterator[TestClient]:
    db_path = tmp_path / "shield-mfa.db"
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


_PASSWORD = "correct horse battery staple!"


def _register(client: TestClient, email: str = "first@example.com") -> dict:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": _PASSWORD, "display_name": "Test User"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _enroll_and_verify(client: TestClient, access: str) -> tuple[str, list[str]]:
    """Run the full enroll->verify handshake; return (secret, recovery_codes)."""
    enroll = client.post("/auth/mfa/enroll", headers={"Authorization": f"Bearer {access}"})
    assert enroll.status_code == 200, enroll.text
    secret = enroll.json()["secret"]
    assert enroll.json()["otpauth_uri"].startswith("otpauth://totp/")

    verify = client.post(
        "/auth/mfa/verify",
        headers={"Authorization": f"Bearer {access}"},
        json={"code": totp.totp_now(secret)},
    )
    assert verify.status_code == 200, verify.text
    codes = verify.json()["recovery_codes"]
    assert len(codes) == 10
    return secret, codes


@pytest.mark.unit
def test_login_without_mfa_returns_pair_no_challenge(app_client: TestClient) -> None:
    _register(app_client)
    r = app_client.post("/auth/login", json={"email": "first@example.com", "password": _PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["mfa_required"] is False
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["mfa_pending_token"] is None


@pytest.mark.unit
def test_enroll_requires_authentication(app_client: TestClient) -> None:
    r = app_client.post("/auth/mfa/enroll")
    assert r.status_code == 401


@pytest.mark.unit
def test_verify_rejects_wrong_code(app_client: TestClient) -> None:
    body = _register(app_client)
    access = body["tokens"]["access_token"]
    app_client.post("/auth/mfa/enroll", headers={"Authorization": f"Bearer {access}"})
    r = app_client.post(
        "/auth/mfa/verify",
        headers={"Authorization": f"Bearer {access}"},
        json={"code": "000000"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["reason"] == "mfa_invalid_code"


@pytest.mark.unit
def test_verify_before_enroll_is_rejected(app_client: TestClient) -> None:
    body = _register(app_client)
    access = body["tokens"]["access_token"]
    r = app_client.post(
        "/auth/mfa/verify",
        headers={"Authorization": f"Bearer {access}"},
        json={"code": "123456"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["reason"] == "mfa_not_started"


@pytest.mark.unit
def test_full_enroll_then_login_with_totp(app_client: TestClient) -> None:
    body = _register(app_client)
    access = body["tokens"]["access_token"]
    secret, _codes = _enroll_and_verify(app_client, access)

    # Now login: password alone yields a challenge, not the pair.
    login = app_client.post(
        "/auth/login", json={"email": "first@example.com", "password": _PASSWORD}
    )
    assert login.status_code == 200
    assert login.json()["mfa_required"] is True
    assert login.json()["access_token"] is None
    pending = login.json()["mfa_pending_token"]
    assert pending

    # The pending token is NOT a usable access token.
    assert (
        app_client.get("/auth/me", headers={"Authorization": f"Bearer {pending}"}).status_code
        == 401
    )

    # Complete the challenge with a valid TOTP.
    done = app_client.post(
        "/auth/mfa/verify-login",
        json={"mfa_pending_token": pending, "code": totp.totp_now(secret)},
    )
    assert done.status_code == 200, done.text
    assert done.json()["access_token"]
    assert done.json()["refresh_token"]


@pytest.mark.unit
def test_verify_login_rejects_wrong_code(app_client: TestClient) -> None:
    body = _register(app_client)
    access = body["tokens"]["access_token"]
    _enroll_and_verify(app_client, access)
    login = app_client.post(
        "/auth/login", json={"email": "first@example.com", "password": _PASSWORD}
    )
    pending = login.json()["mfa_pending_token"]
    r = app_client.post(
        "/auth/mfa/verify-login",
        json={"mfa_pending_token": pending, "code": "000000"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["reason"] == "mfa_invalid_code"


@pytest.mark.unit
def test_verify_login_rejects_access_token_as_pending(app_client: TestClient) -> None:
    body = _register(app_client)
    access = body["tokens"]["access_token"]
    secret, _codes = _enroll_and_verify(app_client, access)
    # An access token must not be accepted where an mfa_pending token is required.
    r = app_client.post(
        "/auth/mfa/verify-login",
        json={"mfa_pending_token": access, "code": totp.totp_now(secret)},
    )
    assert r.status_code == 401


@pytest.mark.unit
def test_recovery_code_login_is_single_use(app_client: TestClient) -> None:
    body = _register(app_client)
    access = body["tokens"]["access_token"]
    _secret, codes = _enroll_and_verify(app_client, access)
    recovery = codes[0]

    def _challenge() -> str:
        login = app_client.post(
            "/auth/login", json={"email": "first@example.com", "password": _PASSWORD}
        )
        return login.json()["mfa_pending_token"]

    # First use of the recovery code succeeds.
    first = app_client.post(
        "/auth/mfa/verify-login",
        json={"mfa_pending_token": _challenge(), "code": recovery},
    )
    assert first.status_code == 200, first.text

    # Second use of the SAME code is rejected (single-use).
    second = app_client.post(
        "/auth/mfa/verify-login",
        json={"mfa_pending_token": _challenge(), "code": recovery},
    )
    assert second.status_code == 401
