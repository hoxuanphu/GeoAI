"""Private bounded JSON-RPC transport over an injected native process."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import threading
import time
import math

from geoai.contracts import RpcNotification, RpcRequest, RpcSuccess, RpcFailure, WorkerLaunchPacket
from geoai.jobs.process import ProcessFactory
from geoai.jobs.protocol import JsonLines, ProtocolError, classify, correlate_response, encode


class TransportError(RuntimeError):
    """Sanitized transport failure; a timeout leaves start acceptance unknown."""


class WorkerTransport:
    def __init__(self, process, *, expected_attempt=None, candidate_id=None):
        self.process = process
        self._expected_attempt = expected_attempt
        self._candidate_id = candidate_id
        self._writer = threading.Lock()
        self._outgoing = queue.Queue(maxsize=64)
        self._state = threading.Lock()
        self._pending = {}
        self._expired = set()
        self._events = queue.Queue(maxsize=256)
        self._next_id = 0
        self._failure = None
        self._closing = False
        self._stopped = False
        self._negotiated = False
        process.start_stderr_drain(max_count=65536)
        self._writer_thread = threading.Thread(target=self._write_stdin, daemon=True)
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._writer_thread.start()
        self._reader.start()

    @classmethod
    def launch(cls, executable: Path, packet: WorkerLaunchPacket, *, process_factory: ProcessFactory,
               owner, bootstrap_timeout=10):
        if (type(bootstrap_timeout) not in (int,float) or not math.isfinite(bootstrap_timeout)
                or not 0 < bootstrap_timeout <= 60):
            raise ValueError("invalid_bootstrap_timeout")
        deadline = time.monotonic() + bootstrap_timeout
        if not isinstance(packet, WorkerLaunchPacket):
            raise TypeError("validated_launch_packet_required")
        if owner is not None and (owner.owner_id, owner.owner_epoch) != (
                packet.execution_owner_id, packet.owner_epoch):
            raise TransportError("launch_owner_mismatch")
        if time.monotonic() >= deadline:
            raise TransportError("bootstrap_timeout")
        process = process_factory.launch_worker(Path(executable), packet, owner=owner, deadline=deadline)
        try:
            result = cls(process, expected_attempt=packet.start.attempt,
                         candidate_id=packet.candidate_manifest_id)
            result._process_factory = process_factory
            return result
        except BaseException:
            if not process.terminate_group(time.monotonic()+5):
                raise TransportError("bootstrap_cleanup_unproved") from None
            raise

    @property
    def stderr_bytes_seen(self):
        return self.process.stderr_bytes_seen

    def _fail(self, reason):
        with self._state:
            self._failure = reason
            for pending in self._pending.values():
                pending.put_nowait(None)
            self._pending.clear()
        try:
            if self.process.terminate_group(time.monotonic()+5):
                self._stopped = True
        except Exception:
            pass
        self._stop_threads()

    def _stop_threads(self):
        while True:
            try:
                self._outgoing.put_nowait(None)
                break
            except queue.Full:
                try:
                    self._outgoing.get_nowait()
                except queue.Empty:
                    pass
        current = threading.current_thread()
        for thread in (self._writer_thread, self._reader):
            if thread is not current and thread.ident is not None:
                thread.join(timeout=1)

    def _write_stdin(self):
        while True:
            frame = self._outgoing.get()
            if frame is None:
                return
            try:
                with self._writer:
                    self.process.stdin.write(frame)
                    self.process.stdin.flush()
            except (OSError, ValueError):
                self._fail("worker_stdin_closed")
                return

    def _read_stdout(self):
        reader = JsonLines()
        try:
            while True:
                chunk = os.read(self.process.stdout.fileno(), 4096)
                if not chunk:
                    reader.finish()
                    if not self._closing:
                        raise ProtocolError("worker_stdout_closed")
                    return
                for value in reader.feed(chunk):
                    message = classify(value)
                    if isinstance(message, RpcNotification):
                        if (self._expected_attempt is not None and
                                message.params.attempt != self._expected_attempt):
                            raise ProtocolError("event_attempt_mismatch")
                        if (self._candidate_id is not None and
                                message.method in ("artifact_candidate", "completed") and
                                message.params.candidate_manifest_id != self._candidate_id):
                            raise ProtocolError("event_candidate_mismatch")
                        try:
                            self._events.put_nowait(message)
                        except queue.Full:
                            raise ProtocolError("event_buffer_full") from None
                    elif isinstance(message, (RpcSuccess, RpcFailure)):
                        with self._state:
                            ident = message.id
                            if ident in self._expired and type(ident) is int:
                                self._expired.remove(ident)
                                continue
                            pending = self._pending.pop(ident, None) if type(ident) is int else None
                        if pending is None:
                            raise ProtocolError("uncorrelated_response")
                        pending.put_nowait(correlate_response(message, ident))
                    else:
                        raise ProtocolError("unexpected_worker_request")
        except (OSError, ProtocolError, ValueError):
            self._fail("protocol_or_pipe_failure")

    def request(self, method, params, timeout: float):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0 or timeout > 86400:
            raise ValueError("invalid_timeout")
        end = time.monotonic() + timeout
        with self._state:
            if self._closing or self._failure:
                raise TransportError(self._failure or "transport_closing")
            if method == "start" and not self._negotiated:
                raise TransportError("capabilities_required")
            if len(self._pending) >= 64:
                raise TransportError("pending_request_limit")
            self._next_id += 1
            ident = self._next_id
            pending = queue.Queue(maxsize=1)
            self._pending[ident] = pending
        try:
            frame = encode(RpcRequest(jsonrpc="2.0", id=ident, method=method, params=params))
            self._outgoing.put_nowait(frame)
        except Exception:
            with self._state:
                self._pending.pop(ident, None)
            raise TransportError("invalid_or_full_request") from None
        try:
            response = pending.get(timeout=max(0, end - time.monotonic()))
        except queue.Empty:
            with self._state:
                if self._pending.pop(ident, None) is not None:
                    if len(self._expired) >= 256:
                        self._failure = "expired_request_limit"
                    else:
                        self._expired.add(ident)
            raise TransportError("request_timeout_acceptance_unknown") from None
        if response is None:
            raise TransportError(self._failure or "transport_failed")
        if method == "capabilities" and isinstance(response, RpcSuccess):
            result = response.result
            if (not isinstance(result, dict) or result.get("protocol_version") != "0.1.0"
                    or result.get("schema_version") != "0.1.0"):
                self._fail("capabilities_mismatch")
                raise TransportError("capabilities_mismatch")
            self._negotiated = True
        return response

    def next_event(self, timeout: float):
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            raise TransportError(self._failure or "event_timeout") from None

    def group_stopped(self, timeout=0):
        return self._stopped or self.process.group_stopped(time.monotonic()+timeout)

    def shutdown(self, grace_seconds=1, terminate_seconds=5):
        if self._stopped:
            self._stop_threads()
            return True
        for value in (grace_seconds, terminate_seconds):
            if type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value <= 86400:
                raise ValueError("invalid_shutdown_budget")
        grace_deadline = time.monotonic()+grace_seconds
        termination_deadline = grace_deadline+terminate_seconds
        with self._state:
            already_closing = self._closing
        if not already_closing and not self._failure:
            try:
                self.request("shutdown", {"graceful": True}, max(0.,grace_deadline-time.monotonic()))
            except TransportError:
                pass
        with self._state:
            self._closing = True
        if self.process.group_stopped(grace_deadline):
            self.process.close()
            self._stopped = True
            self._stop_threads()
            return True
        if self.process.terminate_group(termination_deadline):
            self._stopped = True
            self._stop_threads()
            return True
        return False
