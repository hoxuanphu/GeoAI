"""Technical API metadata cannot grant execution ownership or inference."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from pydantic import ValidationError
from geoai.contracts import HealthResponse, CapabilitiesResponse, WIRE_MODELS
import geoai.contracts as contracts

ROOT = Path(__file__).resolve().parents[2]


class ApiContractTests(unittest.TestCase):
    def test_private_session_descriptor_is_canonical_and_rejects_credential_exfiltration(self):
        self.assertTrue(hasattr(contracts, "SessionDescriptor"), "Private handoff needs canonical Pydantic DTO")
        model = contracts.SessionDescriptor
        valid = {"base_url": "http://127.0.0.1:49231", "token": "synthetic-private-token-0123456789"}
        descriptor = model.model_validate(valid)
        self.assertNotIn(valid["token"], repr(descriptor))
        self.assertIs(contracts.PRIVATE_CONTEXT_MODELS["SessionDescriptor"], model)
        self.assertNotIn("SessionDescriptor", contracts.CONTRACT_MODELS)
        for url in ("https://attacker.invalid", "http://localhost:49231", "http://127.0.0.1:0", "http://127.0.0.1:65536", "http://127.0.0.1:80/", "http://127.0.0.1:80?token=x", "http://user@127.0.0.1:80", "http://127.0.0.1:00080"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                model.model_validate({**valid, "base_url": url})
    def test_api_dtos_are_registered_and_reject_unknown_fields_or_versions(self):
        fixture = json.loads((ROOT / "tests/fixtures/contracts/api.json").read_text())
        for model in (HealthResponse, CapabilitiesResponse):
            self.assertIs(WIRE_MODELS[model.__name__], model)
            model.model_validate(fixture[model.__name__])
            for extra in ({"token": "must-not-be-exported"}, {"schema_version": "9.0.0"}):
                with self.assertRaises(ValidationError):
                    model.model_validate({**fixture[model.__name__], **extra})

    def test_metadata_capabilities_cannot_promote_unimplemented_execution(self):
        for field in ("inference_ready", "execution_owner_ready", "native_launcher_ready", "project_writer_ready"):
            with self.assertRaises(ValidationError):
                CapabilitiesResponse.model_validate({field: True})

    def test_openapi_and_generated_client_are_deterministic_and_current(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/export_api_client.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads((ROOT / "schemas/openapi-v0.1.0.json").read_text())
        self.assertEqual(set(document["paths"]), {"/v1/health", "/v1/capabilities"})
        self.assertEqual(document["components"]["securitySchemes"]["HTTPBearer"]["scheme"], "bearer")
