"""users: prev_refresh_jti + refresh_rotated_at for the reuse grace (hotfix, D-034)

Revision ID: 0033
Revises: 0032
Create Date: 2026-07-24 00:00:00

Stores the jti rotated out by the most recent normal rotation and when that
rotation happened, so /auth/refresh can accept a benign replay of exactly that
token within jwt_refresh_reuse_grace_seconds (concurrent web-side refreshes and
post-restart stale cookies) instead of force-signing-out the user. Additive +
nullable (C0 pattern): old rows carry no grace window and behave strictly.
SQLite-safe via batch_alter_table.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: str | Sequence[str] | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("prev_refresh_jti", sa.String(length=36), nullable=True))
        batch.add_column(sa.Column("refresh_rotated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("refresh_rotated_at")
        batch.drop_column("prev_refresh_jti")
