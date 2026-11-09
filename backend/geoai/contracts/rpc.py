"""Draft JSON-RPC envelopes and typed method/event parameters, no transport."""
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, JsonValue, StrictBool, StrictInt, StrictStr, model_validator

from .common import (
    AttemptKey, Identifier, NonNegativeInt, ResourceBudget, Sha256,
    StructuredError, Text, ValueModel, finite_json,
)

RpcId = StrictStr | StrictInt
FiniteJson = Annotated[JsonValue, AfterValidator(finite_json)]


class CapabilitiesParams(ValueModel):
    protocol_version: Literal["0.1.0"]
    schema_version: Literal["0.1.0"]


class StartParams(ValueModel):
    attempt: AttemptKey
    job_spec_id: Identifier
    input_snapshot_id: Identifier
    access_context_id: Identifier
    access_context_sha256: Sha256
    resource_budget: ResourceBudget

    @model_validator(mode="after")
    def matching_job(self):
        if self.job_spec_id != self.attempt.job_id:
            raise ValueError("start job must match its attempt")
        return self


class CancelParams(ValueModel):
    attempt: AttemptKey


class ShutdownParams(ValueModel):
    graceful: StrictBool


class RpcRequest(ValueModel):
    jsonrpc: Literal["2.0"]
    id: RpcId
    method: Literal["capabilities", "start", "cancel", "shutdown"]
    params: CapabilitiesParams | StartParams | CancelParams | ShutdownParams

    @model_validator(mode="after")
    def method_params(self):
        expected = {"capabilities": CapabilitiesParams, "start": StartParams, "cancel": CancelParams, "shutdown": ShutdownParams}
        if not isinstance(self.params, expected[self.method]):
            raise ValueError("params must match the requested method")
        return self


class HeartbeatParams(ValueModel):
    attempt: AttemptKey


class ProgressParams(HeartbeatParams):
    phase: Text
    completed_units: NonNegativeInt
    total_units: NonNegativeInt | None = None

    @model_validator(mode="after")
    def bounded_progress(self):
        if self.total_units is not None and self.completed_units > self.total_units:
            raise ValueError("completed progress cannot exceed total")
        return self


class CandidateParams(HeartbeatParams):
    candidate_manifest_id: Identifier


class ErrorParams(HeartbeatParams):
    error: StructuredError


class RpcNotification(ValueModel):
    jsonrpc: Literal["2.0"]
    method: Literal["heartbeat", "progress", "artifact_candidate", "completed", "error"]
    params: HeartbeatParams | ProgressParams | CandidateParams | ErrorParams

    @model_validator(mode="after")
    def method_params(self):
        expected = {"heartbeat": HeartbeatParams, "progress": ProgressParams, "artifact_candidate": CandidateParams, "completed": CandidateParams, "error": ErrorParams}
        if type(self.params) is not expected[self.method]:
            raise ValueError("params must match the event method")
        return self


class AcceptedResult(ValueModel):
    accepted: StrictBool


class RpcSuccess(ValueModel):
    jsonrpc: Literal["2.0"]
    id: RpcId
    result: FiniteJson

    @model_validator(mode="after")
    def accepted_result(self):
        # Success payloads remain generic JSON for capability negotiation, but
        # the draft accepted acknowledgement has a fixed shape and strict bool.
        if isinstance(self.result, dict) and "accepted" in self.result:
            AcceptedResult.model_validate(self.result)
        return self


class RpcError(ValueModel):
    code: StrictInt
    message: Text
    data: StructuredError | None = None

    @model_validator(mode="after")
    def standard_or_domain_error(self):
        standard = {-32700, -32600, -32601, -32602, -32603}
        if self.code not in standard and not -32099 <= self.code <= -32001:
            raise ValueError("unsupported JSON-RPC error code")
        if -32099 <= self.code <= -32001 and self.data is None:
            raise ValueError("domain error requires structured error data")
        return self


class RpcFailure(ValueModel):
    jsonrpc: Literal["2.0"]
    id: RpcId | None
    error: RpcError

    @model_validator(mode="after")
    def nullable_error_id(self):
        if self.id is None and self.error.code not in {-32700, -32600}:
            raise ValueError("only parse/invalid-request errors may have a null id")
        return self
