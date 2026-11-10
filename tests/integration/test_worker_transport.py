"""Real Windows worker process and private-handle transport checks."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from geoai.contracts import StartParams, WorkerLaunchPacket
from geoai.contracts import JobSpec
from geoai.jobs.coordinator import JobCoordinator, RetryPolicy
from geoai.jobs.native_process import ManagedProcess
from geoai.jobs.transport import WorkerTransport, TransportError
from geoai.jobs.publisher import Publisher, PublicationError
from geoai.storage.io_resolver import WorkerIOResolver, ExternalRegistration
from geoai.storage.resolver import GrantRegistry
from geoai.storage.windows_io import NativeRoot, NativeIdentity


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_BYTES = b"GeoAI synthetic artifact\n"
WORKFLOW = json.loads((ROOT / "tests/fixtures/contracts/workflow.json").read_text(encoding="utf-8"))
CONTEXT = json.loads((ROOT / "tests/fixtures/contracts/worker-access-context.json").read_text(encoding="utf-8"))["WorkerAccessContext"]


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@unittest.skipUnless(os.name == "nt", "Windows managed process required")
class WorkerTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "project"
        self.root.mkdir()
        registry = base / "registry"
        registry.mkdir()
        job = deepcopy(WORKFLOW["JobSpec"])
        snapshot = deepcopy(WORKFLOW["InputSnapshot"])
        context = deepcopy(CONTEXT)
        job_json, snapshot_json = compact(job), compact(snapshot)
        context["job_spec_sha256"] = sha256(job_json.encode()).hexdigest()
        context["input_snapshot_sha256"] = sha256(snapshot_json.encode()).hexdigest()
        required = {job["workflow_id"], job["grid_id"], *job["model_ids"],
                    *job["physical_model_ids"], *job["parameter_snapshot_ids"],
                    *snapshot["asset_ids"], snapshot["qa_policy_id"],
                    *snapshot["transform_ids"], *snapshot["dependency_ids"]}
        if snapshot.get("mosaic_recipe_id"):
            required.add(snapshot["mosaic_recipe_id"])
        context["read_entries"] = context["read_entries"][:3]
        for entry, data in zip(context["read_entries"], (job_json, snapshot_json)):
            entry["sha256"] = sha256(data.encode()).hexdigest()
            entry["size_bytes"] = len(data.encode())
            location = entry["location"]
            if location["kind"] == "managed-local":
                path = self.root / location["relative_path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data.encode())
        for ref in sorted(required - {e["ref_id"] for e in context["read_entries"]}):
            entry = deepcopy(context["read_entries"][0])
            entry.update(ref_id=ref, kind="profile")
            context["read_entries"].append(entry)
        external_dir = base / "external"
        external_dir.mkdir()
        external_file = external_dir / "input.bin"
        external_file.write_bytes(b"fixture-input")
        with NativeRoot(external_dir) as root:
            with root.open_read("input.bin", sha256=sha256(external_file.read_bytes()).hexdigest(),
                                size_bytes=external_file.stat().st_size) as source:
                identity = source.identity
        external_entry = context["read_entries"][2]
        external_entry["sha256"] = sha256(external_file.read_bytes()).hexdigest()
        external_entry["size_bytes"] = external_file.stat().st_size
        external_entry["location"]["absolute_path"] = str(external_file)
        external_entry["location"]["file_identity"] = {
            "volume_id": identity.volume_id, "file_id": identity.file_id}
        context_json = compact(context)
        start = StartParams(attempt=context["attempt"], job_spec_id=context["job_spec_id"],
                            input_snapshot_id=context["input_snapshot_id"],
                            access_context_id=context["access_context_id"],
                            access_context_sha256=sha256(context_json.encode()).hexdigest(),
                            resource_budget=context["resource_budget"])
        staging = base / "staging"
        staging.mkdir()
        manifest = deepcopy(WORKFLOW["RunManifest"])
        manifest.update(attempt=context["attempt"], publication_state="candidate",
                        input_sha256=context["input_snapshot_sha256"],
                        pipeline_sha256=next(e["sha256"] for e in context["read_entries"]
                                             if e["ref_id"] == job["workflow_id"]))
        manifest["artifacts"][0].update(sha256=sha256(FIXTURE_BYTES).hexdigest(),
                                        size_bytes=len(FIXTURE_BYTES))
        self.payload = dict(
            bootstrap=dict(schema_version="0.1.0", protocol_version="0.1.0",
                           worker_id="worker:1", launch_nonce="launch:1",
                           context_registry_path=str(registry)),
            registry_delivery="handle-snapshot", project_id="project:1",
            execution_owner_id="owner:1", owner_epoch=1,
            context_json=context_json, job_json=job_json, snapshot_json=snapshot_json,
            start=start.model_dump(mode="json"),
            managed_roots=[dict(root_id="root:1", absolute_path=str(self.root))],
            external_registrations=[dict(registration_id="registration:1",
                                         absolute_path=str(external_file),
                                         file_identity={"volume_id": identity.volume_id,
                                                        "file_id": identity.file_id})],
            candidate_manifest_id="candidate:1",
            fixture_output=dict(staging_id="staging:1", absolute_path=str(staging),
                                artifact_relative_path="result.bin", manifest=manifest),
            fixture_mode="block", heartbeat_seconds=0.05)

    def launch(self, **overrides):
        payload = dict(self.payload, **overrides)
        process = WorkerTransport.launch(Path(sys.executable), WorkerLaunchPacket.model_validate(payload))
        self.addCleanup(process.shutdown, 0.1, 3)
        response = process.request("capabilities", {"protocol_version": "0.1.0", "schema_version": "0.1.0"}, 3)
        self.assertIn("fixture", response.result["features"])
        return process

    def test_busy_heartbeat_cancel_ack_and_confirmed_stop(self):
        process = self.launch()
        reply = process.request("start", self.payload["start"], 3)
        self.assertTrue(reply.result["accepted"])
        self.assertEqual(process.next_event(2).method, "heartbeat")
        reply = process.request("cancel", {"attempt": self.payload["start"]["attempt"]}, 2)
        self.assertTrue(reply.result["accepted"])
        self.assertFalse(process.group_stopped(0))
        self.assertTrue(process.shutdown(0.2, 3))
        self.assertTrue(process.group_stopped(0))

    def test_fixture_candidate_completion_and_native_logs(self):
        process = self.launch(fixture_mode="log")
        reply = process.request("start", self.payload["start"], 3)
        self.assertTrue(reply.result["accepted"])
        methods = set()
        until = time.monotonic() + 4
        while "completed" not in methods and time.monotonic() < until:
            methods.add(process.next_event(2).method)
        self.assertTrue({"progress", "artifact_candidate", "completed"} <= methods)
        self.assertGreater(process.stderr_bytes_seen, 0)

    def test_start_replay_and_wrong_context_rejected(self):
        process = self.launch()
        bad = dict(self.payload["start"], access_context_sha256="f" * 64)
        rejected = process.request("start", bad, 3)
        self.assertFalse(rejected.result["accepted"])
        self.assertTrue(process.request("start", self.payload["start"], 3).result["accepted"])
        replay = process.request("start", self.payload["start"], 3)
        self.assertFalse(replay.result["accepted"])

    def test_request_timeout_keeps_ambiguous_state_and_shutdown_bounds(self):
        process = self.launch()
        with self.assertRaises(TransportError):
            process.request("start", self.payload["start"], 0)
        self.assertTrue(process.shutdown(0.1, 3))

    def test_stderr_beyond_pipe_capacity_does_not_block_protocol(self):
        process = self.launch(fixture_mode="flood_stderr")
        self.assertTrue(process.request("start", self.payload["start"], 3).result["accepted"])
        until = time.monotonic() + 4
        methods = set()
        while "completed" not in methods and time.monotonic() < until:
            methods.add(process.next_event(2).method)
        self.assertIn("completed", methods)
        self.assertEqual(process.stderr_bytes_seen, 65536)

    def test_malformed_and_truncated_stdout_stop_contained_process(self):
        cases = [
            "import os,time;os.write(1,b'{\\\"jsonrpc\\\":');time.sleep(30)",
            "import os,time;os.write(1,b'x'*1048577);time.sleep(30)",
            "import os,time;os.write(1,b'{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"id\\\":1,\\\"result\\\":NaN}\\n');time.sleep(30)",
        ]
        for code in cases:
            with self.subTest(code=code[:35]):
                native = ManagedProcess.launch(Path(sys.executable), ["-c", code])
                process = WorkerTransport(native)
                self.addCleanup(process.shutdown, 0.1, 3)
                with self.assertRaises(TransportError):
                    process.request("capabilities", {"protocol_version": "0.1.0", "schema_version": "0.1.0"}, 0.3)
                self.assertTrue(process.shutdown(0.1, 3))
                self.assertTrue(process.group_stopped(0))

    def test_stdin_eof_stops_worker(self):
        process = self.launch()
        process.process.stdin.close()
        self.assertTrue(process.process.wait(3))
        with self.assertRaises(TransportError):
            process.request("start", self.payload["start"], 1)

    def test_partial_frame_and_late_response_preserve_correlation(self):
        code = (
            "import json,os,sys,time\n"
            "one=json.loads(sys.stdin.buffer.readline());time.sleep(.2)\n"
            "reply=lambda i:json.dumps({'jsonrpc':'2.0','id':i,'result':{'protocol_version':'0.1.0','schema_version':'0.1.0'}}).encode()+b'\\n'\n"
            "first=reply(one['id']);os.write(1,first[:8]);time.sleep(.02);os.write(1,first[8:])\n"
            "two=json.loads(sys.stdin.buffer.readline());os.write(1,reply(two['id']));time.sleep(.3)\n"
        )
        native = ManagedProcess.launch(Path(sys.executable), ["-c", code])
        process = WorkerTransport(native)
        self.addCleanup(process.shutdown, 0.1, 3)
        params = {"protocol_version": "0.1.0", "schema_version": "0.1.0"}
        with self.assertRaises(TransportError):
            process.request("capabilities", params, .01)
        self.assertEqual(process.request("capabilities", params, 2).result["protocol_version"], "0.1.0")

    def test_response_id_type_mismatch_is_fatal(self):
        code = (
            "import os,time;os.read(0,4096);"
            "os.write(1,b'{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"id\\\":\\\"1\\\",\\\"result\\\":{}}\\n');"
            "time.sleep(30)"
        )
        native = ManagedProcess.launch(Path(sys.executable), ["-c", code])
        process = WorkerTransport(native)
        self.addCleanup(process.shutdown, 0.1, 3)
        with self.assertRaises(TransportError):
            process.request("capabilities", {"protocol_version": "0.1.0",
                                             "schema_version": "0.1.0"}, 2)
        self.assertTrue(process.shutdown(0.1, 3))

    def test_changed_manifest_bytes_are_rejected_before_acceptance(self):
        process = self.launch()
        (self.root / "manifests" / "job-1.json").write_bytes(b"changed")
        reply = process.request("start", self.payload["start"], 3)
        self.assertFalse(reply.result["accepted"])

    def test_registered_external_manifest_uses_exact_file_identity(self):
        external_dir = Path(self.temp.name) / "external"
        external_dir.mkdir(exist_ok=True)
        external_file = external_dir / "snapshot.json"
        external_file.write_bytes(self.payload["snapshot_json"].encode())
        with NativeRoot(external_dir) as root:
            with root.open_read("snapshot.json", sha256=sha256(external_file.read_bytes()).hexdigest(),
                                size_bytes=external_file.stat().st_size) as source:
                identity = source.identity
        context = json.loads(self.payload["context_json"])
        snapshot_entry = next(entry for entry in context["read_entries"]
                              if entry["ref_id"] == context["input_snapshot_id"])
        snapshot_entry["location"] = {
            "kind": "external-registered-local", "registration_id": "registration:external",
            "absolute_path": str(external_file),
            "file_identity": {"volume_id": identity.volume_id, "file_id": identity.file_id}}
        context_json = compact(context)
        start = dict(self.payload["start"], access_context_sha256=sha256(context_json.encode()).hexdigest())
        registration = dict(registration_id="registration:external", absolute_path=str(external_file),
                            file_identity={"volume_id": identity.volume_id, "file_id": identity.file_id})
        process = self.launch(context_json=context_json, start=start,
                              external_registrations=[*self.payload["external_registrations"], registration])
        self.assertTrue(process.request("start", start, 3).result["accepted"])

    def test_mismatched_launch_identity_fails_before_capabilities(self):
        packet = WorkerLaunchPacket.model_validate(dict(self.payload, project_id="project:other"))
        process = WorkerTransport.launch(Path(sys.executable), packet)
        self.addCleanup(process.shutdown, .1, 3)
        with self.assertRaises(TransportError):
            process.request("capabilities", {"protocol_version": "0.1.0",
                                             "schema_version": "0.1.0"}, 3)

    def test_trusted_owner_identity_is_checked_before_spawn(self):
        class OtherOwner:
            owner_id = "owner:other"
            owner_epoch = 1
        with self.assertRaises(TransportError):
            WorkerTransport.launch(Path(sys.executable),
                                   WorkerLaunchPacket.model_validate(self.payload), owner=OtherOwner())

    def test_shutdown_joins_transport_threads(self):
        process = self.launch()
        self.assertTrue(process.shutdown(.1, 3))
        self.assertFalse(process._reader.is_alive())
        self.assertFalse(process._writer_thread.is_alive())

    def test_fatal_frame_joins_transport_threads(self):
        native = ManagedProcess.launch(Path(sys.executable), ["-c",
            "import os,time;os.write(1,b'not-json\\n');time.sleep(30)"])
        process = WorkerTransport(native)
        self.addCleanup(process.shutdown, .1, 3)
        with self.assertRaises(TransportError):
            process.request("capabilities", {"protocol_version": "0.1.0",
                                             "schema_version": "0.1.0"}, 3)
        self.assertTrue(process.shutdown(.1, 3))
        self.assertFalse(process._reader.is_alive())
        self.assertFalse(process._writer_thread.is_alive())

    def test_process_staging_publisher_and_cancel_fencing(self):
        for cancel_before_publish in (False, True):
            with self.subTest(cancel=cancel_before_publish):
                self._run_publication_case(cancel_before_publish)

    def _run_publication_case(self, cancel_before_publish):
        base = Path(self.temp.name)
        staging_path = base / ("staging-cancel" if cancel_before_publish else "staging-publish")
        output_path = base / ("output-cancel" if cancel_before_publish else "output-publish")
        staging_path.mkdir()
        output_path.mkdir()
        core = JobCoordinator(RetryPolicy(2, 0))
        job = JobSpec.model_validate(WORKFLOW["JobSpec"])
        core.enqueue(job)
        attempt = core.claim("project:1", "job:1", owner_id="owner:1", owner_epoch=1)
        context = json.loads(self.payload["context_json"])
        context["attempt"] = attempt.model_dump(mode="json")
        context_json = compact(context)
        start = dict(self.payload["start"], attempt=attempt.model_dump(mode="json"),
                     access_context_sha256=sha256(context_json.encode()).hexdigest())
        manifest = deepcopy(self.payload["fixture_output"]["manifest"])
        manifest["attempt"] = attempt.model_dump(mode="json")
        fixture_output = dict(self.payload["fixture_output"], absolute_path=str(staging_path),
                              manifest=manifest)
        packet = WorkerLaunchPacket.model_validate(dict(self.payload, context_json=context_json,
                                                         start=start, fixture_output=fixture_output,
                                                         fixture_mode="complete"))
        process = WorkerTransport.launch(Path(sys.executable), packet)
        self.addCleanup(process.shutdown, .1, 3)
        process.request("capabilities", {"protocol_version": "0.1.0", "schema_version": "0.1.0"}, 3)
        self.assertTrue(process.request("start", start, 3).result["accepted"])
        methods = set()
        while "completed" not in methods:
            event = process.next_event(3)
            methods.add(event.method)
            if event.method == "artifact_candidate":
                self.assertEqual(event.params.candidate_manifest_id, packet.candidate_manifest_id)
        self.assertIn("artifact_candidate", methods)
        self.assertEqual((staging_path / "result.bin").read_bytes(), FIXTURE_BYTES)
        self.assertTrue(process.shutdown(.2, 3))

        grants = GrantRegistry(worker_id="worker:1", launch_nonce="launch:1",
                               project_id="project:1", execution_owner_id="owner:1", owner_epoch=1)
        grants.register(context_bytes=context_json.encode(), job_bytes=packet.job_json.encode(),
                        snapshot_bytes=packet.snapshot_json.encode(),
                        expected_start=StartParams.model_validate(start))
        grants.accept(StartParams.model_validate(start))
        roots = {"root:1": NativeRoot(self.root)}
        external = {item.registration_id: ExternalRegistration(Path(item.absolute_path),
                     NativeIdentity(
                         item.file_identity.volume_id, item.file_identity.file_id))
                    for item in packet.external_registrations}
        staging_root = NativeRoot(staging_path)
        output_root = NativeRoot(output_path)
        self.addCleanup(grants.close)
        for root in (*roots.values(), staging_root, output_root):
            self.addCleanup(root.close)

        class Guard:
            def assert_held(self, project_id):
                if project_id != "project:1":
                    raise ValueError("wrong project")

        class MetadataRepository:
            project_id = "project:1"
            def __init__(self):
                self.artifacts = ()
            def get(self, job_id):
                return core.get("project:1", job_id)
            def publish(self, job_id, key, publication_id, artifacts):
                result = core.publish("project:1", job_id, key, "owner:1", 1, publication_id)
                self.artifacts = artifacts
                return result

        repository = MetadataRepository()
        publisher = Publisher(repository, grants, WorkerIOResolver(grants, roots, external),
                              {"staging:1": staging_root}, output_root, Guard(),
                              validator=lambda _job, _manifest: True)
        publisher.register_candidate(candidate_id=packet.candidate_manifest_id,
            context_id=context["access_context_id"], project_id=context["project_id"],
            attempt=attempt, staging_id=context["staging_id"],
            manifest_bytes=packet.fixture_output.manifest.model_dump_json().encode(),
            artifact_paths={packet.fixture_output.manifest.artifacts[0].asset_id: "result.bin"})
        if cancel_before_publish:
            core.cancel("project:1", "job:1")
            with self.assertRaises(PublicationError):
                publisher.publish("candidate:1", "access:1", attempt, "publication:cancel")
            self.assertEqual(repository.artifacts, ())
            self.assertTrue((staging_path / "result.bin").exists())
        else:
            result = publisher.publish("candidate:1", "access:1", attempt, "publication:1")
            self.assertEqual(result.state, "succeeded")
            self.assertEqual(len(repository.artifacts), 2)
            self.assertFalse((staging_path / "result.bin").exists())

    def test_capabilities_handshake_and_finite_deadline_required(self):
        packet = WorkerLaunchPacket.model_validate(self.payload)
        with self.assertRaises(ValueError):
            WorkerTransport.launch(Path(sys.executable), packet, bootstrap_timeout=float("nan"))
        process = WorkerTransport.launch(Path(sys.executable), packet)
        self.addCleanup(process.shutdown, .1, 3)
        with self.assertRaises(TransportError):
            process.request("start", self.payload["start"], 1)
        with self.assertRaises(ValueError):
            process.request("capabilities", {"protocol_version": "0.1.0",
                                             "schema_version": "0.1.0"}, float("nan"))
        self.assertTrue(process.request("capabilities", {"protocol_version": "0.1.0",
                                                         "schema_version": "0.1.0"}, 3))
        self.assertTrue(process.request("start", self.payload["start"], 3).result["accepted"])

    def test_nonreading_child_cannot_block_request_deadline_or_shutdown(self):
        native = ManagedProcess.launch(Path(sys.executable), ["-c", "import time;time.sleep(30)"])
        process = WorkerTransport(native)
        self.addCleanup(process.shutdown, .1, 3)
        params = {"protocol_version": "0.1.0", "schema_version": "0.1.0"}
        def timed_request(_):
            try:
                process.request("capabilities", params, .05)
            except TransportError:
                return
            self.fail("nonreading child unexpectedly responded")
        with ThreadPoolExecutor(max_workers=32) as pool:
            list(pool.map(timed_request, range(64)))
        started = time.monotonic()
        self.assertTrue(process.shutdown(.05, 3))
        self.assertLess(time.monotonic() - started, 4)
        self.assertFalse(process._reader.is_alive())
        self.assertFalse(process._writer_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
