"""Rate-limiting tests (Sprint 3 T3).

Fixed-window per-IP + per-account limits on auth; per-client limits on the
expensive run-AI path. Redis-backed in prod; here we drive the limiter with a
fake in-memory backend and a broken backend so the whole surface is exercised
offline (tests run SQLite / no Redis):

  - a counter over its window -> typed 429 reason=rate_limited + Retry-After;
  - a Redis outage (backend raises) -> request ALLOWED (fail-open) + a loud
    structlog warning, so an infra blip never bricks auth;
  - the wiring on /auth/login enforces both the per-IP and per-account buckets
    with the D-016 typed envelope and the Retry-After header actually reaching
    the client.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alembic import command

# -----------------------------------------------------------------------------
# Fakes
# -----------------------------------------------------------------------------


class _FakeBackend:
    """In-memory fixed-window counter — stands in for Redis in tests."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.expires: dict[str, int] = {}

    def incr(self, key: str, window_seconds: int) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        self.expires[key] = window_seconds
        return self.counts[key]


class _BrokenBackend:
    """A backend whose every call fails the way a Redis outage would."""

    def incr(self, key: str, window_seconds: int) -> int:
        from app.security.rate_limit import RateLimitBackendError

        raise RateLimitBackendError("redis is down")


# -----------------------------------------------------------------------------
# Core limiter behaviour
# -----------------------------------------------------------------------------


@pytest.mark.unit
def test_check_allows_up_to_limit_then_raises_typed_429() -> None:
    from fastapi import HTTPException

    from app.security.rate_limit import RateLimit, RateLimiter

    limiter = RateLimiter(_FakeBackend())
    rate = RateLimit(limit=3, window_seconds=60)

    # First `limit` calls pass silently.
    for _ in range(3):
        limiter.check("k", rate)

    # The one over the line raises a typed 429 with a Retry-After hint.
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("k", rate)
    exc = exc_info.value
    assert exc.status_code == 429
    assert exc.detail["reason"] == "rate_limited"
    assert exc.headers["Retry-After"] == "60"


@pytest.mark.unit
def test_distinct_keys_have_independent_windows() -> None:
    from app.security.rate_limit import RateLimit, RateLimiter

    limiter = RateLimiter(_FakeBackend())
    rate = RateLimit(limit=1, window_seconds=60)

    limiter.check("a", rate)  # consumes a's budget
    limiter.check("b", rate)  # b is independent, still fine


@pytest.mark.unit
def test_fail_open_when_backend_unavailable(capsys) -> None:
    """A Redis outage must never block a request — allow it, loudly.

    structlog renders to stdout via PrintLoggerFactory, so we capture stdout
    (not stdlib caplog) to prove the warning is emitted.
    """
    from app.security.rate_limit import RateLimit, RateLimiter

    limiter = RateLimiter(_BrokenBackend())
    rate = RateLimit(limit=1, window_seconds=60)

    # Far more calls than the limit; none may raise because the backend is
    # down and we fail open.
    for _ in range(5):
        limiter.check("k", rate)

    assert "rate_limit.backend_unavailable" in capsys.readouterr().out


@pytest.mark.unit
def test_enforce_ai_blocks_per_client_after_limit() -> None:
    import uuid

    from fastapi import HTTPException

    from app.config import Settings
    from app.security.rate_limit import RateLimiter

    settings = Settings(shield_rate_limit_ai_max=2, shield_rate_limit_ai_window_seconds=60)
    limiter = RateLimiter(_FakeBackend(), settings)
    cid = uuid.uuid4()

    limiter.enforce_ai(cid)
    limiter.enforce_ai(cid)
    with pytest.raises(HTTPException) as exc_info:
        limiter.enforce_ai(cid)
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["reason"] == "rate_limited"


@pytest.mark.unit
def test_disabled_limiter_never_blocks() -> None:
    import uuid

    from app.config import Settings
    from app.security.rate_limit import RateLimiter

    settings = Settings(shield_rate_limit_enabled=False, shield_rate_limit_ai_max=1)
    limiter = RateLimiter(_FakeBackend(), settings)
    cid = uuid.uuid4()
    for _ in range(5):
        limiter.enforce_ai(cid)  # never raises when the feature is off


# -----------------------------------------------------------------------------
# Route wiring: /auth/login enforces both buckets, typed envelope, Retry-After
# -----------------------------------------------------------------------------


def _make_app_client(settings) -> Iterator[TestClient]:
    from app.db.session import get_db
    from app.main import create_app
    from app.security.rate_limit import RateLimiter, get_rate_limiter

    def override_get_db() -> Iterator[Session]:
        db = _make_app_client._TestSession()
        try:
            yield db
        finally:
            db.close()

    limiter = RateLimiter(_FakeBackend(), settings)

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sqlite_engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'shield-rl.db'}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url, future=True)
    _make_app_client._TestSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    return engine


@pytest.mark.unit
def test_login_per_ip_rate_limited(sqlite_engine) -> None:
    from app.config import Settings

    settings = Settings(
        shield_rate_limit_auth_ip_max=3,
        shield_rate_limit_auth_ip_window_seconds=60,
        shield_rate_limit_auth_account_max=100,
        shield_rate_limit_auth_account_window_seconds=60,
    )
    client = next(_make_app_client(settings))

    body = {"email": "nobody@example.com", "password": "whatever-wrong-pass!"}
    # First 3 attempts hit the auth logic (401 invalid credentials).
    for _ in range(3):
        r = client.post("/auth/login", json=body)
        assert r.status_code == 401, r.text
    # The 4th trips the per-IP limit before any auth work.
    r = client.post("/auth/login", json=body)
    assert r.status_code == 429, r.text
    assert r.json()["error"]["reason"] == "rate_limited"
    assert r.headers["retry-after"] == "60"


@pytest.mark.unit
def test_login_per_account_rate_limited(sqlite_engine) -> None:
    from app.config import Settings

    settings = Settings(
        shield_rate_limit_auth_ip_max=100,
        shield_rate_limit_auth_ip_window_seconds=60,
        shield_rate_limit_auth_account_max=2,
        shield_rate_limit_auth_account_window_seconds=60,
    )
    client = next(_make_app_client(settings))

    victim = {"email": "victim@example.com", "password": "wrong-pass-guess!"}
    for _ in range(2):
        r = client.post("/auth/login", json=victim)
        assert r.status_code == 401, r.text
    # Third attempt on the same account trips the per-account bucket.
    r = client.post("/auth/login", json=victim)
    assert r.status_code == 429, r.text

    # A different account is unaffected (per-account keying, not global).
    r = client.post("/auth/login", json={"email": "other@example.com", "password": "x!"})
    assert r.status_code == 401, r.text
