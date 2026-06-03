"""add role and refresh_token to users

Revision ID: a1b2c3d4e5f6
Revises: 3d69ec8f4e90
Create Date: 2026-06-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "3d69ec8f4e90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )
    op.add_column(
        "users",
        sa.Column("refresh_token", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "refresh_token")
    op.drop_column("users", "role")
