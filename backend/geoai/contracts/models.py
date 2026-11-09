"""ML and physical-model metadata; no model is loaded by this module."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import Contract, Identifier, PositiveFloat, PositiveInt, Sha256, Text, ValueModel


class WeightReference(ValueModel):
    component_id: Identifier
    revision: Text
    sha256: Sha256
    format: Literal["safetensors", "onnx", "pt"]
    conversion_record_id: Identifier | None = None


class TensorProfile(ValueModel):
    channels: PositiveInt
    frames: PositiveInt
    height: PositiveInt
    width: PositiveInt
    batch_min: PositiveInt = 1
    batch_max: PositiveInt = 1

    @model_validator(mode="after")
    def batch_range(self):
        if self.batch_max < self.batch_min:
            raise ValueError("batch_max must not be below batch_min")
        return self


class Normalization(ValueModel):
    unit: Text
    mean: Annotated[tuple[float, ...], Field(min_length=1)]
    std: Annotated[tuple[PositiveFloat, ...], Field(min_length=1)]


class ModelSpec(Contract):
    model_id: Identifier
    name: Text
    backbone: WeightReference
    decoder: WeightReference | None = None
    decoder_trained: bool = False
    task: Literal["segmentation", "classification", "regression", "reconstruction"]
    product_profile_id: Identifier
    band_order: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    tensor: TensorProfile
    normalization: Normalization
    metadata_policy: Literal["required_tl", "validated_without_metadata", "none"]
    gsd_m: PositiveFloat
    class_schema_id: Identifier | None = None
    runtime_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    precisions: Annotated[tuple[Literal["fp32", "fp16", "int8"], ...], Field(min_length=1)]
    license_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    evaluation_ids: tuple[Identifier, ...] = ()
    readiness: Literal["technical", "business"]

    @model_validator(mode="after")
    def compatible_profile_and_readiness(self):
        if len(set(self.band_order)) != len(self.band_order):
            raise ValueError("input bands must be unique")
        if {len(self.band_order), len(self.normalization.mean), len(self.normalization.std)} != {self.tensor.channels}:
            raise ValueError("bands and normalization must match channel count")
        if self.task in {"segmentation", "classification"} and self.class_schema_id is None:
            raise ValueError("class schema is required for class outputs")
        if self.readiness == "business":
            if not self.evaluation_ids:
                raise ValueError("business model requires evaluation")
            if self.task == "reconstruction":
                raise ValueError("reconstruction is not the required business analysis")
            if self.task == "segmentation" and (self.decoder is None or not self.decoder_trained):
                raise ValueError("business segmentation requires a trained decoder")
        return self


class PhysicalVariable(ValueModel):
    name: Identifier
    unit: Text
    role: Literal["input", "output", "parameter"]
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def valid_range(self):
        if self.minimum is not None and self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("variable maximum must not be below minimum")
        return self


class PhysicalModelSpec(Contract):
    physical_model_id: Identifier
    method_id: Literal["GEO-01", "PHY-01", "PHY-02", "PHY-03", "PHY-04", "PHY-05", "PHY-06", "PHY-07", "PHY-08"]
    method_version: Text
    method_kind: Literal["index", "physical", "semi_empirical", "terrain"]
    implementation_id: Identifier
    implementation_sha256: Sha256
    source_refs: Annotated[tuple[Text, ...], Field(min_length=1)]
    variables: Annotated[tuple[PhysicalVariable, ...], Field(min_length=1)]
    parameter_profile_id: Identifier
    grid_id: Identifier | None = None
    time_step_seconds: PositiveFloat | None = None
    vertical_datum: Text | None = None
    initial_condition_ref: Identifier | None = None
    boundary_refs: tuple[Identifier, ...] = ()
    solver_version: Text | None = None
    calibration_ids: tuple[Identifier, ...] = ()
    evaluation_ids: tuple[Identifier, ...] = ()
    uncertainty_policy_id: Identifier
    resume_capability: Literal["none", "chunk", "native_checkpoint"]
    readiness: Literal["technical", "business"]

    @model_validator(mode="after")
    def solver_and_evidence(self):
        if self.method_id == "PHY-06" and not self.solver_version:
            raise ValueError("hydraulic method requires solver version")
        if self.readiness == "business" and not self.evaluation_ids:
            raise ValueError("business physical method requires evaluation")
        if len({v.name for v in self.variables}) != len(self.variables):
            raise ValueError("variable names must be unique")
        return self


class DatasetVersion(Contract):
    dataset_id: Identifier
    label_asset_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    class_schema_id: Identifier
    split_id: Identifier
    split_method: Literal["spatial", "temporal", "spatial_temporal"]
    license_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    sha256: Sha256
