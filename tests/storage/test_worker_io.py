import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import test_grant_registry as fixtures
from geoai.storage.io_resolver import WorkerIOResolver, ExternalRegistration
from geoai.storage.windows_io import NativeRoot, StorageIOError, WindowsIOFactory
from geoai.storage.resolver import GrantError


@unittest.skipUnless(os.name == "nt", "Windows I/O handles required")
class WorkerIOTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GrantTests()
        self.fixture.setUp()
        self.managed = tempfile.TemporaryDirectory()
        self.external = tempfile.TemporaryDirectory()
        self.root = NativeRoot(Path(self.managed.name))
        self.external_root = NativeRoot(Path(self.external.name))
        self.external_root.create_file("input.bin", [b"outside"], max_bytes=7)
        checksum = hashlib.sha256(b"outside").hexdigest()
        with self.external_root.open_read("input.bin", sha256=checksum, size_bytes=7) as handle:
            self.identity = handle.identity
        entry = self.fixture.context['read_entries'][2]
        entry['sha256'], entry['size_bytes'] = checksum, 7
        entry['location'].update(absolute_path=str(Path(self.external.name) / "input.bin"),
            file_identity={"volume_id": self.identity.volume_id, "file_id": self.identity.file_id})
        self.fixture.refresh()
        for entry, content in zip(self.fixture.context['read_entries'][:2], (self.fixture.jb, self.fixture.sb)):
            self.root.create_file(entry['location']['relative_path'], [content], max_bytes=len(content))
        self.fixture.register()
        self.fixture.registry.accept(self.fixture.start)
        self.io_factory = WindowsIOFactory()
        self.read_root = self.io_factory.open_registered_root("root:1", Path(self.managed.name), purpose="read")
        self.resolver = WorkerIOResolver(self.fixture.registry, {"root:1": self.read_root}, {
            "registration:1": ExternalRegistration(Path(self.external.name) / "input.bin", self.identity)}, io_factory=self.io_factory)

    def tearDown(self):
        self.read_root.close()
        self.root.close()
        self.external_root.close()
        self.managed.cleanup()
        self.external.cleanup()

    def read(self, ref):
        return self.resolver.open_read("access:1", self.fixture.start.attempt, ref)

    def test_managed_and_registered_external_files_are_readable(self):
        with self.read("job:1") as source:
            self.assertEqual(source.read(), self.fixture.jb)
        with self.read("local:input:1") as source:
            self.assertEqual(source.read(), b"outside")

    def test_unknown_ref_revoked_grant_and_changed_external_are_rejected(self):
        with self.assertRaises(GrantError):
            self.read("not:allowed")
        (Path(self.external.name) / "input.bin").write_bytes(b"changed")
        with self.assertRaises(StorageIOError):
            self.read("local:input:1")
        self.fixture.registry.revoke("access:1")
        with self.assertRaises(GrantError):
            self.read("job:1")

    def test_registration_permission_is_independent_of_context_path(self):
        denied = WorkerIOResolver(self.fixture.registry, {"root:1": self.read_root}, {}, io_factory=self.io_factory)
        with self.assertRaises(StorageIOError):
            denied.open_read("access:1", self.fixture.start.attempt, "local:input:1")
