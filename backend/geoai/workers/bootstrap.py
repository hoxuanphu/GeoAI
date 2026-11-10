"""Read one trusted inherited-handle launch snapshot before other runtime imports."""
import os
from pathlib import Path

from geoai.contracts import WorkerLaunchPacket
from geoai.jobs.protocol import JsonLines, ProtocolError


def read_launch_packet(handle: int) -> WorkerLaunchPacket:
    if os.name != "nt" or type(handle) is not int or handle <= 0:
        raise ValueError("trusted_launch_handle_required")
    import msvcrt
    fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    reader = JsonLines()
    values = []
    try:
        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            values.extend(reader.feed(chunk))
        reader.finish()
    finally:
        os.close(fd)
    if len(values) != 1:
        raise ProtocolError("one private launch packet required")
    packet = WorkerLaunchPacket.model_validate(values[0])
    registry = Path(packet.bootstrap.context_registry_path)
    if not registry.is_absolute() or not registry.is_dir():
        raise ValueError("trusted_registry_directory_required")
    return packet
