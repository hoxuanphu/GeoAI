"""Draft workflow records; references and publication remain service checks."""
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictFloat, StringConstraints, model_validator

from .common import (
    ArtifactRef, AttemptKey, Contract, Fraction, Identifier, JsonObject,
    ResourceBudget, Sha256, Text, TimeRange, UtcDateTime, ValueModel,
)
from .geography import Wgs84Geometry

ComputePolicy = Annotated[str, StringConstraints(pattern=r"^(cpu|auto|gpu:[A-Za-z0-9][A-Za-z0-9._:-]*)$")]
Representation = Literal["raster", "vector"]
ReviewState = Literal["unreviewed", "reviewed"]
NumericMetrics = dict[Text, StrictFloat]


class JobSpec(Contract):
    job_id: Identifier
    project_id: Identifier
    workflow_id: Identifier
    workflow_version: Text
    input_snapshot_id: Identifier
    grid_id: Identifier
    execution_kind: Literal["ml", "physical", "hybrid", "gis"]
    model_ids: tuple[Identifier, ...] = ()
    physical_model_ids: tuple[Identifier, ...] = ()
    parameter_snapshot_ids: tuple[Identifier, ...] = ()
    parameters: JsonObject
    compute_policy: ComputePolicy
    resource_budget: ResourceBudget
    idempotency_key: Identifier

    @model_validator(mode="after")
    def execution_references(self):
        if self.execution_kind in {"ml", "hybrid"} and not self.model_ids:
            raise ValueError("ML execution requires a model reference")
        if self.execution_kind in {"physical", "hybrid"} and not self.physical_model_ids:
            raise ValueError("physical execution requires a physical model reference")
        return self


class RuntimeProvenance(ValueModel):
    runtime_id: Identifier
    backend: Text
    runtime_version: Text
    precision: Literal["fp32", "fp16", "int8"]
    device_id: Identifier | None = None
    driver_version: Text | None = None

    @model_validator(mode="after")
    def gpu_identity(self):
        if self.backend.lower() in {"cuda", "tensorrt", "onnxruntime_cuda"} or self.device_id is not None:
            if self.device_id is None or self.driver_version is None:
                raise ValueError("GPU runtime requires device and driver provenance")
        if self.driver_version is not None and self.device_id is None:
            raise ValueError("driver provenance requires a device identity")
        return self


class RunManifest(Contract):
    run_id: Identifier
    job_id: Identifier
    attempt: AttemptKey
    input_snapshot_id: Identifier
    input_sha256: Sha256
    pipeline_sha256: Sha256
    config_sha256: Sha256
    grid_id: Identifier
    transform_ids: tuple[Identifier, ...] = ()
    model_ids: tuple[Identifier, ...] = ()
    physical_model_ids: tuple[Identifier, ...] = ()
    runtime: RuntimeProvenance
    used_fallback: StrictBool
    fallback_reason: Text | None = None
    coverage_fraction: Fraction
    artifacts: tuple[ArtifactRef, ...] = ()
    quality_flags: tuple[Text, ...] = ()
    publication_state: Literal["candidate", "published"]
    # No PHY feature-specific provenance schema has been selected. A free-form
    # dictionary here would falsely imply reproducibility of physical runs.
    physical_provenance: None = None

    @model_validator(mode="after")
    def publication_invariants(self):
        if self.attempt.job_id != self.job_id:
            raise ValueError("manifest job must match its attempt")
        if self.publication_state == "published" and not self.artifacts:
            raise ValueError("published manifest requires an artifact with checksum")
        if self.used_fallback and self.fallback_reason is None:
            raise ValueError("fallback requires a reason")
        if self.physical_model_ids:
            raise ValueError("physical run provenance is unsupported pending a typed feature-specific profile")
        return self


class ResultRevision(Contract):
    revision_id: Identifier
    base_run_id: Identifier
    parent_revision_id: Identifier | None = None
    edit_asset_ids: tuple[Identifier, ...] = ()
    representation: Representation
    class_schema_id: Identifier
    author_id: Identifier
    reason: Text
    review_state: ReviewState
    reviewed_by: Identifier | None = None
    reviewed_at: UtcDateTime | None = None

    @model_validator(mode="after")
    def review_and_lineage(self):
        if self.parent_revision_id == self.revision_id:
            raise ValueError("revision cannot be its own parent")
        if self.review_state == "reviewed":
            if self.reviewed_by is None or self.reviewed_at is None:
                raise ValueError("reviewed revision requires reviewer and time")
        elif self.reviewed_by is not None or self.reviewed_at is not None:
            raise ValueError("unreviewed revision cannot retain review metadata")
        return self


class EvaluationRecord(Contract):
    evaluation_id: Identifier
    dataset_id: Identifier
    split_id: Identifier
    target_model_id: Identifier
    kind: Literal["technical", "business"]
    metrics: NumericMetrics
    per_class_metrics: dict[Text, NumericMetrics]
    baseline_evaluation_id: Identifier | None = None
    gate_id: Identifier | None = None
    gate_decision: Literal["not_assessed", "pass", "fail"]
    limitations: tuple[Text, ...] = ()

    @model_validator(mode="after")
    def gate_evidence(self):
        if self.kind == "technical" and self.gate_decision == "pass":
            raise ValueError("technical evaluation cannot pass a business gate")
        if self.gate_decision == "pass" and self.gate_id is None:
            raise ValueError("business gate pass requires a gate reference")
        return self


class MetricsSnapshot(Contract):
    metrics_snapshot_id: Identifier
    run_id: Identifier
    revision_id: Identifier
    representation: Representation
    aoi: Wgs84Geometry
    coverage_fraction: Fraction
    metrics: NumericMetrics
    unit: Text
    method_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]


class ReportContext(Contract):
    report_context_id: Identifier
    revision_id: Identifier
    representation: Representation
    metrics_snapshot_id: Identifier
    aoi: Wgs84Geometry
    acquisition: TimeRange
    coverage_fraction: Fraction
    evaluation_ids: tuple[Identifier, ...] = ()
    model_ids: tuple[Identifier, ...] = ()
    physical_model_ids: tuple[Identifier, ...] = ()
    template_version: Text
    style_version: Text
    font_version: Text
    report_kind: Literal["draft", "official"]
    review_state_snapshot: ReviewState

    @model_validator(mode="after")
    def official_review(self):
        if self.report_kind == "official" and self.review_state_snapshot != "reviewed":
            raise ValueError("official report requires a reviewed revision snapshot")
        return self
