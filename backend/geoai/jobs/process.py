"""Native process contracts use absolute monotonic deadlines, not durations."""
import math
import time
from pathlib import Path
from typing import BinaryIO, Protocol
from geoai.contracts import AttemptKey, WorkerLaunchPacket
from geoai.storage.native_owner import ExecutionOwner


class NativeProcessError(RuntimeError):
    """A child could not be contained or its stop could not be proved."""


class WorkloadStopEvidence(Protocol):
    def assert_stopped(self, project_id: str, attempt: AttemptKey) -> None: ...


class ManagedProcess(Protocol):
    stdin: BinaryIO
    stdout: BinaryIO
    stderr: BinaryIO
    pid: int
    stderr_bytes_seen: int
    def wait(self, deadline: float) -> bool: ...
    def start_stderr_drain(self, max_count: int = 65536) -> None: ...
    def terminate_group(self, deadline: float) -> bool: ...
    def group_stopped(self, deadline: float) -> bool: ...
    def close(self) -> None: ...


class ProcessFactory(Protocol):
    def launch_worker(self, executable: Path, packet: WorkerLaunchPacket, *,
                      owner: ExecutionOwner, deadline: float) -> ManagedProcess: ...
    def stop_evidence(self, process: ManagedProcess, *, project_id: str,
                      attempt: AttemptKey) -> WorkloadStopEvidence: ...


def remaining_seconds(deadline):
    if type(deadline) not in (int,float) or not math.isfinite(deadline):
        raise NativeProcessError('invalid_deadline')
    return min(86400.,max(0.,deadline-time.monotonic()))
