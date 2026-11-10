"""Initial local project metadata schema. ORM objects never cross IPC."""
from sqlalchemy import Boolean, CheckConstraint, ForeignKeyConstraint, Index, Integer, LargeBinary, String, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProjectMeta(Base):
    __tablename__ = "project_meta"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    schema_profile: Mapped[str] = mapped_column(String(32), nullable=False)


class Job(Base):
    __tablename__ = "jobs"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    intent_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    intent_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    intent_profile: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    attempts_started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_attempt_id: Mapped[str | None] = mapped_column(String(256))
    current_token: Mapped[str | None] = mapped_column(String(256))
    owner_id: Mapped[str | None] = mapped_column(String(256))
    owner_epoch: Mapped[int | None] = mapped_column(Integer)
    compute_allocated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retry_pending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backoff_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recovery_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    progress_units: Mapped[int | None] = mapped_column(Integer)
    candidate_manifest_id: Mapped[str | None] = mapped_column(String(256))
    __table_args__ = (
        UniqueConstraint("project_id", "idempotency_key", name="uq_job_request"),
        ForeignKeyConstraint(["project_id"], ["project_meta.project_id"]),
        CheckConstraint("attempts_started >= 0", name="ck_attempt_count"),
        CheckConstraint("owner_epoch IS NULL OR owner_epoch > 0", name="ck_owner_epoch"),
        CheckConstraint("compute_allocated != stop_confirmed", name="ck_compute_stop"),
        CheckConstraint("state NOT IN ('running','cancel_requested') OR compute_allocated = 1", name="ck_active_state"),
        CheckConstraint("state NOT IN ('queued','cancelled') OR compute_allocated = 0", name="ck_idle_state"),
        CheckConstraint("recovery_required = 0 OR (compute_allocated = 1 AND token_revoked = 1)", name="ck_recovery_state"),
        Index("uq_active_project", "project_id", unique=True,
              sqlite_where=text("compute_allocated = 1")),
    )


class Attempt(Base):
    __tablename__ = "attempts"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    generation_token: Mapped[str] = mapped_column(String(256), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(256), nullable=False)
    owner_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    token_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    __table_args__ = (
        ForeignKeyConstraint(["project_id", "job_id"], ["jobs.project_id", "jobs.job_id"]),
        UniqueConstraint("project_id", "generation_token", name="uq_attempt_token"),
        CheckConstraint("owner_epoch > 0", name="ck_attempt_owner_epoch"),
    )


class Publication(Base):
    __tablename__ = "publications"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    publication_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(256), nullable=False)
    attempt_id: Mapped[str] = mapped_column(String(256), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (
        ForeignKeyConstraint(["project_id", "job_id", "attempt_id"],
                             ["attempts.project_id", "attempts.job_id", "attempts.attempt_id"]),
        UniqueConstraint("project_id", "job_id", name="uq_publication_job"),
    )


class Artifact(Base):
    __tablename__ = "artifacts"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    publication_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (
        ForeignKeyConstraint(["project_id", "publication_id"],
                             ["publications.project_id", "publications.publication_id"]),
        CheckConstraint("size_bytes >= 0", name="ck_artifact_size"),
    )


class DependencyPin(Base):
    __tablename__ = "dependency_pins"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    dependency_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    __table_args__ = (ForeignKeyConstraint(["project_id", "job_id"],
                                         ["jobs.project_id", "jobs.job_id"]),)


class DependencyLease(Base):
    __tablename__ = "dependency_leases"
    project_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    lease_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    dependency_id: Mapped[str] = mapped_column(String(256), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(256), nullable=False)
    owner_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (
        ForeignKeyConstraint(["project_id"], ["project_meta.project_id"]),
        CheckConstraint("owner_epoch > 0", name="ck_lease_epoch"),
        Index("ix_lease_dependency", "project_id", "dependency_id"),
    )
