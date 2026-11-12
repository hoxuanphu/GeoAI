"""Contained fixture worker. The launch handle is the only private input."""
import os
import sys

# Running this trusted file directly works with the native launcher's fixed cwd.
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))


def _protocol_output():
    sys.stdout.flush()
    protocol_fd = os.dup(1)
    os.dup2(2, 1)
    if os.name == "nt":
        import ctypes
        import msvcrt
        msvcrt.setmode(protocol_fd, os.O_BINARY)
        msvcrt.setmode(0, os.O_BINARY)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.SetStdHandle.argtypes = [ctypes.c_ulong, ctypes.c_void_p]
        kernel.SetStdHandle.restype = ctypes.c_int
        if not kernel.SetStdHandle(0xFFFFFFF5, msvcrt.get_osfhandle(2)):
            raise OSError("stdout_redirection_failed")
    sys.stdout = os.fdopen(1, "w", encoding="utf-8", errors="replace", closefd=False)
    return os.fdopen(protocol_fd, "wb", buffering=0)


def run(handle):
    output = _protocol_output()
    from hashlib import sha256
    from pathlib import Path
    import threading
    import time
    from geoai.contracts import WorkerAccessContext, RpcNotification, RpcSuccess
    from geoai.contracts.access import FIXTURE_ARTIFACT_BYTES
    from geoai.jobs.protocol import JsonLines, ProtocolError, classify, encode, failure
    from geoai.storage.resolver import GrantRegistry, GrantError
    from geoai.storage.io_resolver import WorkerIOResolver, ExternalRegistration
    from geoai.storage.windows_io import NativeRoot, NativeIdentity, StorageIOError, WindowsIOFactory
    from geoai.workers.bootstrap import read_launch_packet

    packet = read_launch_packet(handle)
    bootstrap = packet.bootstrap
    context_bytes = packet.context_json.encode("utf-8")
    job_bytes = packet.job_json.encode("utf-8")
    snapshot_bytes = packet.snapshot_json.encode("utf-8")
    context = WorkerAccessContext.model_validate_json(context_bytes)
    if (bootstrap.worker_id, bootstrap.launch_nonce, packet.project_id,
            packet.execution_owner_id, packet.owner_epoch) != (
            context.worker_id, context.launch_nonce, context.project_id,
            context.execution_owner_id, context.owner_epoch):
        raise ValueError("launch_identity_mismatch")
    registry = GrantRegistry(worker_id=bootstrap.worker_id, launch_nonce=bootstrap.launch_nonce,
                             project_id=packet.project_id, execution_owner_id=packet.execution_owner_id,
                             owner_epoch=packet.owner_epoch)
    registry.register(context_bytes=context_bytes, job_bytes=job_bytes,
                      snapshot_bytes=snapshot_bytes, expected_start=packet.start)
    io_factory = WindowsIOFactory()
    roots = {}
    staging_root = None
    try:
        for item in packet.managed_roots:
            roots[item.root_id] = io_factory.open_registered_root(item.root_id, Path(item.absolute_path), purpose="read")
        if packet.fixture_output is not None:
            if packet.fixture_output.staging_id != context.staging_id:
                raise ValueError("fixture_staging_mismatch")
            staging_root = NativeRoot(Path(packet.fixture_output.absolute_path))
        external = {item.registration_id: ExternalRegistration(
            Path(item.absolute_path), NativeIdentity(item.file_identity.volume_id,
                                                     item.file_identity.file_id))
                    for item in packet.external_registrations}
        resolver = WorkerIOResolver(registry, roots, external, io_factory=io_factory)
        writer_lock = threading.Lock()
        cancelled = threading.Event()
        done = threading.Event()
        active = False
        closing = False
        negotiated = False

        def send(value):
            with writer_lock:
                output.write(encode(value))
                output.flush()

        def event(method, params):
            send(RpcNotification(jsonrpc="2.0", method=method, params=params))

        def handler():
            attempt = packet.start.attempt
            try:
                if packet.fixture_mode == "flood_stderr":
                    os.write(2, b"diagnostic " * 30000)
                if packet.fixture_mode == "log":
                    os.write(1, b"native stdout diagnostic\n")
                if packet.fixture_mode == "block":
                    cancelled.wait(30)
                    if cancelled.is_set():
                        event("error", {"attempt": attempt, "error": {
                            "code": "cancelled", "message": "Fixture cancelled", "retryable": False}})
                        return
                if packet.fixture_output is None:
                    event("error", {"attempt": attempt, "error": {
                        "code": "missing_resource", "message": "Fixture output unavailable",
                        "retryable": False}})
                    return
                staging_root.create_file(packet.fixture_output.artifact_relative_path,
                    [FIXTURE_ARTIFACT_BYTES], max_bytes=len(FIXTURE_ARTIFACT_BYTES),
                    cancelled=cancelled.is_set, deadline_seconds=5)
                event("progress", {"attempt": attempt, "phase": "fixture", "completed_units": 1,
                                   "total_units": 1})
                event("artifact_candidate", {"attempt": attempt,
                                             "candidate_manifest_id": packet.candidate_manifest_id})
                event("completed", {"attempt": attempt,
                                     "candidate_manifest_id": packet.candidate_manifest_id})
            except StorageIOError:
                event("error", {"attempt": attempt, "error": {
                    "code": "invalid_input", "message": "Fixture staging failed",
                    "retryable": False}})
            finally:
                done.set()

        def heartbeat():
            while not done.wait(packet.heartbeat_seconds):
                event("heartbeat", {"attempt": packet.start.attempt})

        reader = JsonLines()
        while True:
            chunk = os.read(0, 4096)
            if not chunk:
                reader.finish()
                return
            for value in reader.feed(chunk):
                message = classify(value)
                if not hasattr(message, "method") or not hasattr(message, "id"):
                    if hasattr(message, "error"):
                        send(message)
                        continue
                    raise ProtocolError("worker received non-request")
                if message.method == "capabilities":
                    negotiated = True
                    result = {"app": "GeoAI", "worker": "fixture", "runtime": "python",
                              "features": ["fixture"], "cancel": True, "resume": False,
                              "protocol_version": "0.1.0", "schema_version": "0.1.0"}
                elif message.method == "start":
                    accepted = False
                    if negotiated and not active and not closing:
                        grant_accepted = False
                        try:
                            registry.accept(message.params)
                            grant_accepted = True
                            start_deadline = time.monotonic() + 30
                            manifests = {context.job_spec_id: job_bytes,
                                         context.input_snapshot_id: snapshot_bytes}
                            for entry in context.read_entries:
                                remaining = start_deadline - time.monotonic()
                                if remaining <= 0:
                                    raise StorageIOError("cancelled_or_deadline")
                                with resolver.open_read(context.access_context_id, context.attempt,
                                                        entry.ref_id, deadline_seconds=remaining) as source:
                                    expected = manifests.get(entry.ref_id)
                                    if expected is not None and source.read() != expected:
                                        raise StorageIOError("content_mismatch")
                            registry.register_candidate(packet.candidate_manifest_id,
                                context.access_context_id, project_id=context.project_id,
                                attempt=context.attempt, staging_id=context.staging_id)
                            accepted = True
                        except (GrantError, StorageIOError):
                            if grant_accepted:
                                registry.revoke(context.access_context_id)
                    result = {"accepted": accepted}
                    if accepted:
                        active = True
                        send(RpcSuccess(jsonrpc="2.0", id=message.id, result=result))
                        threading.Thread(target=heartbeat, daemon=True).start()
                        threading.Thread(target=handler, daemon=True).start()
                        continue
                elif message.method == "cancel":
                    accepted = active and message.params.attempt == context.attempt
                    if accepted:
                        cancelled.set()
                    result = {"accepted": accepted}
                elif message.method == "shutdown":
                    closing = True
                    cancelled.set()
                    send(RpcSuccess(jsonrpc="2.0", id=message.id, result={"accepted": True}))
                    done.wait(1 if message.params.graceful else 0)
                    return
                send(RpcSuccess(jsonrpc="2.0", id=message.id, result=result))
    finally:
        registry.close()
        for root in roots.values():
            root.close()
        if staging_root is not None:
            staging_root.close()
        output.close()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("launch_handle_required")
        run(int(sys.argv[1]))
    except BaseException:
        raise SystemExit(1)
