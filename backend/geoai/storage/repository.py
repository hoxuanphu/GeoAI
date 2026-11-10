"""Guarded SQLAlchemy project repository for draft local job metadata.

The native composition root owns the WriterGuard and confirms process-group stop.
No route, worker, or request body may supply a guard or call confirm_stopped.
"""
from __future__ import annotations

import os
import math
import re
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from alembic import command
from alembic.config import Config
from pydantic import TypeAdapter
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session

from geoai.contracts import AttemptKey, JobSpec
from geoai.contracts.common import Identifier, PositiveInt
from geoai.storage.db_models import Artifact, Attempt, DependencyLease, DependencyPin, Job, ProjectMeta, Publication
from geoai.storage.guards import OwnerStopEvidence, WriterGuard
from geoai.storage.intents import INTENT_DIGEST_PROFILE, canonical_intent


_identifier = TypeAdapter(Identifier)
_epoch = TypeAdapter(PositiveInt)
_ROOT = Path(__file__).resolve().parents[3]
_WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", *(f"COM{n}" for n in range(1, 10)),
                    *(f"LPT{n}" for n in range(1, 10))}


def _local_path(value: str | Path, *, existing: bool) -> Path:
    path = Path(value)
    if not path.is_absolute() or str(path).startswith(("\\\\", "//")):
        raise ValueError("absolute local path required")
    if not path.parent.is_dir():
        raise ValueError("parent directory does not exist")
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(ancestor)):
            raise ValueError("reparse paths are unsupported")
    if existing and not path.is_file():
        raise ValueError("project database missing")
    return path


def _engine(path: Path):
    engine = create_engine(f"sqlite:///{path.as_posix()}",
                           connect_args={"timeout": 5}, future=True)

    @event.listens_for(engine, "connect")
    def configure(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def _migration_config(connection, lease, project_id):
    config = Config(str(_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_ROOT / "migrations"))
    config.attributes["connection"] = connection
    config.attributes["guard_lease"] = lease
    config.attributes["project_id"] = project_id
    return config


def migrate_project(path: str | Path, project_id: str, guard: WriterGuard) -> None:
    """Upgrade under caller-held native writer authority, before opening work."""
    _identifier.validate_python(project_id)
    guard.assert_held(project_id)
    lease = guard.retain(project_id)
    engine = None
    try:
        database = _local_path(path, existing=False)
        lease.assert_held(project_id)
        if database.exists():
            # Preserve a consistent pre-upgrade image; WAL may hold latest pages.
            backup_path = database.with_name(database.name + ".pre-migration-" + secrets.token_hex(8))
            with sqlite3.connect(database) as source, sqlite3.connect(backup_path) as target:
                source.backup(target)
        engine = _engine(database)
        lease.assert_held(project_id)
        with engine.begin() as connection:
            command.upgrade(_migration_config(connection, lease, project_id), "head")
            row = connection.execute(select(ProjectMeta).where(ProjectMeta.project_id == project_id)).scalar_one_or_none()
            if row is None:
                any_project = connection.execute(select(ProjectMeta.project_id)).first()
                if any_project is not None:
                    raise ValueError("database belongs to another project")
                connection.execute(ProjectMeta.__table__.insert().values(project_id=project_id, schema_profile="0.1.0"))
    finally:
        if engine is not None:
            engine.dispose()
        lease.close()


def _validate_metadata(session: Session, project_id: str) -> None:
    """Reject structurally valid rows that cannot be reconciled as a job graph."""
    jobs = session.scalars(select(Job).where(Job.project_id == project_id)).all()
    attempts = session.scalars(select(Attempt).where(Attempt.project_id == project_id)).all()
    publications = session.scalars(select(Publication).where(Publication.project_id == project_id)).all()
    attempt_map = {(a.job_id, a.attempt_id): a for a in attempts}
    publication_map = {p.job_id: p for p in publications}
    counts = {job.job_id: 0 for job in jobs}
    for attempt in attempts:
        if attempt.job_id not in counts:
            raise ValueError("orphan attempt metadata")
        counts[attempt.job_id] += 1
    for job in jobs:
        try:
            spec = JobSpec.model_validate_json(bytes(job.intent_bytes))
            raw, digest = canonical_intent(spec)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid immutable job intent") from exc
        if (spec.project_id != project_id or spec.job_id != job.job_id
                or spec.idempotency_key != job.idempotency_key
                or raw != bytes(job.intent_bytes) or digest != job.intent_digest
                or job.intent_profile != INTENT_DIGEST_PROFILE):
            raise ValueError("job intent metadata mismatch")
        if (job.state not in {"queued", "running", "cancel_requested", "failed", "succeeded", "cancelled"}
                or job.compute_allocated == job.stop_confirmed
                or job.attempts_started != counts[job.job_id]
                or (job.recovery_required and (not job.compute_allocated or not job.token_revoked))
                or (job.retry_pending and (job.state != "failed" or not job.compute_allocated))
                or (job.backoff_required and job.state != "queued")):
            raise ValueError("job state metadata mismatch")
        current_fields = (job.current_attempt_id, job.current_token, job.owner_id, job.owner_epoch)
        if job.attempts_started == 0:
            if (any(value is not None for value in current_fields)
                    or job.state not in {"queued", "cancelled"} or job.compute_allocated
                    or job.job_id in publication_map):
                raise ValueError("unstarted job metadata mismatch")
            continue
        if any(value is None for value in current_fields):
            raise ValueError("current attempt metadata incomplete")
        current = attempt_map.get((job.job_id, job.current_attempt_id))
        if (current is None or current.generation_token != job.current_token
                or current.owner_id != job.owner_id or current.owner_epoch != job.owner_epoch
                or current.stop_confirmed != job.stop_confirmed
                or current.token_revoked != job.token_revoked):
            raise ValueError("current attempt metadata mismatch")
        allowed_attempt_states = {
            "queued": {"failed"}, "running": {"running"},
            "cancel_requested": {"cancel_requested"}, "failed": {"failed"},
            "succeeded": {"succeeded"}, "cancelled": {"cancelled", "failed"},
        }
        if (current.state not in allowed_attempt_states[job.state]
                or (job.state in {"queued", "cancelled"} and job.compute_allocated)
                or (job.state in {"running", "cancel_requested"} and not job.compute_allocated)
                or (job.state == "running" and job.token_revoked and not job.recovery_required)
                or (job.state in {"failed", "cancel_requested"} and not job.token_revoked)
                or (job.state == "succeeded") != (job.job_id in publication_map)):
            raise ValueError("attempt/publication state mismatch")
        publication = publication_map.get(job.job_id)
        if publication is not None and publication.attempt_id != job.current_attempt_id:
            raise ValueError("publication attempt mismatch")


@dataclass(frozen=True)
class RepositoryJobView:
    project_id: str
    job_id: str
    state: str
    intent_bytes: bytes
    intent_digest: str
    attempts_started: int
    attempt: AttemptKey | None
    compute_allocated: bool
    stop_confirmed: bool
    token_revoked: bool
    recovery_required: bool
    publication_id: str | None
    publication_available: bool | None
    progress_units: int | None
    candidate_manifest_id: str | None
    retained_dependencies: frozenset[str]

    @property
    def job_spec(self) -> JobSpec:
        return JobSpec.model_validate_json(self.intent_bytes)


@dataclass(frozen=True)
class ArtifactInventoryRecord:
    publication_id: str
    asset_id: str
    relative_path: str
    sha256: str
    size_bytes: int
    available: bool


@dataclass(frozen=True)
class PublicationRecord:
    project_id: str
    job_id: str
    publication_id: str
    attempt_id: str
    available: bool
    artifacts: tuple[ArtifactInventoryRecord, ...]


class ProjectRepository:
    def __init__(self, path: Path, project_id: str, guard: WriterGuard, retry_policy):
        self.path, self.project_id, self.guard = path, project_id, guard
        if type(retry_policy.max_attempts) is not int or not 1 <= retry_policy.max_attempts <= 100:
            raise ValueError("bounded retry policy required")
        if type(retry_policy.backoff_seconds) not in (float, int) or not math.isfinite(retry_policy.backoff_seconds) or not 0 <= retry_policy.backoff_seconds <= 86400:
            raise ValueError("bounded backoff required")
        self.retry_policy = retry_policy
        guard.assert_held(project_id)
        self.lease = guard.retain(project_id)
        self._transactions = 0
        self._lifecycle_lock = threading.RLock()
        self._closed = False
        self.engine = None
        try:
            self.engine = _engine(path)
            with self._transaction() as session:
                meta = session.get(ProjectMeta, project_id)
                if meta is None or meta.schema_profile != "0.1.0" or session.scalars(select(ProjectMeta.project_id)).all() != [project_id]:
                    raise ValueError("project metadata mismatch")
                version = session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                if version != "0001_initial":
                    raise ValueError("unsupported schema version")
                _validate_metadata(session, project_id)
                for job in session.scalars(select(Job).where(Job.project_id == project_id, Job.compute_allocated.is_(True))):
                    if job.owner_id == guard.owner_id and job.owner_epoch == guard.owner_epoch:
                        continue
                    job.recovery_required = True
                    job.token_revoked = True
                    attempt = session.get(Attempt, (project_id, job.job_id, job.current_attempt_id))
                    if attempt is not None:
                        attempt.token_revoked = True
        except Exception:
            if self.engine is not None:
                self.engine.dispose()
            self.lease.close()
            self._closed = True
            raise

    @classmethod
    def open(cls, path: str | Path, project_id: str, guard: WriterGuard, retry_policy):
        _identifier.validate_python(project_id)
        return cls(_local_path(path, existing=True), project_id, guard, retry_policy)

    @contextmanager
    def _operation(self):
        # Register before attempting a connection. close cannot release native
        # writer authority during acquisition, transaction or online backup.
        with self._lifecycle_lock:
            if self._closed:
                raise RuntimeError("repository closed")
            self.lease.assert_held(self.project_id)
            self._transactions += 1
        try:
            yield
        finally:
            with self._lifecycle_lock:
                self._transactions -= 1

    @contextmanager
    def _transaction(self):
        with self._operation():
            connection = self.engine.connect()
            try:
                connection.exec_driver_sql("BEGIN IMMEDIATE")
                session = Session(bind=connection)
                try:
                    yield session
                    session.flush()
                    self.lease.assert_held(self.project_id)
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
                finally:
                    session.close()
            finally:
                connection.close()

    def close(self):
        with self._lifecycle_lock:
            if self._closed:
                return
            if self._transactions:
                raise RuntimeError("active repository operation")
            self.engine.dispose()
            self.lease.close()
            self._closed = True

    def _job(self, session, job_id: str) -> Job:
        _identifier.validate_python(job_id)
        job = session.get(Job, (self.project_id, job_id))
        if job is None:
            raise ValueError("unknown project job")
        return job

    def _view(self, session, job: Job) -> RepositoryJobView:
        publication = session.scalar(select(Publication).where(Publication.project_id == self.project_id,
                                                               Publication.job_id == job.job_id))
        pins = session.scalars(select(DependencyPin.dependency_id).where(
            DependencyPin.project_id == self.project_id, DependencyPin.job_id == job.job_id)).all()
        attempt = (AttemptKey(job_id=job.job_id, attempt_id=job.current_attempt_id,
                              generation_token=job.current_token) if job.current_attempt_id else None)
        return RepositoryJobView(self.project_id, job.job_id, job.state, bytes(job.intent_bytes),
                                 job.intent_digest, job.attempts_started, attempt,
                                 job.compute_allocated, job.stop_confirmed, job.token_revoked,
                                 job.recovery_required, publication.publication_id if publication else None,
                                 publication.available if publication else None, job.progress_units,
                                 job.candidate_manifest_id, frozenset(pins))

    def get(self, job_id: str) -> RepositoryJobView:
        with self._transaction() as session:
            return self._view(session, self._job(session, job_id))

    def enqueue(self, spec: JobSpec) -> RepositoryJobView:
        raw, digest = canonical_intent(spec)
        intent = JobSpec.model_validate_json(raw)
        if intent.project_id != self.project_id:
            raise ValueError("wrong project")
        with self._transaction() as session:
            existing = session.scalar(select(Job).where(Job.project_id == self.project_id,
                                                       Job.idempotency_key == intent.idempotency_key))
            if existing:
                if existing.intent_digest != digest or bytes(existing.intent_bytes) != raw or existing.intent_profile != INTENT_DIGEST_PROFILE:
                    raise ValueError("idempotency key conflicts with immutable intent")
                return self._view(session, existing)
            if session.get(Job, (self.project_id, intent.job_id)):
                raise ValueError("job ID already exists")
            job = Job(project_id=self.project_id, job_id=intent.job_id, idempotency_key=intent.idempotency_key,
                      intent_bytes=raw, intent_digest=digest, intent_profile=INTENT_DIGEST_PROFILE,
                      state="queued", attempts_started=0, compute_allocated=False,
                      stop_confirmed=True, token_revoked=False, retry_pending=False,
                      backoff_required=False, recovery_required=False)
            session.add(job)
            session.flush()
            return self._view(session, job)

    def claim(self, job_id: str, *, elapsed_backoff_seconds: float = 0) -> AttemptKey:
        if (type(elapsed_backoff_seconds) not in (int, float)
                or not math.isfinite(elapsed_backoff_seconds) or elapsed_backoff_seconds < 0):
            raise ValueError("invalid elapsed backoff")
        _identifier.validate_python(self.guard.owner_id)
        _epoch.validate_python(self.guard.owner_epoch)
        with self._transaction() as session:
            job = self._job(session, job_id)
            if job.state != "queued" or not job.stop_confirmed or job.recovery_required or job.attempts_started >= self.retry_policy.max_attempts:
                raise ValueError("job cannot be claimed")
            if elapsed_backoff_seconds < (self.retry_policy.backoff_seconds if job.backoff_required else 0):
                raise ValueError("retry backoff not elapsed")
            if session.scalar(select(Job.job_id).where(Job.project_id == self.project_id, Job.compute_allocated.is_(True))):
                raise ValueError("project compute already allocated")
            key = AttemptKey(job_id=job_id, attempt_id="attempt:" + secrets.token_hex(16),
                             generation_token="generation:" + secrets.token_hex(32))
            job.current_attempt_id, job.current_token = key.attempt_id, key.generation_token
            job.owner_id, job.owner_epoch = self.guard.owner_id, self.guard.owner_epoch
            job.attempts_started += 1
            job.compute_allocated, job.stop_confirmed = True, False
            job.token_revoked = job.retry_pending = job.backoff_required = False
            job.candidate_manifest_id = job.progress_units = None
            job.state = "running"
            session.add(Attempt(project_id=self.project_id, job_id=job_id, attempt_id=key.attempt_id,
                                generation_token=key.generation_token, owner_id=job.owner_id,
                                owner_epoch=job.owner_epoch, state="running", token_revoked=False,
                                stop_confirmed=False))
            return key

    def _current(self, session, job: Job, key: AttemptKey) -> Attempt | None:
        if not isinstance(key, AttemptKey) or key.job_id != job.job_id:
            return None
        if (job.current_attempt_id != key.attempt_id or job.current_token != key.generation_token
                or job.owner_id != self.guard.owner_id or job.owner_epoch != self.guard.owner_epoch
                or job.recovery_required):
            return None
        return session.get(Attempt, (self.project_id, job.job_id, key.attempt_id))

    def progress(self, job_id: str, key: AttemptKey, completed_units: int) -> bool:
        if type(completed_units) is not int or completed_units < 0:
            raise ValueError("invalid progress")
        with self._transaction() as session:
            job = self._job(session, job_id)
            attempt = self._current(session, job, key)
            if attempt is None or job.state != "running" or job.token_revoked:
                return False
            job.progress_units = completed_units
            return True

    def candidate(self, job_id: str, key: AttemptKey, candidate_manifest_id: str) -> bool:
        _identifier.validate_python(candidate_manifest_id)
        with self._transaction() as session:
            job = self._job(session, job_id)
            attempt = self._current(session, job, key)
            if attempt is None or job.state != "running" or job.token_revoked:
                return False
            job.candidate_manifest_id = candidate_manifest_id
            return True

    def cancel(self, job_id: str) -> RepositoryJobView:
        with self._transaction() as session:
            job = self._job(session, job_id)
            if job.state == "queued":
                job.state = "cancelled"
                job.retry_pending = False
            elif job.state in {"running", "failed"} and job.compute_allocated:
                job.state = "cancel_requested"
                job.retry_pending = False
                job.token_revoked = True
                attempt = session.get(Attempt, (self.project_id, job_id, job.current_attempt_id))
                attempt.token_revoked = True
                attempt.state = "cancel_requested"
            return self._view(session, job)

    def cancel_ack(self, job_id: str, key: AttemptKey) -> bool:
        with self._transaction() as session:
            job = self._job(session, job_id)
            return self._current(session, job, key) is not None and job.state == "cancel_requested"

    def fail(self, job_id: str, key: AttemptKey, *, retryable: bool) -> RepositoryJobView:
        if type(retryable) is not bool:
            raise ValueError("retryable must be bool")
        with self._transaction() as session:
            job = self._job(session, job_id)
            attempt = self._current(session, job, key)
            if attempt is None or job.state not in {"running", "cancel_requested"}:
                raise ValueError("attempt cannot fail")
            cancelling = job.state == "cancel_requested"
            job.state = "cancel_requested" if cancelling else "failed"
            job.retry_pending = not cancelling and retryable and job.attempts_started < self.retry_policy.max_attempts
            job.token_revoked = True
            attempt.state = "cancel_requested" if cancelling else "failed"
            attempt.token_revoked = True
            return self._view(session, job)

    def confirm_stopped(self, job_id: str, key: AttemptKey) -> RepositoryJobView:
        """Only the native process-group observer may call after confirmed stop."""
        with self._transaction() as session:
            job = self._job(session, job_id)
            attempt = self._current(session, job, key)
            if attempt is None or not job.compute_allocated:
                raise ValueError("attempt is not allocated")
            job.compute_allocated, job.stop_confirmed = False, True
            job.token_revoked = True
            attempt.stop_confirmed = attempt.token_revoked = True
            if job.state == "cancel_requested":
                job.state = "cancelled"
                attempt.state = "cancelled"
            elif job.state == "failed" and job.retry_pending:
                job.state = "queued"
                job.backoff_required = True
            elif job.state == "running":
                job.state = "failed"
                attempt.state = "failed"
            job.retry_pending = False
            return self._view(session, job)

    def reconcile_stopped(self, job_id: str, key: AttemptKey) -> RepositoryJobView:
        """Native observer has proved the previous owner generation stopped."""
        with self._transaction() as session:
            job = self._job(session, job_id)
            if (not job.recovery_required or not job.compute_allocated or key.job_id != job_id
                    or key.attempt_id != job.current_attempt_id or key.generation_token != job.current_token):
                raise ValueError("recovery attempt mismatch")
            attempt = session.get(Attempt, (self.project_id, job_id, key.attempt_id))
            if attempt is None:
                raise ValueError("recovery attempt missing")
            attempt.stop_confirmed = attempt.token_revoked = True
            job.stop_confirmed, job.compute_allocated = True, False
            job.recovery_required = False
            if job.state == "cancel_requested":
                job.state = "cancelled"
                attempt.state = "cancelled"
            elif job.state == "failed" and job.retry_pending:
                job.state = "queued"
                job.backoff_required = True
            elif job.state == "running":
                job.state = "failed"
                attempt.state = "failed"
            job.retry_pending = False
            return self._view(session, job)

    def publish(self, job_id: str, key: AttemptKey, publication_id: str,
                artifacts: tuple[tuple[str, str, str, int], ...] = ()) -> RepositoryJobView:
        """Register caller-validated immutable bytes after transaction-time fencing."""
        _identifier.validate_python(publication_id)
        if not artifacts:
            raise ValueError("publication inventory required")
        for asset_id, relative_path, sha256, size_bytes in artifacts:
            _identifier.validate_python(asset_id)
            if (not isinstance(relative_path, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", relative_path)
                    or any(part in ("", ".", "..") for part in relative_path.split("/"))
                    or any(part.endswith(".") or part.split(".")[0].upper() in _WINDOWS_DEVICES
                           for part in relative_path.split("/"))
                    or not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256)
                    or type(size_bytes) is not int or size_bytes < 0):
                raise ValueError("invalid artifact inventory")
        with self._transaction() as session:
            job = self._job(session, job_id)
            attempt = self._current(session, job, key)
            if (attempt is None or job.state != "running" or not job.compute_allocated
                    or job.token_revoked or attempt.token_revoked):
                raise ValueError("publication not authorized")
            if session.scalar(select(Publication).where(Publication.project_id == self.project_id,
                                                        Publication.job_id == job_id)):
                raise ValueError("job already published")
            if session.get(Publication, (self.project_id, publication_id)):
                raise ValueError("publication ID already exists in project")
            session.add(Publication(project_id=self.project_id, publication_id=publication_id,
                                    job_id=job_id, attempt_id=key.attempt_id, available=True))
            # Keep the FK parent insertion explicit: these independent ORM
            # mappers intentionally have no relationship objects/UOW cascade.
            # This flush remains inside the same conditional write transaction.
            session.flush()
            for asset_id, relative_path, sha256, size_bytes in artifacts:
                session.add(Artifact(project_id=self.project_id, publication_id=publication_id,
                                     asset_id=asset_id, relative_path=relative_path,
                                     sha256=sha256, size_bytes=size_bytes, available=True))
            job.state = "succeeded"
            attempt.state = "succeeded"
            session.flush()
            return self._view(session, job)

    def retain_dependency(self, job_id: str, dependency_id: str) -> RepositoryJobView:
        _identifier.validate_python(dependency_id)
        with self._transaction() as session:
            job = self._job(session, job_id)
            if session.get(DependencyPin, (self.project_id, job_id, dependency_id)) is None:
                session.add(DependencyPin(project_id=self.project_id, job_id=job_id,
                                          dependency_id=dependency_id))
                session.flush()
            return self._view(session, job)

    def release_dependency(self, job_id: str, dependency_id: str) -> RepositoryJobView:
        with self._transaction() as session:
            job = self._job(session, job_id)
            pin = session.get(DependencyPin, (self.project_id, job_id, dependency_id))
            if pin:
                session.delete(pin)
                session.flush()
            return self._view(session, job)

    def acquire_dependency_lease(self, lease_id: str, dependency_id: str) -> None:
        _identifier.validate_python(lease_id)
        _identifier.validate_python(dependency_id)
        _identifier.validate_python(self.guard.owner_id)
        _epoch.validate_python(self.guard.owner_epoch)
        with self._transaction() as session:
            if session.get(DependencyLease, (self.project_id, lease_id)):
                raise ValueError("lease ID already exists")
            session.add(DependencyLease(project_id=self.project_id, lease_id=lease_id,
                                        dependency_id=dependency_id, owner_id=self.guard.owner_id,
                                        owner_epoch=self.guard.owner_epoch, active=True))

    def release_dependency_lease(self, lease_id: str) -> None:
        with self._transaction() as session:
            lease = session.get(DependencyLease, (self.project_id, lease_id))
            if lease is None or lease.owner_id != self.guard.owner_id or lease.owner_epoch != self.guard.owner_epoch:
                raise ValueError("unknown or stale lease")
            lease.active = False

    def reconcile_owner_leases(self, old_owner_id: str, old_owner_epoch: int,
                               evidence: OwnerStopEvidence) -> int:
        """Retire only leases of a native-confirmed stopped owner generation."""
        _identifier.validate_python(old_owner_id)
        _epoch.validate_python(old_owner_epoch)
        if old_owner_epoch >= self.guard.owner_epoch:
            raise ValueError("old owner epoch must precede current owner")
        if evidence is None or not callable(getattr(evidence, "assert_stopped", None)):
            raise TypeError("trusted owner stop evidence required")
        with self._transaction() as session:
            evidence.assert_stopped(self.project_id, old_owner_id, old_owner_epoch)
            leases = session.scalars(select(DependencyLease).where(
                DependencyLease.project_id == self.project_id,
                DependencyLease.owner_id == old_owner_id,
                DependencyLease.owner_epoch == old_owner_epoch,
                DependencyLease.active.is_(True))).all()
            for lease in leases:
                lease.active = False
            return len(leases)

    def dependency_retained(self, dependency_id: str) -> bool:
        with self._transaction() as session:
            return bool(session.scalar(select(DependencyPin.dependency_id).where(
                DependencyPin.project_id == self.project_id, DependencyPin.dependency_id == dependency_id))
                or session.scalar(select(DependencyLease.lease_id).where(
                    DependencyLease.project_id == self.project_id,
                    DependencyLease.dependency_id == dependency_id,
                    DependencyLease.active.is_(True))))

    def collect_unretained(self, dependency_id: str, collector, *, policy_id: str) -> bool:
        """Coordinator-only GC under a configured retention decision and DB lock.

        collector deletes only a pre-registered disposable file by verified
        handle. No directory traversal or source-file deletion policy is inferred.
        The write transaction blocks concurrent pin/lease insertion until the
        callback completes. File deletion and commit still need crash reconcile.
        """
        _identifier.validate_python(dependency_id)
        _identifier.validate_python(policy_id)
        if not callable(collector):
            raise TypeError("trusted collector required")
        with self._transaction() as session:
            if session.scalar(select(Job.job_id).where(Job.project_id == self.project_id,
                                                       Job.compute_allocated.is_(True))):
                raise ValueError("GC blocked until compute stop is confirmed")
            pinned = session.scalar(select(DependencyPin.dependency_id).where(
                DependencyPin.project_id == self.project_id, DependencyPin.dependency_id == dependency_id))
            leased = session.scalar(select(DependencyLease.lease_id).where(
                DependencyLease.project_id == self.project_id, DependencyLease.dependency_id == dependency_id,
                DependencyLease.active.is_(True)))
            if pinned or leased:
                return False
            self.lease.assert_held(self.project_id)
            collector()
            for artifact in session.scalars(select(Artifact).where(Artifact.project_id == self.project_id,
                                                                    Artifact.asset_id == dependency_id)):
                artifact.available = False
                session.get(Publication, (self.project_id, artifact.publication_id)).available = False
            return True

    def artifact_inventory(self, job_id: str) -> tuple[ArtifactInventoryRecord, ...]:
        with self._transaction() as session:
            self._job(session, job_id)
            publication = session.scalar(select(Publication).where(Publication.project_id == self.project_id,
                                                                   Publication.job_id == job_id))
            if publication is None:
                return ()
            return tuple(ArtifactInventoryRecord(row.publication_id, row.asset_id,
                                                  row.relative_path, row.sha256,
                                                  row.size_bytes, row.available)
                         for row in session.scalars(select(Artifact).where(
                             Artifact.project_id == self.project_id,
                             Artifact.publication_id == publication.publication_id).order_by(Artifact.asset_id)))

    def get_publication(self, job_id: str) -> PublicationRecord | None:
        with self._transaction() as session:
            self._job(session, job_id)
            publication = session.scalar(select(Publication).where(Publication.project_id == self.project_id,
                                                                   Publication.job_id == job_id))
            if publication is None:
                return None
            inventory = tuple(ArtifactInventoryRecord(row.publication_id, row.asset_id,
                                                      row.relative_path, row.sha256,
                                                      row.size_bytes, row.available)
                              for row in session.scalars(select(Artifact).where(
                                  Artifact.project_id == self.project_id,
                                  Artifact.publication_id == publication.publication_id).order_by(Artifact.asset_id)))
            return PublicationRecord(self.project_id, job_id, publication.publication_id,
                                     publication.attempt_id, publication.available, inventory)

    def recovery_views(self) -> tuple[RepositoryJobView, ...]:
        with self._transaction() as session:
            return tuple(self._view(session, job) for job in session.scalars(
                select(Job).where(Job.project_id == self.project_id,
                                  Job.recovery_required.is_(True)).order_by(Job.job_id)))

    def mark_artifact_unavailable(self, publication_id: str, asset_id: str) -> None:
        """Reconciler records missing or mismatched bytes; never fabricates them."""
        with self._transaction() as session:
            artifact = session.get(Artifact, (self.project_id, publication_id, asset_id))
            if artifact is None:
                raise ValueError("unknown artifact")
            artifact.available = False
            session.get(Publication, (self.project_id, publication_id)).available = False

    def reconcile_artifacts(self, verifier: Callable[[ArtifactInventoryRecord], bool]) -> tuple[tuple[str, str], ...]:
        """Demote bytes rejected by a trusted native file-handle verifier."""
        if not callable(verifier):
            raise TypeError("verifier required")
        unavailable = []
        with self._transaction() as session:
            for artifact in session.scalars(select(Artifact).where(Artifact.project_id == self.project_id)):
                record = ArtifactInventoryRecord(artifact.publication_id, artifact.asset_id,
                                                 artifact.relative_path, artifact.sha256,
                                                 artifact.size_bytes, artifact.available)
                valid = verifier(record)
                if type(valid) is not bool:
                    raise ValueError("verifier must return bool")
                if not valid:
                    artifact.available = False
                    session.get(Publication, (self.project_id, artifact.publication_id)).available = False
                    unavailable.append((artifact.publication_id, artifact.asset_id))
        return tuple(unavailable)

    def backup(self, destination: str | Path) -> None:
        """SQLite online backup includes committed WAL content under writer guard."""
        target = _local_path(destination, existing=False)
        if target.exists():
            raise ValueError("backup destination exists")
        with self._operation():
            source = self.engine.raw_connection()
            try:
                with sqlite3.connect(target) as dest:
                    self.lease.assert_held(self.project_id)
                    source.driver_connection.backup(dest)
            finally:
                source.close()


def restore_project(source: str | Path, destination: str | Path, project_id: str,
                    guard: WriterGuard, retry_policy) -> None:
    """Validate backup and restore with SQLite backup API under a writer lease."""
    _identifier.validate_python(project_id)
    guard.assert_held(project_id)
    lease = guard.retain(project_id)
    try:
        backup = _local_path(source, existing=True)
        target = _local_path(destination, existing=False)
        if target.exists():
            raise ValueError("restore destination exists")
        with sqlite3.connect(backup) as source_db:
            version = source_db.execute("SELECT version_num FROM alembic_version").fetchone()
            meta = source_db.execute("SELECT project_id, schema_profile FROM project_meta").fetchall()
            source_db.execute("PRAGMA foreign_keys=ON")
            if (version != ("0001_initial",) or meta != [(project_id, "0.1.0")]
                    or source_db.execute("PRAGMA foreign_key_check").fetchone() is not None
                    or source_db.execute("PRAGMA integrity_check").fetchone() != ("ok",)):
                raise ValueError("backup validation failed")
            check_engine = create_engine(f"sqlite:///{backup.as_posix()}", future=True)
            try:
                with Session(check_engine) as check_session:
                    _validate_metadata(check_session, project_id)
            finally:
                check_engine.dispose()
            with sqlite3.connect(target) as target_db:
                source_db.backup(target_db)
                target_db.execute("UPDATE jobs SET recovery_required=1, token_revoked=1 WHERE compute_allocated=1")
                target_db.execute("UPDATE attempts SET token_revoked=1 WHERE (project_id,job_id,attempt_id) IN (SELECT project_id,job_id,current_attempt_id FROM jobs WHERE compute_allocated=1)")
                target_db.commit()
        repo = ProjectRepository.open(target, project_id, guard, retry_policy)
        repo.close()
    finally:
        lease.close()
