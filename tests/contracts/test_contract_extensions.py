"""Missing draft boundary behavior, using synthetic data only."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pydantic import ValidationError

c = importlib.import_module("geoai.contracts")
ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/contracts"
WORKFLOW = json.loads((FIXTURES / "workflow.json").read_text(encoding="utf-8"))
HASH = "a" * 64
ATTEMPT = deepcopy(WORKFLOW["RunManifest"]["attempt"])
BUDGET = deepcopy(WORKFLOW["JobSpec"]["resource_budget"])
START = {
    "attempt": ATTEMPT, "job_spec_id": "job:1", "input_snapshot_id": "snapshot:1",
    "access_context_id": "access:1", "access_context_sha256": HASH,
    "resource_budget": BUDGET,
}
CONTEXT = {
    "schema_version": "0.1.0", "created_at": "2026-11-08T00:00:00Z",
    "access_context_id": "access:1", "project_id": "project:1", "worker_id": "worker:1",
    "launch_nonce": "launch:1", "execution_owner_id": "owner:1", "owner_epoch": 1,
    "attempt": ATTEMPT, "job_spec_id": "job:1", "job_spec_sha256": HASH,
    "input_snapshot_id": "snapshot:1", "input_snapshot_sha256": HASH,
    "read_entries": [
        {"ref_id": "job:1", "kind": "manifest", "sha256": HASH, "size_bytes": 128,
         "permission": "read_only", "location": {"kind": "managed-local", "root_id": "root:1", "relative_path": "manifests/job-1.json"}},
        {"ref_id": "snapshot:1", "kind": "manifest", "sha256": HASH, "size_bytes": 128,
         "permission": "read_only", "location": {"kind": "managed-local", "root_id": "root:1", "relative_path": "manifests/snapshot-1.json"}},
        {"ref_id": "local:input:1", "kind": "input", "sha256": HASH, "size_bytes": 128,
         "permission": "read_only", "location": {"kind": "external-registered-local", "registration_id": "registration:1", "absolute_path": "C:\\GeoAI-Synthetic\\input.tif", "file_identity": {"volume_id": "volume:fixture", "file_id": "file:fixture"}}},
    ],
    "staging_id": "staging:1", "resource_budget": BUDGET,
}


class ExtendedContractTests(unittest.TestCase):
    def require(self, name):
        self.assertTrue(hasattr(c, name), f"missing contract {name}")
        return getattr(c, name)

    def validate(self, name, payload):
        return self.require(name).model_validate(payload)

    def reject(self, name, payload):
        model = self.require(name)
        with self.assertRaises(ValidationError):
            model.model_validate(payload)

    def test_all_rpc_methods_accept_only_their_typed_params(self):
        cases = {
            "capabilities": {"protocol_version": "0.1.0", "schema_version": "0.1.0"},
            "start": START, "cancel": {"attempt": ATTEMPT}, "shutdown": {"graceful": True},
        }
        for method, params in cases.items():
            with self.subTest(method=method):
                self.validate("RpcRequest", {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
                other = "cancel" if method != "cancel" else "shutdown"
                self.reject("RpcRequest", {"jsonrpc": "2.0", "id": 1, "method": other, "params": params})

    def test_start_requires_context_hash_and_matching_job(self):
        for field in ("access_context_id", "access_context_sha256"):
            params = deepcopy(START); del params[field]
            self.reject("RpcRequest", {"jsonrpc": "2.0", "id": "1", "method": "start", "params": params})
        params = deepcopy(START); params["job_spec_id"] = "job:other"
        self.reject("RpcRequest", {"jsonrpc": "2.0", "id": "1", "method": "start", "params": params})

    def test_every_attempt_event_has_a_valid_positive_case(self):
        cases = {
            "heartbeat": {}, "progress": {"phase": "infer", "completed_units": 3, "total_units": 10},
            "artifact_candidate": {"candidate_manifest_id": "candidate:1"},
            "completed": {"candidate_manifest_id": "candidate:1"},
            "error": {"error": {"code": "invalid_input", "message": "Synthetic failure", "retryable": False}},
        }
        for method, extra in cases.items():
            payload = {"jsonrpc": "2.0", "method": method, "params": {"attempt": ATTEMPT, **extra}}
            with self.subTest(method=method):
                self.validate("RpcNotification", payload)
                del payload["params"]["attempt"]
                self.reject("RpcNotification", payload)

    def test_progress_without_total_is_valid_but_invalid_counts_are_rejected(self):
        payload = {"jsonrpc": "2.0", "method": "progress", "params": {"attempt": ATTEMPT, "phase": "infer", "completed_units": 0}}
        self.validate("RpcNotification", payload)
        for value in (-1, True, 1.5, "2"):
            p = deepcopy(payload); p["params"]["completed_units"] = value
            self.reject("RpcNotification", p)
        p = deepcopy(payload); p["params"]["total_units"] = -1
        self.reject("RpcNotification", p)

    def test_rpc_ids_and_boolean_parameters_are_strict(self):
        for identity in (True, None, 1.5):
            self.reject("RpcRequest", {"jsonrpc": "2.0", "id": identity, "method": "shutdown", "params": {"graceful": True}})
        for value in (1, "true"):
            self.reject("RpcRequest", {"jsonrpc": "2.0", "id": "1", "method": "shutdown", "params": {"graceful": value}})

    def test_accepted_acknowledgement_requires_boolean(self):
        self.validate("RpcSuccess", {"jsonrpc": "2.0", "id": "1", "result": {"accepted": True}})
        for value in (1, "true"):
            self.reject("RpcSuccess", {"jsonrpc": "2.0", "id": "1", "result": {"accepted": value}})

    def test_metrics_contain_finite_numbers_including_per_class(self):
        p = deepcopy(WORKFLOW["EvaluationRecord"])
        p["metrics"] = {"macro_f1": 0.8}
        p["per_class_metrics"] = {"0": {"precision": 0.9, "recall": 0.7}}
        self.validate("EvaluationRecord", p)
        for value in (True, "0.8", None, [0.8]):
            p = deepcopy(WORKFLOW["EvaluationRecord"]); p["metrics"] = {"macro_f1": value}
            self.reject("EvaluationRecord", p)
        for value in (True, "0.8", None, float("nan")):
            p = deepcopy(WORKFLOW["EvaluationRecord"]); p["per_class_metrics"] = {"0": {"f1": value}}
            self.reject("EvaluationRecord", p)

    def test_rpc_result_null_is_present_and_error_response_ids_follow_profile(self):
        self.validate("RpcSuccess", {"jsonrpc": "2.0", "id": "1", "result": None})
        self.reject("RpcSuccess", {"jsonrpc": "2.0", "id": "1"})
        self.reject("RpcSuccess", {"jsonrpc": "2.0", "id": None, "result": None})
        for code in (-32700, -32600):
            self.validate("RpcFailure", {"jsonrpc": "2.0", "id": None, "error": {"code": code, "message": "Invalid JSON"}})
        self.reject("RpcFailure", {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "Failure"}})
        self.reject("RpcFailure", {"jsonrpc": "2.0", "id": "1"})
        self.reject("RpcFailure", {"jsonrpc": "2.0", "id": True, "error": {"code": -32603, "message": "Failure"}})

    def test_domain_rpc_error_requires_structured_error(self):
        self.validate("RpcFailure", {"jsonrpc": "2.0", "id": "1", "error": {"code": -32001, "message": "Rejected", "data": {"code": "unsupported_schema", "message": "Rejected", "retryable": False}}})
        self.reject("RpcFailure", {"jsonrpc": "2.0", "id": "1", "error": {"code": -32001, "message": "Rejected"}})

    def test_open_json_fields_reject_nested_nonfinite_values(self):
        for name, field in (("JobSpec", "parameters"), ("EvaluationRecord", "metrics"), ("EvaluationRecord", "per_class_metrics"), ("MetricsSnapshot", "metrics")):
            for number in (float("nan"), float("inf"), -float("inf")):
                p = deepcopy(WORKFLOW[name]); p[field] = {"nested": {"values": [number]}}
                with self.subTest(name=name, field=field, number=number): self.reject(name, p)
        self.reject("RpcSuccess", {"jsonrpc": "2.0", "id": "1", "result": {"nested": [float("inf")]}})

    def test_resource_budget_and_grid_dimensions_reject_coercion(self):
        for value in (True, 1.5, "2"):
            p = deepcopy(WORKFLOW["JobSpec"]); p["resource_budget"]["cpu_threads"] = value
            self.reject("JobSpec", p)
            p = deepcopy(WORKFLOW["GridSpec"]); p["width"] = value
            self.reject("GridSpec", p)

    def test_compute_policy_and_execution_references(self):
        for policy in ("cpu", "auto", "gpu:device-1"):
            p = deepcopy(WORKFLOW["JobSpec"]); p["compute_policy"] = policy
            self.validate("JobSpec", p)
        for policy in ("gpu:", "gpu:http://example", "magic"):
            p = deepcopy(WORKFLOW["JobSpec"]); p["compute_policy"] = policy
            self.reject("JobSpec", p)
        for kind, models, physicals in (("ml", [], []), ("hybrid", ["model:1"], []), ("hybrid", [], ["physical:1"])):
            p = deepcopy(WORKFLOW["JobSpec"]); p.update(execution_kind=kind, model_ids=models, physical_model_ids=physicals)
            self.reject("JobSpec", p)
        p = deepcopy(WORKFLOW["JobSpec"]); p.update(execution_kind="physical", model_ids=[], physical_model_ids=["physical:1"])
        self.validate("JobSpec", p)
        p.update(execution_kind="gis", physical_model_ids=[])
        self.validate("JobSpec", p)

    def test_fallback_requires_reason_and_gpu_runtime_requires_provenance(self):
        p = deepcopy(WORKFLOW["RunManifest"]); p["used_fallback"] = True
        self.reject("RunManifest", p)
        p["fallback_reason"] = "Synthetic capability fallback"
        self.validate("RunManifest", p)
        p["runtime"]["backend"] = "cuda"
        self.reject("RunManifest", p)
        p["runtime"].update(device_id="gpu:fixture", driver_version="fixture-driver")
        self.validate("RunManifest", p)

    def test_physical_run_provenance_is_rejected_until_typed_feature_profile_exists(self):
        p = deepcopy(WORKFLOW["RunManifest"])
        p.update(physical_model_ids=["physical:fixture"], physical_provenance={"parameter_snapshot_ids": ["parameter:1"], "sha256": HASH})
        self.reject("RunManifest", p)
        p["physical_model_ids"] = []
        self.reject("RunManifest", p)

    def test_review_metadata_and_self_parent_are_consistent(self):
        p = deepcopy(WORKFLOW["ResultRevision"])
        p.update(review_state="reviewed", reviewed_by="reviewer:1", reviewed_at="2026-11-08T01:00:00Z")
        self.validate("ResultRevision", p)
        p["review_state"] = "unreviewed"
        self.reject("ResultRevision", p)
        p = deepcopy(WORKFLOW["ResultRevision"]); p["parent_revision_id"] = p["revision_id"]
        self.reject("ResultRevision", p)

    def test_business_gate_requires_gate_and_official_report_review(self):
        p = deepcopy(WORKFLOW["EvaluationRecord"]); p.update(kind="business", gate_decision="pass")
        self.reject("EvaluationRecord", p)
        p["gate_id"] = "gate:approved-fixture-v1"
        self.validate("EvaluationRecord", p)
        p = deepcopy(WORKFLOW["ReportContext"]); p.update(report_kind="official", review_state_snapshot="reviewed")
        self.validate("ReportContext", p)

    def test_business_segmentation_with_trained_decoder_and_evidence_is_valid(self):
        p = deepcopy(WORKFLOW["ModelSpec"])
        p.update(readiness="business", decoder_trained=True, evaluation_ids=["evaluation:fixture"])
        self.validate("ModelSpec", p)

    def test_private_context_typed_locations_and_manifest_bindings(self):
        context = self.validate("WorkerAccessContext", CONTEXT)
        self.assertEqual(context.job_spec_id, "job:1")
        self.assertEqual(context.read_entries[2].location.file_identity.file_id, "file:fixture")
        for change in ("duplicate_ref", "wrong_job", "wrong_manifest_hash", "missing_manifest", "writable", "unknown_location", "unregistered_external"):
            p = deepcopy(CONTEXT)
            if change == "duplicate_ref": p["read_entries"].append(p["read_entries"][0])
            elif change == "wrong_job": p["attempt"]["job_id"] = "job:other"
            elif change == "wrong_manifest_hash": p["read_entries"][0]["sha256"] = "b" * 64
            elif change == "missing_manifest": del p["read_entries"][0]
            elif change == "writable": p["read_entries"][0]["permission"] = "write"
            elif change == "unknown_location": p["read_entries"][0]["location"]["kind"] = "remote"
            else: del p["read_entries"][2]["location"]["registration_id"]
            with self.subTest(change=change): self.reject("WorkerAccessContext", p)

    def test_private_bootstrap_is_not_a_public_rpc_path(self):
        self.validate("WorkerBootstrap", {"schema_version": "0.1.0", "protocol_version": "0.1.0", "worker_id": "worker:1", "launch_nonce": "launch:1", "context_registry_path": "C:\\GeoAI-Synthetic\\registry"})
        p = deepcopy(START); p["context_registry_path"] = "C:\\GeoAI-Synthetic\\registry"
        self.reject("RpcRequest", {"jsonrpc": "2.0", "id": "1", "method": "start", "params": p})

    def test_complete_rpc_and_private_fixtures_round_trip(self):
        for filename, registry_name in (("rpc-workflow.json", "WIRE_MODELS"), ("worker-access-context.json", "PRIVATE_CONTEXT_MODELS")):
            with self.subTest(filename=filename):
                path = FIXTURES / filename
                self.assertTrue(path.is_file(), "missing complete wire/private fixture")
                for name, payload in json.loads(path.read_text(encoding="utf-8")).items():
                    model = getattr(c, registry_name)[name]
                    value = model.model_validate_json(json.dumps(payload))
                    self.assertEqual(value, model.model_validate_json(value.model_dump_json()))

    def test_exporter_is_deterministic_offline_from_other_cwd_and_check_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "contracts.json"
            command = [sys.executable, str(ROOT / "tools/export_contract_schemas.py"), "--output", str(output)]
            missing = subprocess.run(command + ["--check"], cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse(output.exists())
            generated = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            first = output.read_bytes()
            repeated = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(first, output.read_bytes())
            definitions = json.loads(first)["$defs"]
            for name in ("JobSpec", "RpcRequest", "RpcNotification", "WorkerAccessContext", "WorkerBootstrap"):
                self.assertIn(name, definitions)
            output.write_bytes(b"{}\n")
            stale = subprocess.run(command + ["--check"], cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertEqual(output.read_bytes(), b"{}\n")


if __name__ == "__main__":
    unittest.main()
