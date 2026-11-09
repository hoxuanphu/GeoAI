"""Technical metadata only; no execution ownership is granted by these DTOs."""
from typing import Annotated, Literal
from pydantic import Field, StringConstraints, model_validator
from .common import SCHEMA_VERSION, Text, ValueModel


class HealthResponse(ValueModel):
    status: Literal["ok"] = "ok"
    app_version: Text
    schema_version: Literal["0.1.0"] = SCHEMA_VERSION


class CapabilitiesResponse(ValueModel):
    schema_version: Literal["0.1.0"] = SCHEMA_VERSION
    runtime: Literal["python-local-metadata"] = "python-local-metadata"
    features: tuple[Literal["health", "capabilities"], ...] = ("health", "capabilities")
    technical_ready: Literal[True] = True
    inference_ready: Literal[False] = False
    execution_owner_ready: Literal[False] = False
    native_launcher_ready: Literal[False] = False
    project_writer_ready: Literal[False] = False


class SessionDescriptor(ValueModel):
    """Private native/dev pipe handoff only; never durable project metadata."""
    base_url: Annotated[str, StringConstraints(strict=True, pattern=r"^http://127\.0\.0\.1:[1-9][0-9]{0,4}$")]
    token: Annotated[str, StringConstraints(strict=True, min_length=20, max_length=256, pattern=r"^[A-Za-z0-9_-]+$")] = Field(repr=False)

    @model_validator(mode="after")
    def valid_port(self):
        if int(self.base_url.rsplit(":", 1)[1]) > 65535:
            raise ValueError("Invalid local session port")
        return self
