"""Real Windows handle tests using private temporary fixture directories."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
import subprocess

from geoai.storage.windows_io import NativeRoot, StorageIOError


@unittest.skipUnless(os.name == "nt", "Windows handle adapter required")
class WindowsIOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="GeoAI-địa-hình-")
        self.root = Path(self.temp.name)
        self.scope = NativeRoot(self.root)

    def tearDown(self):
        self.scope.close()
        self.temp.cleanup()

    def test_create_and_verify_read_without_write_or_delete_sharing(self):
        content = b"small synthetic raster bytes"
        digest = hashlib.sha256(content).hexdigest()
        self.scope.create_file("nested/input.bin", [content], max_bytes=128)
        with self.scope.open_read("nested/input.bin", sha256=digest, size_bytes=len(content)) as source:
            self.assertEqual(source.read(), content)
            self.assertTrue(source.identity.file_id)
            with self.assertRaises(OSError):
                (self.root / "nested" / "input.bin").write_bytes(b"changed")
            with self.assertRaises(OSError):
                (self.root / "nested").rename(self.root / "swapped")
        self.assertEqual((self.root / "nested/input.bin").read_bytes(), content)

    def test_invalid_paths_and_hardlink_preserve_external_sentinel(self):
        sentinel = self.root.parent / (self.root.name + "-sentinel")
        sentinel.write_bytes(b"outside")
        self.addCleanup(sentinel.unlink)
        for path in ("../escape", "C:/escape", "x:stream", "CON", "file. ", "x/../y", "\\\\host\\share"):
            with self.subTest(path=path), self.assertRaises(StorageIOError):
                self.scope.create_file(path, [b"x"], max_bytes=1)
        os.link(sentinel, self.root / "linked.bin")
        with self.assertRaises(StorageIOError):
            self.scope.open_read("linked.bin", sha256=hashlib.sha256(b"outside").hexdigest(), size_bytes=7)
        self.assertEqual(sentinel.read_bytes(), b"outside")

    def test_quota_cancel_no_overwrite_hash_and_closed_scope(self):
        with self.assertRaises(StorageIOError):
            self.scope.create_file("partial.bin", [b"too large"], max_bytes=2)
        self.assertFalse((self.root / "partial.bin").exists())
        with self.assertRaises(StorageIOError):
            self.scope.create_file("cancel.bin", [b"x"], max_bytes=2, cancelled=lambda: True)
        self.assertFalse((self.root / "cancel.bin").exists())
        self.scope.create_file("kept.bin", [b"old"], max_bytes=3)
        with self.assertRaises(StorageIOError):
            self.scope.create_file("kept.bin", [b"new"], max_bytes=3)
        with self.assertRaises(StorageIOError):
            self.scope.open_read("kept.bin", sha256="0" * 64, size_bytes=3)
        self.assertEqual((self.root / "kept.bin").read_bytes(), b"old")
        self.scope.close()
        with self.assertRaises(StorageIOError):
            self.scope.open_read("kept.bin", sha256=hashlib.sha256(b"old").hexdigest(), size_bytes=3)

    def test_external_identity_and_reparse_root(self):
        self.scope.create_file("valid.bin", [b"data"], max_bytes=4)
        with self.scope.open_read("valid.bin", sha256=hashlib.sha256(b"data").hexdigest(), size_bytes=4) as source:
            identity = source.identity
        with self.assertRaises(StorageIOError):
            self.scope.open_read("valid.bin", sha256=hashlib.sha256(b"data").hexdigest(), size_bytes=4,
                                 expected_identity=("wrong", "wrong"))
        with self.scope.open_read("valid.bin", sha256=hashlib.sha256(b"data").hexdigest(), size_bytes=4,
                                  expected_identity=(identity.volume_id, identity.file_id)) as source:
            self.assertEqual(source.read(), b"data")

    def test_junction_root_and_ancestor_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="GeoAI-external-") as outside:
            target = Path(outside)
            (target / "sentinel.bin").write_bytes(b"safe")
            junction = self.root / "junction"
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(target)],
                                    capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, "fixture junction could not be created")
            try:
                with self.assertRaises(StorageIOError):
                    NativeRoot(junction)
                with self.assertRaises(StorageIOError):
                    self.scope.create_file("junction/sentinel.bin", [b"changed"], max_bytes=10)
                self.assertEqual((target / "sentinel.bin").read_bytes(), b"safe")
            finally:
                junction.rmdir()  # Remove only this test's junction, never its target.

    def test_reader_holds_root_lifetime_and_same_size_mutation_is_rejected(self):
        self.scope.create_file("identity.bin", [b"old"], max_bytes=3)
        digest = hashlib.sha256(b"old").hexdigest()
        with self.scope.open_read("identity.bin", sha256=digest, size_bytes=3):
            with self.assertRaises(StorageIOError):
                self.scope.close()
        (self.root / "identity.bin").write_bytes(b"new")
        with self.assertRaises(StorageIOError):
            self.scope.open_read("identity.bin", sha256=digest, size_bytes=3)

    def test_verified_move_is_atomic_no_overwrite_and_delete_checks_bytes(self):
        with tempfile.TemporaryDirectory(prefix="GeoAI-published-") as output:
            with NativeRoot(Path(output)) as published:
                digest = hashlib.sha256(b"payload").hexdigest()
                self.scope.create_file("candidate.bin", [b"payload"], max_bytes=7)
                published.create_file("kept.bin", [b"old"], max_bytes=3)
                with self.assertRaises(StorageIOError):
                    self.scope.move_verified("candidate.bin", published, "kept.bin", sha256=digest, size_bytes=7)
                self.assertTrue((self.root / "candidate.bin").exists())
                self.scope.move_verified("candidate.bin", published, "run/result.bin", sha256=digest, size_bytes=7)
                self.assertFalse((self.root / "candidate.bin").exists())
                with published.open_read("run/result.bin", sha256=digest, size_bytes=7) as source:
                    self.assertEqual(source.read(), b"payload")
                with self.assertRaises(StorageIOError):
                    published.delete_verified("run/result.bin", sha256="0" * 64, size_bytes=7)
                self.assertTrue((Path(output) / "run/result.bin").exists())
                published.delete_verified("run/result.bin", sha256=digest, size_bytes=7)
                self.assertFalse((Path(output) / "run/result.bin").exists())

