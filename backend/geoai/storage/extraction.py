"""Bounded offline ZIP extraction into an internally supplied staging root."""
from __future__ import annotations

import io
import time
import zipfile

from geoai.storage.importer import ImportRejected, inspect_zip
from geoai.storage.windows_io import NativeRoot, StorageIOError


def extract_zip(source, policy, staging: NativeRoot, *, inventory_id, created_at,
                cancelled=lambda: False, monotonic=time.monotonic):
    """Inspect every member before writing; success returns inventory, not an asset.

    The importer service still validates format/content and registers the result
    transactionally. This routine never activates a model or loads native data.
    A failure removes only the exact new files whose bytes we wrote. Empty
    directories may remain in unregistered staging for recovery/cleanup.
    """
    if not isinstance(staging, NativeRoot):
        raise StorageIOError("trusted_staging_required")
    began = monotonic()

    def check():
        if cancelled():
            raise ImportRejected("cancelled")
        if monotonic() - began >= policy.max_seconds:
            raise ImportRejected("deadline_exceeded")

    inventory = inspect_zip(source, policy, inventory_id=inventory_id, created_at=created_at,
                            cancelled=cancelled, monotonic=monotonic)
    written = []
    try:
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            for info, entry in zip(archive.infolist(), inventory.entries, strict=True):
                check()
                if entry.kind == "directory":
                    staging.ensure_directory(entry.relative_path)
                    continue
                with archive.open(info) as stream:
                    def blocks():
                        while True:
                            check()
                            block = stream.read(policy.chunk_bytes)
                            if not block:
                                return
                            yield block

                    remaining = policy.max_seconds - (monotonic() - began)
                    if remaining <= 0:
                        raise ImportRejected("deadline_exceeded")
                    size, checksum = staging.create_file(entry.relative_path, blocks(),
                        max_bytes=entry.size_bytes, max_chunk_bytes=policy.chunk_bytes,
                        cancelled=cancelled, deadline_seconds=remaining)
                    written.append((entry.relative_path, checksum, size))
                    if (size, checksum) != (entry.size_bytes, entry.sha256):
                        raise ImportRejected("content_mismatch")
        check()
        return inventory
    except BaseException:
        for path, checksum, size in reversed(written):
            try:
                staging.delete_verified(path, sha256=checksum, size_bytes=size)
            except StorageIOError:
                # Preserve unregistered staging for recovery rather than deleting
                # a path whose identity/bytes changed since we created it.
                pass
        raise
