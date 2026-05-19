"""Tech Debt ingest tests: service creation + capability extraction.

The extraction call uses a FixtureProvider-backed LLMClient with canned
JSON responses, so the test is deterministic + offline.
"""

from __future__ import annotations

import io
import json
import os
import uuid as _uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.ai.llm import FixtureProvider, LLMClient, LLMResponse
from app.models.capability import CapabilityList
from app.models.llm_call import LLMCall
from app.storage.local import LocalFilesystemStorage
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def app_client(tmp_path) -> Iterator[tuple[TestClient, sessionmaker, FixtureProvider]]:
    db_path = tmp_path / "shield-td.db"
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    storage = LocalFilesystemStorage(tmp_path / "storage")
    provider = FixtureProvider()
    client = LLMClient(provider)

    from app.db.session import get_db
    from app.main import create_app
    from app.routes.artifacts import _storage_dep
    from app.routes.tech_debt import _llm_dep

    def override_get_db() -> Iterator[Session]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[_storage_dep] = lambda: storage
    app.dependency_overrides[_llm_dep] = lambda: client

    with TestClient(app) as c:
        yield c, TestSession, provider


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


def _upload_csv(c: TestClient, bearer: str, name: str, csv_bytes: bytes) -> str:
    r = c.post(
        "/artifacts",
        headers={"Authorization": f"Bearer {bearer}"},
        files={"file": (name, io.BytesIO(csv_bytes), "text/csv")},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.mark.unit
def test_admin_can_open_service(app_client) -> None:
    c, _, _ = app_client
    admin = _register(c, "admin@example.com")
    r = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {admin['tokens']['access_token']}"},
        json={"kind": "tech_debt", "title": "Atlas — Tech Debt"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kind"] == "tech_debt"
    assert body["status"] == "in_progress"
    assert body["title"] == "Atlas — Tech Debt"


@pytest.mark.unit
def test_client_role_cannot_open_service(app_client) -> None:
    c, _, _ = app_client
    _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    r = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {client['tokens']['access_token']}"},
        json={"kind": "tech_debt", "title": "x"},
    )
    assert r.status_code == 403


@pytest.mark.unit
def test_extract_runs_redacted_call_and_writes_capability_list(app_client) -> None:
    c, TestSession, provider = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]

    captured: dict = {}

    def fake(payload: dict) -> LLMResponse:
        captured["payload"] = payload
        return LLMResponse(
            content=json.dumps(
                {
                    "items": [
                        {
                            "name": "Wiz",
                            "vendor": "Wiz, Inc.",
                            "category": "CNAPP",
                            "function": "Cloud posture",
                            "annual_cost_usd": 350000,
                            "license_count": 200,
                            "notes": "Strong cloud-native coverage.",
                            "confidence_pct": 92,
                            "source_row_index": 0,
                        },
                        {
                            "name": "Splunk Enterprise",
                            "vendor": "Splunk",
                            "category": "SIEM",
                            "function": "Log analytics",
                            "annual_cost_usd": 480000,
                            "license_count": None,
                            "notes": None,
                            "confidence_pct": 88,
                            "source_row_index": 1,
                        },
                    ]
                }
            )
        )

    provider.register("extract.capabilities", fake)

    # Open the service.
    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "tech_debt", "title": "Atlas — Tech Debt"},
    )
    svc_id = sr.json()["id"]

    # Upload a small inventory CSV with PII so we can prove redaction.
    csv = (
        b"Tool,Vendor,Owner,Owner Email,Annual Cost\n"
        b"Wiz,Wiz Inc,Alice Pemberton,alice@atlas-defense.gov,$350000\n"
        b"Splunk Enterprise,Splunk,Bob,bob@atlas-defense.gov,$480000\n"
    )
    artifact_id = _upload_csv(c, bearer, "inventory.csv", csv)

    # Extract.
    r = c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["version"] == 1
    assert len(body["items"]) == 2
    names = sorted(i["name"] for i in body["items"])
    assert names == ["Splunk Enterprise", "Wiz"]
    item = next(i for i in body["items"] if i["name"] == "Wiz")
    assert item["annual_cost_usd"] == 350000.0
    assert item["confidence_pct"] == 92
    assert item["category"] == "CNAPP"

    # Provider received the REDACTED rows. The owner emails should be
    # placeholder strings; the raw emails must not appear anywhere.
    payload_json = json.dumps(captured["payload"])
    assert "alice@atlas-defense.gov" not in payload_json
    assert "bob@atlas-defense.gov" not in payload_json
    assert "[EMAIL]" in payload_json

    # An llm_calls row exists for this extraction.
    with TestSession() as db:
        call = db.execute(select(LLMCall)).scalar_one()
        assert call.purpose == "extract.capabilities"
        assert call.status == "completed"
        assert call.redacted_counts["email"] == 2
        cap_list = db.execute(select(CapabilityList)).scalar_one()
        assert cap_list.service_id == _uuid.UUID(svc_id)
        assert cap_list.version == 1


@pytest.mark.unit
def test_extract_rejects_unknown_service(app_client) -> None:
    c, _, _ = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    artifact_id = _upload_csv(c, bearer, "x.csv", b"A,B\n1,2\n")
    r = c.post(
        f"/tech-debt/services/{_uuid.uuid4()}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    assert r.status_code == 404


@pytest.mark.unit
def test_extract_rejects_unsupported_artifact_mime(app_client) -> None:
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    provider.register("extract.capabilities", lambda _p: LLMResponse('{"items": []}'))

    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"title": "x"},
    )
    svc_id = sr.json()["id"]

    # Upload a PDF (allowed for intake artifacts but not for tech-debt
    # ingest in v1).
    r = c.post(
        "/artifacts",
        headers={"Authorization": f"Bearer {bearer}"},
        files={"file": ("inv.pdf", io.BytesIO(b"%PDF-1.7 stub"), "application/pdf")},
    )
    artifact_id = r.json()["id"]
    r = c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    assert r.status_code == 415


@pytest.mark.unit
def test_extract_versions_subsequent_lists(app_client) -> None:
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    provider.register(
        "extract.capabilities",
        lambda _p: LLMResponse('{"items": [{"name": "Wiz"}]}'),
    )

    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"title": "x"},
    )
    svc_id = sr.json()["id"]
    artifact_id = _upload_csv(c, bearer, "x.csv", b"A\n1\n")

    r1 = c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    assert r1.json()["version"] == 1
    r2 = c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    assert r2.json()["version"] == 2


@pytest.mark.unit
def test_latest_capability_list_admin_only(app_client) -> None:
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    a_bearer = admin["tokens"]["access_token"]
    c_bearer = client["tokens"]["access_token"]
    provider.register(
        "extract.capabilities",
        lambda _p: LLMResponse('{"items": []}'),
    )

    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {a_bearer}"},
        json={"title": "x"},
    )
    svc_id = sr.json()["id"]
    artifact_id = _upload_csv(c, a_bearer, "x.csv", b"A\n1\n")
    c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {a_bearer}"},
        json={"artifact_id": artifact_id},
    )

    r = c.get(
        f"/tech-debt/services/{svc_id}/capability-lists/latest",
        headers={"Authorization": f"Bearer {a_bearer}"},
    )
    assert r.status_code == 200
    r = c.get(
        f"/tech-debt/services/{svc_id}/capability-lists/latest",
        headers={"Authorization": f"Bearer {c_bearer}"},
    )
    assert r.status_code == 403


@pytest.mark.unit
def test_extract_503_when_llm_returns_bad_json(app_client) -> None:
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    provider.register(
        "extract.capabilities",
        lambda _p: LLMResponse("totally not json"),
    )

    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"title": "x"},
    )
    svc_id = sr.json()["id"]
    artifact_id = _upload_csv(c, bearer, "x.csv", b"A\n1\n")
    r = c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    assert r.status_code == 502
