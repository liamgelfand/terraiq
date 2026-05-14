"""pilot corridors batches telemetry billing lineage

Revision ID: f3a4b5c6d7e8
Revises: a1b2c3d4e5f6
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_corridors",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("fleet_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("destination", sa.Text(), nullable=False),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("load_kg", sa.Float(), nullable=True),
        sa.Column("time_budget_fraction", sa.Float(), nullable=False, server_default="1.05"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_corridors_fleet_id", "saved_corridors", ["fleet_id"])

    op.create_table(
        "job_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("fleet_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_batches_fleet_id", "job_batches", ["fleet_id"])

    op.add_column("jobs", sa.Column("corridor_id", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("batch_id", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("simulation_engine_version", sa.String(length=32), nullable=True))
    op.add_column("jobs", sa.Column("lineage", sa.JSON(), nullable=True))
    op.create_foreign_key("fk_jobs_saved_corridor", "jobs", "saved_corridors", ["corridor_id"], ["id"])
    op.create_foreign_key("fk_jobs_job_batch", "jobs", "job_batches", ["batch_id"], ["id"])
    op.create_index("ix_jobs_corridor_id", "jobs", ["corridor_id"])
    op.create_index("ix_jobs_batch_id", "jobs", ["batch_id"])

    op.create_table(
        "telemetry_uploads",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("fleet_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=True),
        sa.Column("corridor_id", sa.String(), nullable=True),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("points", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("adherence", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["corridor_id"], ["saved_corridors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telemetry_uploads_fleet_id", "telemetry_uploads", ["fleet_id"])
    op.create_index("ix_telemetry_uploads_job_id", "telemetry_uploads", ["job_id"])
    op.create_index("ix_telemetry_uploads_corridor_id", "telemetry_uploads", ["corridor_id"])

    op.add_column("fleets", sa.Column("stripe_customer_id", sa.String(length=128), nullable=True))
    op.add_column("fleets", sa.Column("stripe_subscription_id", sa.String(length=128), nullable=True))
    op.add_column(
        "fleets",
        sa.Column("billing_plan", sa.String(length=32), nullable=False, server_default="free"),
    )


def downgrade() -> None:
    op.drop_column("fleets", "billing_plan")
    op.drop_column("fleets", "stripe_subscription_id")
    op.drop_column("fleets", "stripe_customer_id")

    op.drop_index("ix_telemetry_uploads_corridor_id", table_name="telemetry_uploads")
    op.drop_index("ix_telemetry_uploads_job_id", table_name="telemetry_uploads")
    op.drop_index("ix_telemetry_uploads_fleet_id", table_name="telemetry_uploads")
    op.drop_table("telemetry_uploads")

    op.drop_index("ix_jobs_batch_id", table_name="jobs")
    op.drop_index("ix_jobs_corridor_id", table_name="jobs")
    op.drop_constraint("fk_jobs_job_batch", "jobs", type_="foreignkey")
    op.drop_constraint("fk_jobs_saved_corridor", "jobs", type_="foreignkey")
    op.drop_column("jobs", "lineage")
    op.drop_column("jobs", "simulation_engine_version")
    op.drop_column("jobs", "batch_id")
    op.drop_column("jobs", "corridor_id")

    op.drop_index("ix_job_batches_fleet_id", table_name="job_batches")
    op.drop_table("job_batches")

    op.drop_index("ix_saved_corridors_fleet_id", table_name="saved_corridors")
    op.drop_table("saved_corridors")
