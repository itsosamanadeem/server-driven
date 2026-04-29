"""add field access rules

Revision ID: 8a1c2d9b43f0
Revises: 94bf8bc119fb
Create Date: 2026-04-29 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a1c2d9b43f0"
down_revision: Union[str, Sequence[str], None] = "94bf8bc119fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ir_field_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("field", sa.String(length=100), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=False),
        sa.Column("can_write", sa.Boolean(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["ir_groups.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["ir_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ir_field_access")
