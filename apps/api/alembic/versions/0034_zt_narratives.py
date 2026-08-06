"""zt_assessments: persisted Run-AI narratives (Sprint 10 S4)

Revision ID: 0034
Revises: 0033
Create Date: 2026-08-03 00:00:00

The zt_score Run-AI already drafts an executive summary, a roadmap summary and
per-pillar narratives, but the route threw all three away after echoing them in
the HTTP response, so the deliverable could never carry them. These three
columns give them a home.

All three are nullable and additive (the C0 pattern): every assessment written
before this migration parses unchanged with three NULLs, and the response
schema defaults `pillar_narratives` to None rather than an empty dict.
`pillar_narratives` is generic JSON with a native JSONB variant on Postgres,
matching `app/models/attack_assessment.py`. SQLite-safe via batch_alter_table
(tests run SQLite, prod runs Postgres).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0034"
down_revision: str | Sequence[str] | None = "0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JSON_MAP = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    with op.batch_alter_table("zt_assessments") as batch:
        batch.add_column(sa.Column("roadmap_summary", sa.Text(), nullable=True))
        batch.add_column(sa.Column("executive_summary", sa.Text(), nullable=True))
        batch.add_column(sa.Column("pillar_narratives", _JSON_MAP, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("zt_assessments") as batch:
        batch.drop_column("pillar_narratives")
        batch.drop_column("executive_summary")
        batch.drop_column("roadmap_summary")
