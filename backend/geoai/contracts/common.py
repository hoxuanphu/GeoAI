"""Shared values for draft contracts, independent of GIS and runtime libraries."""
from datetime import datetime, timezone
import math
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue, StringConstraints, model_validator

SCHEMA_VERSION = "0.1.0"
Identifier = Annotated[str, StringConstraints(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
PositiveFloat = Annotated[float, Field(gt=0)]
Fraction = Annotated[float, Field(ge=0, le=1)]


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone is required")
    return value.astimezone(timezone.utc)


UtcDateTime = Annotated[datetime, AfterValidator(utc)]


def finite_json(value: JsonValue) -> JsonValue:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("JSON numbers must be finite")
    if isinstance(value, dict):
        for child in value.values():
            finite_json(child)
    elif isinstance(value, list):
        for child in value:
            finite_json(child)
    return value


JsonObject = Annotated[dict[str, JsonValue], AfterValidator(finite_json)]


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, validate_default=True)


class Contract(ValueModel):
    schema_version: Literal["0.1.0"] = SCHEMA_VERSION
    created_at: UtcDateTime


class TimeRange(ValueModel):
    start: UtcDateTime
    end: UtcDateTime

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("end must not precede start")
        return self


class AttemptKey(ValueModel):
    job_id: Identifier
    attempt_id: Identifier
    generation_token: Identifier


class ResourceBudget(ValueModel):
    cpu_threads: PositiveInt
    ram_bytes: PositiveInt
    temporary_bytes: NonNegativeInt
    vram_bytes: NonNegativeInt = 0


class ArtifactRef(ValueModel):
    asset_id: Identifier
    sha256: Sha256
    size_bytes: NonNegativeInt
    media_type: Text


class StructuredError(ValueModel):
    code: Literal["unsupported_schema", "invalid_input", "missing_resource", "stale_attempt", "incompatible_model", "resource_exhausted", "cancelled", "internal_error"]
    message: Text
    retryable: bool
