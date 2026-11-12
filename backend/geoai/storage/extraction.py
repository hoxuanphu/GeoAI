"""Bounded offline ZIP extraction into an internally supplied staging root."""
from __future__ import annotations

import io
import time
import zipfile

from geoai.storage.importer import ImportRejected, inspect_zip
from geoai.storage.native_io import NativeRoot, StorageIOError, operation_deadline


def extract_zip(source, policy, staging: NativeRoot, *, io_factory, inventory_id, created_at,
                cancelled=lambda: False, monotonic=time.monotonic):
    """Inspect every member before writing; success returns inventory, not an asset.

    The importer service still validates format/content and registers the result
    transactionally. This routine never activates a model or loads native data.
    A failure removes only the exact new files whose bytes we wrote. Empty
    directories may remain in unregistered staging for recovery/cleanup.
    """
    io_factory.require_root(staging, purpose="staging")
    deadline = operation_deadline(policy.max_seconds, monotonic=monotonic)

    def check():
        if cancelled():
            raise ImportRejected("cancelled")
        if monotonic() >= deadline:
            raise ImportRejected("deadline_exceeded")

    inventory = inspect_zip(source, policy, inventory_id=inventory_id, created_at=created_at,
                            cancelled=cancelled, monotonic=monotonic)
    written = []
    try:
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            for info, entry in zip(archive.infolist(), inventory.entries, strict=True):
                check()
                io_factory.require_root(staging, purpose="staging")
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

                    check()
                    size, checksum = staging.create_file(entry.relative_path, blocks(),
                        max_bytes=entry.size_bytes, max_chunk_bytes=policy.chunk_bytes,
                        cancelled=cancelled, deadline=deadline)
                    written.append((entry.relative_path, checksum, size))
                    if (size, checksum) != (entry.size_bytes, entry.sha256):
                        raise ImportRejected("content_mismatch")
        check()
        return inventory
    except BaseException:
        # Cleanup has its own bounded budget: user cancellation must not prevent
        # rollback of exact newly created files. Never reset the copy deadline.
        cleanup_deadline = operation_deadline(60)
        for path, checksum, size in reversed(written):
            try:
                io_factory.require_root(staging, purpose="staging")
                staging.delete_verified(path, sha256=checksum, size_bytes=size,
                    cancelled=lambda: False, deadline=cleanup_deadline)
            except StorageIOError:
                # Preserve unregistered staging for recovery rather than deleting
                # a path whose identity/bytes changed since we created it.
                pass
        raise
