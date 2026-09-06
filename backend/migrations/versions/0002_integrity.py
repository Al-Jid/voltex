"""Repair target timestamps and permit reward reversals.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("reviews", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("""UPDATE reviews SET is_current = false WHERE id IN (
        SELECT id FROM (SELECT id, row_number() OVER (
            PARTITION BY target_type, target_id ORDER BY created_at DESC, id DESC
        ) AS position FROM reviews) ranked WHERE position > 1
    )""")
    op.add_column("stock_requests", sa.Column("source_branch_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_stock_requests_source_branch", "stock_requests", "branches", ["source_branch_id"], ["id"], ondelete="RESTRICT")
    op.execute("ALTER TABLE idempotency_keys DROP CONSTRAINT IF EXISTS idempotency_keys_pkey")
    op.execute("ALTER TABLE idempotency_keys DROP CONSTRAINT IF EXISTS pk_idempotency_keys")
    op.create_primary_key(op.f("pk_idempotency_keys"), "idempotency_keys", ["key", "user_id"])
    op.add_column("branch_targets", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("branch_targets", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    # Cover both explicit and convention-expanded names from initial installations.
    op.execute("ALTER TABLE point_ledger DROP CONSTRAINT IF EXISTS points_delta_positive")
    op.execute("ALTER TABLE point_ledger DROP CONSTRAINT IF EXISTS ck_point_ledger_points_delta_positive")
    op.create_check_constraint(op.f("ck_point_ledger_points_delta_nonzero"), "point_ledger", "points_delta <> 0")


def downgrade():
    # Refuse to discard reversal history through an incompatible downgrade.
    raise RuntimeError("0002 is forward-only; restore an independently verified backup if necessary")
