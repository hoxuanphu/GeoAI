"""Only technical metadata routes; no filesystem or execution endpoints."""
from fastapi import FastAPI, Security
from fastapi.security import HTTPBearer
from geoai.contracts.api import HealthResponse, CapabilitiesResponse
from .session import SessionBoundary, SessionPolicy


def create_app(policy: SessionPolicy) -> FastAPI:
    app = FastAPI(title="GeoAI local foundation", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None, dependencies=[Security(HTTPBearer(auto_error=False))])
    app.add_middleware(SessionBoundary, policy=policy)

    @app.get("/v1/health", response_model=HealthResponse, operation_id="getHealth")
    def health() -> HealthResponse:
        return HealthResponse(app_version="0.1.0")

    @app.get("/v1/capabilities", response_model=CapabilitiesResponse, operation_id="getCapabilities")
    def capabilities() -> CapabilitiesResponse:
        return CapabilitiesResponse()

    return app
