"""fleet RBAC invites audit webhooks deliveries usage

Revision ID: a1b2c3d4e5f6
Revises: cd039fc1fb0a
Create Date: 2026-05-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "cd039fc1fb0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=False, server_default="admin"),
    )
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.create_table(
        "fleet_invites",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("fleet_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invited_by_user_id", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"]),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fleet_invites_fleet_id"), "fleet_invites", ["fleet_id"], unique=False)
    op.create_index(op.f("ix_fleet_invites_email"), "fleet_invites", ["email"], unique=False)
    op.create_index(op.f("ix_fleet_invites_token_hash"), "fleet_invites", ["token_hash"], unique=True)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("fleet_id", sa.String(), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_fleet_id"), "audit_events", ["fleet_id"], unique=False)
    op.create_index(op.f("ix_audit_events_created_at"), "audit_events", ["created_at"], unique=False)

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("event", sa.String(length=64), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_webhook_deliveries_job_id"), "webhook_deliveries", ["job_id"], unique=False
    )
    op.create_index(
        op.f("ix_webhook_deliveries_created_at"), "webhook_deliveries", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_deliveries_created_at"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_job_id"), table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index(op.f("ix_audit_events_created_at"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_fleet_id"), table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index(op.f("ix_fleet_invites_token_hash"), table_name="fleet_invites")
    op.drop_index(op.f("ix_fleet_invites_email"), table_name="fleet_invites")
    op.drop_index(op.f("ix_fleet_invites_fleet_id"), table_name="fleet_invites")
    op.drop_table("fleet_invites")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "role")
