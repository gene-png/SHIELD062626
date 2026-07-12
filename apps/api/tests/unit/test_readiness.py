"""Full dependency-health readiness endpoint (Sprint 6 T3).

`/ready` reports a per-dependency matrix — db, redis, minio, keycloak
(dormant), and LLM readiness. A down *required* dependency flips
`ready=false` and names the offender; informational checks (keycloak,
llm-in-fixture) never gate readiness. `/health` stays cheap.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def ready_client(monkeypatch) -> Iterator[TestClient]:
    """App whose db probe hits a live in-memory SQLite (SELECT 1 works) and
    whose external-service probes are monkeypatchable per test."""
    import app.routes.health as health_mod
    from app.db.session import get_db
    from app.main import create_app

    engine = create_engine("sqlite://", future=True)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db() -> Iterator[Session]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # Default the network probes to healthy so a test that wants an all-green
    # matrix doesn't need a real Redis/MinIO. Individual tests override these.
    monkeypatch.setattr(
        health_mod,
        "_probe_redis",
        lambda settings: health_mod.DependencyStatus(status="ok", required=True, detail="PING ok"),
    )
    monkeypatch.setattr(
        health_mod,
        "_probe_minio",
        lambda settings: health_mod.DependencyStatus(
            status="ok", required=True, detail="bucket reachable"
        ),
    )

    with TestClient(app) as c:
        yield c


@pytest.mark.unit
def test_health_liveness_does_not_touch_dependencies(ready_client: TestClient) -> None:
    # Liveness must stay cheap: no checks matrix, always ok.
    body = ready_client.get("/health").json()
    assert body["status"] == "ok"
    assert "checks" not in body


@pytest.mark.unit
def test_ready_reports_full_dependency_matrix(ready_client: TestClient) -> None:
    resp = ready_client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["status"] == "ok"
    checks = body["checks"]
    for dep in ("db", "redis", "minio", "keycloak", "llm"):
        assert dep in checks, f"{dep} missing from readiness matrix"
        assert "status" in checks[dep]
        assert "required" in checks[dep]
    assert checks["db"]["status"] == "ok"


@pytest.mark.unit
def test_ready_marks_keycloak_dormant_and_not_required(ready_client: TestClient) -> None:
    checks = ready_client.get("/ready").json()["checks"]
    assert checks["keycloak"]["status"] == "dormant"
    assert checks["keycloak"]["required"] is False


@pytest.mark.unit
def test_ready_llm_fixture_mode_ok_and_informational(ready_client: TestClient) -> None:
    # Fixture mode is a valid running state, so LLM must not gate readiness.
    checks = ready_client.get("/ready").json()["checks"]
    assert checks["llm"]["required"] is False
    assert checks["llm"]["status"] == "ok"


@pytest.mark.unit
def test_ready_flips_false_and_names_offender_when_redis_down(
    ready_client: TestClient, monkeypatch
) -> None:
    import app.routes.health as health_mod

    monkeypatch.setattr(
        health_mod,
        "_probe_redis",
        lambda settings: health_mod.DependencyStatus(
            status="down", required=True, detail="ConnectionError: refused"
        ),
    )
    body = ready_client.get("/ready").json()
    assert body["ready"] is False
    assert body["status"] == "degraded"
    assert body["checks"]["redis"]["status"] == "down"
    # The offender is named in the response.
    assert "redis" in body["offenders"]
    assert "db" not in body["offenders"]


@pytest.mark.unit
def test_ready_flips_false_when_minio_down(ready_client: TestClient, monkeypatch) -> None:
    import app.routes.health as health_mod

    monkeypatch.setattr(
        health_mod,
        "_probe_minio",
        lambda settings: health_mod.DependencyStatus(
            status="down", required=True, detail="EndpointConnectionError"
        ),
    )
    body = ready_client.get("/ready").json()
    assert body["ready"] is False
    assert "minio" in body["offenders"]


@pytest.mark.unit
def test_ready_stays_true_when_only_informational_check_off(
    ready_client: TestClient, monkeypatch
) -> None:
    # An informational (not-required) check being non-ok must NOT flip readiness.
    import app.routes.health as health_mod

    monkeypatch.setattr(
        health_mod,
        "_probe_llm",
        lambda settings: health_mod.DependencyStatus(
            status="down", required=False, detail="live mode misconfigured"
        ),
    )
    body = ready_client.get("/ready").json()
    assert body["ready"] is True
    assert body["offenders"] == []


@pytest.mark.unit
def test_probe_redis_reports_down_on_unreachable_server() -> None:
    # Real probe against a dead address fails loudly-but-caught into a "down"
    # status (readiness must never raise 500 — it reports the offender).
    from app.config import Settings
    from app.routes.health import _probe_redis

    settings = Settings(redis_url="redis://127.0.0.1:1/0")
    result = _probe_redis(settings)
    assert result.status == "down"
    assert result.required is True
    assert result.detail
