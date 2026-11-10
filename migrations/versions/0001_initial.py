"""Initial draft project metadata schema.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("project_meta",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("schema_profile", sa.String(32), nullable=False))
    op.create_table("jobs",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("job_id", sa.String(256), primary_key=True),
        sa.Column("idempotency_key", sa.String(256), nullable=False),
        sa.Column("intent_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("intent_digest", sa.String(64), nullable=False),
        sa.Column("intent_profile", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("attempts_started", sa.Integer(), nullable=False),
        sa.Column("current_attempt_id", sa.String(256)),
        sa.Column("current_token", sa.String(256)),
        sa.Column("owner_id", sa.String(256)),
        sa.Column("owner_epoch", sa.Integer()),
        sa.Column("compute_allocated", sa.Boolean(), nullable=False),
        sa.Column("stop_confirmed", sa.Boolean(), nullable=False),
        sa.Column("token_revoked", sa.Boolean(), nullable=False),
        sa.Column("retry_pending", sa.Boolean(), nullable=False),
        sa.Column("backoff_required", sa.Boolean(), nullable=False),
        sa.Column("recovery_required", sa.Boolean(), nullable=False),
        sa.Column("progress_units", sa.Integer()),
        sa.Column("candidate_manifest_id", sa.String(256)),
        sa.ForeignKeyConstraint(["project_id"], ["project_meta.project_id"]),
        sa.UniqueConstraint("project_id", "idempotency_key", name="uq_job_request"),
        sa.CheckConstraint("attempts_started >= 0", name="ck_attempt_count"),
        sa.CheckConstraint("owner_epoch IS NULL OR owner_epoch > 0", name="ck_owner_epoch"),
        sa.CheckConstraint("compute_allocated != stop_confirmed", name="ck_compute_stop"),
        sa.CheckConstraint("state NOT IN ('running','cancel_requested') OR compute_allocated = 1", name="ck_active_state"),
        sa.CheckConstraint("state NOT IN ('queued','cancelled') OR compute_allocated = 0", name="ck_idle_state"),
        sa.CheckConstraint("recovery_required = 0 OR (compute_allocated = 1 AND token_revoked = 1)", name="ck_recovery_state"))
    op.create_index("uq_active_project", "jobs", ["project_id"], unique=True,
                    sqlite_where=sa.text("compute_allocated = 1"))
    op.create_table("attempts",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("job_id", sa.String(256), primary_key=True),
        sa.Column("attempt_id", sa.String(256), primary_key=True),
        sa.Column("generation_token", sa.String(256), nullable=False),
        sa.Column("owner_id", sa.String(256), nullable=False),
        sa.Column("owner_epoch", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("token_revoked", sa.Boolean(), nullable=False),
        sa.Column("stop_confirmed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "job_id"], ["jobs.project_id", "jobs.job_id"]),
        sa.UniqueConstraint("project_id", "generation_token", name="uq_attempt_token"),
        sa.CheckConstraint("owner_epoch > 0", name="ck_attempt_owner_epoch"))
    op.create_table("publications",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("publication_id", sa.String(256), primary_key=True),
        sa.Column("job_id", sa.String(256), nullable=False),
        sa.Column("attempt_id", sa.String(256), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "job_id", "attempt_id"],
                                ["attempts.project_id", "attempts.job_id", "attempts.attempt_id"]),
        sa.UniqueConstraint("project_id", "job_id", name="uq_publication_job"))
    op.create_table("artifacts",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("publication_id", sa.String(256), primary_key=True),
        sa.Column("asset_id", sa.String(256), primary_key=True),
        sa.Column("relative_path", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "publication_id"],
                                ["publications.project_id", "publications.publication_id"]),
        sa.CheckConstraint("size_bytes >= 0", name="ck_artifact_size"))
    op.create_table("dependency_pins",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("job_id", sa.String(256), primary_key=True),
        sa.Column("dependency_id", sa.String(256), primary_key=True),
        sa.ForeignKeyConstraint(["project_id", "job_id"], ["jobs.project_id", "jobs.job_id"]))
    op.create_table("dependency_leases",
        sa.Column("project_id", sa.String(256), primary_key=True),
        sa.Column("lease_id", sa.String(256), primary_key=True),
        sa.Column("dependency_id", sa.String(256), nullable=False),
        sa.Column("owner_id", sa.String(256), nullable=False),
        sa.Column("owner_epoch", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project_meta.project_id"]),
        sa.CheckConstraint("owner_epoch > 0", name="ck_lease_epoch"))
    op.create_index("ix_lease_dependency", "dependency_leases", ["project_id", "dependency_id"])


def downgrade():
    # Draft only; a released project is never downgraded automatically.
    raise RuntimeError("downgrade of project metadata is unsupported")
