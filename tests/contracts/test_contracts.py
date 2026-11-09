"""Boundary invariants for synthetic contracts, not GIS/model validation."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pydantic import ValidationError

try:
    c = importlib.import_module("geoai.contracts")
except ModuleNotFoundError as exc:
    if exc.name not in {"geoai", "geoai.contracts"}:
        raise
    c = None

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / "tests/fixtures/contracts/workflow.json").read_text(encoding="utf-8"))


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(c, "geoai.contracts is not implemented yet")

    def payload(self, name):
        return deepcopy(FIXTURE[name])

    def test_workflow_payloads_round_trip_without_losing_identity(self):
        for name, payload in FIXTURE.items():
            with self.subTest(contract=name):
                model = c.CONTRACT_MODELS[name]
                item = model.model_validate_json(json.dumps(payload))
                again = model.model_validate_json(item.model_dump_json())
                self.assertEqual(again, item)
                self.assertEqual(item.schema_version, "0.1.0")

    def test_unknown_schema_version_is_rejected(self):
        p = self.payload("GridSpec"); p["schema_version"] = "9.0.0"
        with self.assertRaises(ValidationError): c.GridSpec.model_validate(p)

    def test_credentials_and_signed_urls_are_not_asset_fields(self):
        for field in ["credential", "download_url", "signed_url"]:
            p = self.payload("AssetRef"); p[field] = "sensitive-value"
            with self.subTest(field=field), self.assertRaises(ValidationError):
                c.AssetRef.model_validate(p)

    def test_asset_id_requires_provider_namespace(self):
        p = self.payload("AssetRef"); p["asset_id"] = "other:scene-1"
        with self.assertRaises(ValidationError): c.AssetRef.model_validate(p)

    def test_url_cannot_be_used_as_internal_asset_id(self):
        p = self.payload("AssetRef"); p["asset_id"] = "https://provider/scene?token=secret"
        with self.assertRaises(ValidationError): c.AssetRef.model_validate(p)

    def test_naive_persisted_time_is_rejected(self):
        p = self.payload("GridSpec"); p["created_at"] = "2026-11-08T07:00:00"
        with self.assertRaises(ValidationError): c.GridSpec.model_validate(p)

    def test_offset_time_is_normalized_to_utc(self):
        p = self.payload("GridSpec"); p["created_at"] = "2026-11-08T07:00:00+07:00"
        self.assertEqual(c.GridSpec.model_validate(p).created_at.isoformat(), "2026-11-08T00:00:00+00:00")

    def test_reversed_acquisition_range_is_rejected(self):
        p = self.payload("AssetRef"); p["acquisition"]["end"] = "2026-11-07T00:00:00Z"
        with self.assertRaises(ValidationError): c.AssetRef.model_validate(p)

    def test_polygon_requires_closed_ring_and_wgs84_ranges(self):
        for polygon in [
            {"type": "Polygon", "coordinates": [[[105,10],[106,10],[106,11],[105,11]]]},
            {"type": "Polygon", "coordinates": [[[500000,10],[106,10],[106,11],[500000,10]]]},
        ]:
            p = self.payload("InputSnapshot"); p["aoi"] = polygon
            with self.subTest(polygon=polygon), self.assertRaises(ValidationError):
                c.InputSnapshot.model_validate(p)

    def test_singular_affine_and_nonfinite_coefficients_are_rejected(self):
        for affine in [[1,2,0,2,4,0], [float("inf"),0,0,0,-30,0]]:
            p = self.payload("GridSpec"); p["affine"] = affine
            with self.subTest(affine=affine), self.assertRaises(ValidationError):
                c.GridSpec.model_validate(p)

    def test_categorical_grid_cannot_interpolate_class_ids(self):
        p = self.payload("GridSpec"); p["data_kind"] = "categorical"
        with self.assertRaises(ValidationError): c.GridSpec.model_validate(p)
        p["resampling"] = "nearest"
        self.assertEqual(c.GridSpec.model_validate(p).resampling, "nearest")

    def test_composite_snapshot_requires_recipe(self):
        p = self.payload("InputSnapshot"); p["temporal_selection"] = "composite"
        with self.assertRaises(ValidationError): c.InputSnapshot.model_validate(p)

    def test_model_band_count_must_match_tensor_and_stats(self):
        p = self.payload("ModelSpec"); p["band_order"] = ["red", "green", "blue"]
        with self.assertRaises(ValidationError): c.ModelSpec.model_validate(p)

    def test_zero_normalization_std_is_rejected(self):
        p = self.payload("ModelSpec"); p["normalization"]["std"][0] = 0
        with self.assertRaises(ValidationError): c.ModelSpec.model_validate(p)

    def test_random_decoder_cannot_be_business_ready(self):
        p = self.payload("ModelSpec"); p["readiness"] = "business"; p["evaluation_ids"] = ["evaluation:1"]
        with self.assertRaises(ValidationError): c.ModelSpec.model_validate(p)

    def test_business_model_requires_evaluation(self):
        p = self.payload("ModelSpec"); p["readiness"] = "business"; p["decoder_trained"] = True
        with self.assertRaises(ValidationError): c.ModelSpec.model_validate(p)

    def test_hydraulic_spec_requires_solver_identity(self):
        p = self.payload("PhysicalModelSpec"); p["method_id"] = "PHY-06"
        with self.assertRaises(ValidationError): c.PhysicalModelSpec.model_validate(p)

    def test_physical_job_requires_physical_model_reference(self):
        p = self.payload("JobSpec"); p["execution_kind"] = "physical"; p["model_ids"] = []
        with self.assertRaises(ValidationError): c.JobSpec.model_validate(p)

    def test_published_manifest_cannot_have_no_output(self):
        p = self.payload("RunManifest"); p["artifacts"] = []
        with self.assertRaises(ValidationError): c.RunManifest.model_validate(p)
        p["publication_state"] = "candidate"
        self.assertEqual(c.RunManifest.model_validate(p).publication_state, "candidate")

    def test_manifest_cannot_publish_for_another_job(self):
        p = self.payload("RunManifest"); p["attempt"]["job_id"] = "job:other"
        with self.assertRaises(ValidationError): c.RunManifest.model_validate(p)

    def test_physical_run_requires_parameter_forcing_provenance(self):
        p = self.payload("RunManifest"); p["physical_model_ids"] = ["physical:et0:fixture"]
        with self.assertRaises(ValidationError): c.RunManifest.model_validate(p)

    def test_reviewed_revision_requires_reviewer_and_time(self):
        p = self.payload("ResultRevision"); p["review_state"] = "reviewed"
        with self.assertRaises(ValidationError): c.ResultRevision.model_validate(p)

    def test_technical_evaluation_cannot_pass_business_gate(self):
        p = self.payload("EvaluationRecord"); p["gate_decision"] = "pass"; p["gate_id"] = "gate:1"
        with self.assertRaises(ValidationError): c.EvaluationRecord.model_validate(p)

    def test_official_report_requires_reviewed_snapshot(self):
        p = self.payload("ReportContext"); p["report_kind"] = "official"
        with self.assertRaises(ValidationError): c.ReportContext.model_validate(p)

    def test_coverage_is_fraction_not_percent(self):
        p = self.payload("MetricsSnapshot"); p["coverage_fraction"] = 75
        with self.assertRaises(ValidationError): c.MetricsSnapshot.model_validate(p)

    def test_rpc_boolean_id_is_not_an_integer_id(self):
        p = {"jsonrpc":"2.0", "id":True, "method":"capabilities", "params":{"protocol_version":"0.1.0", "schema_version":"0.1.0"}}
        with self.assertRaises(ValidationError): c.RpcRequest.model_validate(p)

    def test_rpc_start_requires_attempt_and_matching_job(self):
        p = {"jsonrpc":"2.0", "id":"1", "method":"start", "params":{"job_spec_id":"job:1"}}
        with self.assertRaises(ValidationError): c.RpcRequest.model_validate(p)
        p["params"] = {"attempt":self.payload("RunManifest")["attempt"], "job_spec_id":"job:other", "input_snapshot_id":"snapshot:1", "resource_budget":self.payload("JobSpec")["resource_budget"]}
        with self.assertRaises(ValidationError): c.RpcRequest.model_validate(p)

    def test_rpc_response_cannot_contain_both_result_and_error(self):
        p = {"jsonrpc":"2.0", "id":"1", "result":None, "error":{"code":-32603,"message":"failure"}}
        with self.assertRaises(ValidationError): c.RpcSuccess.model_validate(p)
        with self.assertRaises(ValidationError): c.RpcFailure.model_validate(p)

    def test_rpc_progress_cannot_exceed_total(self):
        p = {"jsonrpc":"2.0", "method":"progress", "params":{"attempt":self.payload("RunManifest")["attempt"], "completed_units":11, "total_units":10, "phase":"infer"}}
        with self.assertRaises(ValidationError): c.RpcNotification.model_validate(p)

    def test_exporter_check_detects_stale_generated_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "contracts.json"
            command = [sys.executable, str(ROOT / "tools/export_contract_schemas.py"), "--output", str(output)]
            good = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertIn("GridSpec", json.loads(output.read_text(encoding="utf-8"))["$defs"])
            output.write_text("{}\n", encoding="utf-8")
            stale = subprocess.run(command + ["--check"], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("stale", stale.stderr.lower())


if __name__ == "__main__":
    unittest.main()
