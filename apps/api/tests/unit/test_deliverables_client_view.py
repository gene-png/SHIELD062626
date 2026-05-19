"""Phase 3 acceptance gate: end-to-end client released-deliverable view.

This walks the full happy path: admin opens service, AI-extracts a
capability list (FixtureProvider so it's deterministic), marks
dispositions, approves the list, finalizes the deliverable, then
releases it. From the engagement client's POV we verify:

  - the deliverable shows up under GET /deliverables
  - the client can download the PDF + XLSX bytes
  - the detail endpoint is reachable
  - re-finalize + re-release supersedes the prior version in the list
  - a client cannot see an UN-released deliverable
"""

from __future__ import annotations

import io
import json
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.ai.llm import FixtureProvider, LLMClient, LLMResponse
from app.storage.local import LocalFilesystemStorage
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def app_client(tmp_path) -> Iterator[tuple[TestClient, sessionmaker, FixtureProvider]]:
    db_path = tmp_path / "shield-deliv.db"
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
    llm = LLMClient(provider)

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
    app.dependency_overrides[_llm_dep] = lambda: llm

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


def _seed_and_release(
    c: TestClient, bearer: str, provider: FixtureProvider, *, title: str = "Atlas"
) -> tuple[str, str]:
    """Open service, extract, approve, finalize, release. Returns (service_id, deliverable_id)."""
    provider.register(
        "extract.capabilities",
        lambda _p: LLMResponse(
            json.dumps(
                {
                    "items": [
                        {"name": "Wiz", "category": "CNAPP", "annual_cost_usd": 350000},
                        {"name": "Lacework", "category": "CNAPP", "annual_cost_usd": 120000},
                        {"name": "Splunk", "category": "SIEM", "annual_cost_usd": 480000},
                    ]
                }
            )
        ),
    )
    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "tech_debt", "title": title},
    )
    svc_id = sr.json()["id"]

    art = c.post(
        "/artifacts",
        headers={"Authorization": f"Bearer {bearer}"},
        files={"file": ("inv.csv", io.BytesIO(b"A\n1\n"), "text/csv")},
    )
    artifact_id = art.json()["id"]
    extr = c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"artifact_id": artifact_id},
    )
    items = extr.json()["items"]
    for item, disp in zip(items, ["keep", "consolidate", "cut"], strict=True):
        c.patch(
            f"/tech-debt/capability-items/{item['id']}",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"disposition": disp},
        )
    latest = c.get(
        f"/tech-debt/services/{svc_id}/capability-lists/latest",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    list_id = latest.json()["id"]
    c.post(
        f"/tech-debt/capability-lists/{list_id}/approve",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    fin = c.post(
        f"/tech-debt/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    deliv_id = fin.json()["id"]
    rel = c.post(
        f"/tech-debt/deliverables/{deliv_id}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert rel.status_code == 200, rel.text
    return svc_id, deliv_id


@pytest.mark.unit
def test_phase3_acceptance_gate(app_client) -> None:
    """Full Phase 3 happy path through to client download."""
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    admin_bearer = admin["tokens"]["access_token"]
    client_bearer = client["tokens"]["access_token"]

    svc_id, deliv_id = _seed_and_release(c, admin_bearer, provider)

    # Client sees the released deliverable in their list.
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert listing.status_code == 200, listing.text
    body = listing.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["id"] == deliv_id
    assert item["service_id"] == svc_id
    assert item["version"] == 1
    assert item["released_to_client_at"] is not None
    assert item["pdf_artifact_id"] is not None
    assert item["xlsx_artifact_id"] is not None
    assert item["pdf_filename"].endswith(".pdf")
    assert item["xlsx_filename"].endswith(".xlsx")

    # Detail endpoint reachable by the client.
    detail = c.get(
        f"/deliverables/{deliv_id}",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["id"] == deliv_id

    # Client can download both files; bytes look like a PDF + XLSX.
    pdf_resp = c.get(
        f"/artifacts/{item['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert pdf_resp.status_code == 200, pdf_resp.text
    assert pdf_resp.content.startswith(b"%PDF-")
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert "attachment" in pdf_resp.headers["content-disposition"]

    xlsx_resp = c.get(
        f"/artifacts/{item['xlsx_artifact_id']}/download",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert xlsx_resp.status_code == 200, xlsx_resp.text
    # XLSX is a zip envelope.
    assert xlsx_resp.content[:2] == b"PK"


@pytest.mark.unit
def test_unreleased_deliverable_invisible_to_client(app_client) -> None:
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    admin_bearer = admin["tokens"]["access_token"]
    client_bearer = client["tokens"]["access_token"]

    provider.register(
        "extract.capabilities",
        lambda _p: LLMResponse(
            json.dumps(
                {
                    "items": [
                        {"name": "Wiz", "category": "CNAPP", "annual_cost_usd": 350000},
                    ]
                }
            )
        ),
    )
    sr = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {admin_bearer}"},
        json={"kind": "tech_debt", "title": "Atlas"},
    )
    svc_id = sr.json()["id"]
    art = c.post(
        "/artifacts",
        headers={"Authorization": f"Bearer {admin_bearer}"},
        files={"file": ("inv.csv", io.BytesIO(b"A\n1\n"), "text/csv")},
    )
    c.post(
        f"/tech-debt/services/{svc_id}/capability-lists/extract",
        headers={"Authorization": f"Bearer {admin_bearer}"},
        json={"artifact_id": art.json()["id"]},
    )
    latest = c.get(
        f"/tech-debt/services/{svc_id}/capability-lists/latest",
        headers={"Authorization": f"Bearer {admin_bearer}"},
    )
    c.post(
        f"/tech-debt/capability-lists/{latest.json()['id']}/approve",
        headers={"Authorization": f"Bearer {admin_bearer}"},
    )
    fin = c.post(
        f"/tech-debt/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {admin_bearer}"},
    )
    deliv_id = fin.json()["id"]

    # Not yet released - client's list is empty and detail 404s.
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert listing.json()["items"] == []
    detail = c.get(
        f"/deliverables/{deliv_id}",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert detail.status_code == 404

    # And the PDF download is forbidden until release.
    pdf_dl = c.get(
        f"/artifacts/{fin.json()['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    assert pdf_dl.status_code == 404


@pytest.mark.unit
def test_re_release_supersedes_prior_in_client_list(app_client) -> None:
    c, _, provider = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    admin_bearer = admin["tokens"]["access_token"]
    client_bearer = client["tokens"]["access_token"]

    svc_id, _v1_id = _seed_and_release(c, admin_bearer, provider)

    # Re-finalize on the same day -> v2 and release it too.
    fin2 = c.post(
        f"/tech-debt/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {admin_bearer}"},
    )
    v2_id = fin2.json()["id"]
    c.post(
        f"/tech-debt/deliverables/{v2_id}/release",
        headers={"Authorization": f"Bearer {admin_bearer}"},
    )

    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {client_bearer}"},
    )
    items = listing.json()["items"]
    # Superseded v1 is hidden; only v2 should be visible.
    assert len(items) == 1
    assert items[0]["id"] == v2_id
    assert items[0]["version"] == 2
