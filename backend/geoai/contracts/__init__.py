"""Public draft contracts and a separate registry of private runtime values."""
from .common import (
    SCHEMA_VERSION, ArtifactRef, AttemptKey, Contract, ResourceBudget,
    StructuredError, TimeRange, ValueModel,
)
from .geography import (
    AssetRef, BandSpec, ContentIdentity, CrsRef, GridResource, GridSpec,
    InputSnapshot, TransformSpec, Wgs84Geometry,
)
from .models import (
    DatasetVersion, ModelSpec, Normalization, PhysicalModelSpec,
    PhysicalVariable, TensorProfile, WeightReference,
)
from .runs import (
    EvaluationRecord, JobSpec, MetricsSnapshot, ReportContext, ResultRevision,
    RunManifest, RuntimeProvenance,
)
from .rpc import (
    AcceptedResult, CancelParams, CandidateParams, CapabilitiesParams, ErrorParams,
    HeartbeatParams, ProgressParams, RpcError, RpcFailure, RpcNotification,
    RpcRequest, RpcSuccess, ShutdownParams, StartParams,
)
from .access import (
    ExternalRegisteredLocalLocation, FileIdentity, ManagedLocalLocation,
    WorkerAccessContext, WorkerBootstrap, WorkerReadEntry,
)
from .api import HealthResponse, CapabilitiesResponse, SessionDescriptor
from .imports import (
    ArchiveEntry, ArchiveInventory, ArchivePolicy, ProviderAssetBinding,
    ProviderEndpoint, ProviderPolicy, ProviderRequestPlan, ProviderStreamReceipt,
)

CONTRACT_MODELS = {model.__name__: model for model in (
    AssetRef, GridSpec, TransformSpec, InputSnapshot, ModelSpec,
    PhysicalModelSpec, DatasetVersion, JobSpec, RunManifest, ResultRevision,
    EvaluationRecord, MetricsSnapshot, ReportContext, ArchivePolicy, ArchiveInventory, ProviderPolicy,
)}
WIRE_MODELS = {model.__name__: model for model in (
    RpcRequest, RpcSuccess, RpcFailure, RpcNotification, AcceptedResult,
    HealthResponse, CapabilitiesResponse,
)}
PRIVATE_CONTEXT_MODELS = {model.__name__: model for model in (
    WorkerAccessContext, WorkerBootstrap, SessionDescriptor,
)}

__all__ = [
    "SCHEMA_VERSION", "ValueModel", "Contract", "ArtifactRef", "AttemptKey",
    "ResourceBudget", "StructuredError", "TimeRange", "AssetRef", "BandSpec",
    "ContentIdentity", "CrsRef", "GridResource", "GridSpec", "InputSnapshot",
    "TransformSpec", "Wgs84Geometry", "DatasetVersion", "ModelSpec",
    "Normalization", "PhysicalModelSpec", "PhysicalVariable", "TensorProfile",
    "WeightReference", "EvaluationRecord", "JobSpec", "MetricsSnapshot",
    "ReportContext", "ResultRevision", "RunManifest", "RuntimeProvenance",
    "AcceptedResult", "CancelParams", "CandidateParams", "CapabilitiesParams",
    "ErrorParams", "HeartbeatParams", "ProgressParams", "RpcError", "RpcFailure",
    "RpcNotification", "RpcRequest", "RpcSuccess", "ShutdownParams", "StartParams",
    "ExternalRegisteredLocalLocation", "FileIdentity", "ManagedLocalLocation",
    "WorkerAccessContext", "WorkerBootstrap", "WorkerReadEntry", "CONTRACT_MODELS",
    "WIRE_MODELS", "PRIVATE_CONTEXT_MODELS",
    "HealthResponse", "CapabilitiesResponse",
    "SessionDescriptor",
    "ArchiveEntry", "ArchiveInventory", "ArchivePolicy",
    "ProviderAssetBinding", "ProviderEndpoint", "ProviderPolicy", "ProviderRequestPlan", "ProviderStreamReceipt",
]
