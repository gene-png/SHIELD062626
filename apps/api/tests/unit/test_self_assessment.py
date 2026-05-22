"""Client self-assessment flow (Phase 1 backend).

Intake auto-provisions a workspace + draft assessment for each CSF/ZT request;
the client then reads, answers, and submits their own assessment. Score/gap
stay admin-only.
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


@pytest.fixture()
def app_client(tmp_path) -> Iterator[TestClient]:
    db_path = tmp_path / "shield-selfassess.db"
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

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


def _register(c: TestClient, email: str) -> dict:
    r = c.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple!",
            "display_name": email.split("@")[0],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _client_submit_intake(c: TestClient) -> tuple[str, dict]:
    """First user is admin; the second (client-role) runs intake. Returns the
    client bearer + the intake submit response."""
    _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer = client["tokens"]["access_token"]
    r = c.post(
        "/intake/submit",
        headers={"Authorization": f"Bearer {bearer}"},
        json={
            "client": {"legal_name": "Atlas Defense Solutions"},
            "service_requests": [
                {"service_type": "nist_csf", "csf_target_tier": 3, "csf_profile": "MOD"},
                {"service_type": "zero_trust_cisa", "zt_target_stage": 3},
            ],
        },
    )
    assert r.status_code == 200, r.text
    return bearer, r.json()


def _service_id(state: dict, service_type: str) -> str:
    sr = next(s for s in state["service_requests"] if s["service_type"] == service_type)
    assert sr["fulfilled_service_id"] is not None, "request was not auto-provisioned"
    return sr["fulfilled_service_id"]


@pytest.mark.unit
def test_intake_autoprovisions_csf_and_zt(app_client: TestClient) -> None:
    _bearer, state = _client_submit_intake(app_client)
    by_type = {s["service_type"]: s for s in state["service_requests"]}
    assert by_type["nist_csf"]["fulfilled_service_id"] is not None
    assert by_type["zero_trust_cisa"]["fulfilled_service_id"] is not None


@pytest.mark.unit
def test_client_fills_and_submits_csf(app_client: TestClient) -> None:
    bearer, state = _client_submit_intake(app_client)
    h = {"Authorization": f"Bearer {bearer}"}
    svc_id = _service_id(state, "nist_csf")

    cat = app_client.get("/csf/catalog", headers=h).json()
    r = app_client.get(f"/csf/services/{svc_id}/self-assessment", headers=h)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["status"] == "draft"
    assert len(a["answers"]) == cat["total_subcategories"]

    answer_id = a["answers"][0]["id"]
    r = app_client.patch(
        f"/csf/self-assessment/answers/{answer_id}", headers=h, json={"maturity_tier": 2}
    )
    assert r.status_code == 200, r.text
    assert r.json()["maturity_tier"] == 2

    r = app_client.post(
        f"/csf/services/{svc_id}/self-assessment/submit", headers=h, json={"target_tier": 4}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "submitted"
    assert body["client_target_tier"] == 4

    # Locked for the client once submitted.
    r = app_client.patch(
        f"/csf/self-assessment/answers/{answer_id}", headers=h, json={"maturity_tier": 3}
    )
    assert r.status_code == 409
    # Score stays admin-only (client never sees the analysis pre-release).
    assert app_client.get(f"/csf/services/{svc_id}/score", headers=h).status_code == 403


@pytest.mark.unit
def test_csf_catalog_tags_profiles_and_assessment_exposes_profile(
    app_client: TestClient,
) -> None:
    bearer, state = _client_submit_intake(app_client)
    h = {"Authorization": f"Bearer {bearer}"}
    svc_id = _service_id(state, "nist_csf")

    cat = app_client.get("/csf/catalog", headers=h).json()
    profiles = {
        s["min_profile"]
        for fn in cat["functions"]
        for c in fn["categories"]
        for s in c["subcategories"]
    }
    # The curated mapping uses all three levels so filtering is meaningful.
    assert profiles == {"LOW", "MOD", "HIGH"}

    # The assessment surfaces the client's intake profile (MOD here) so the UI
    # can filter the checklist to it.
    a = app_client.get(f"/csf/services/{svc_id}/self-assessment", headers=h).json()
    assert a["client_profile"] == "MOD"


@pytest.mark.unit
def test_client_fills_and_submits_zt(app_client: TestClient) -> None:
    bearer, state = _client_submit_intake(app_client)
    h = {"Authorization": f"Bearer {bearer}"}
    svc_id = _service_id(state, "zero_trust_cisa")

    cat = app_client.get("/zt/catalog?framework=cisa_ztmm_2_0", headers=h).json()
    r = app_client.get(f"/zt/services/{svc_id}/self-assessment", headers=h)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["status"] == "draft"
    assert len(a["answers"]) == cat["total_capabilities"]

    answer_id = a["answers"][0]["id"]
    r = app_client.patch(
        f"/zt/self-assessment/answers/{answer_id}", headers=h, json={"maturity_stage": 2}
    )
    assert r.status_code == 200, r.text

    r = app_client.post(
        f"/zt/services/{svc_id}/self-assessment/submit", headers=h, json={"target_stage": 4}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "submitted"
    assert body["client_target_stage"] == 4

    r = app_client.patch(
        f"/zt/self-assessment/answers/{answer_id}", headers=h, json={"maturity_stage": 3}
    )
    assert r.status_code == 409
