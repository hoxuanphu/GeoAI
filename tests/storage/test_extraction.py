import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone

from geoai.contracts.imports import ArchivePolicy
from geoai.storage.extraction import extract_zip
from geoai.storage.windows_io import NativeRoot, WindowsIOFactory


def zipped(entries):
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as stream:
        for name, content in entries:
            stream.writestr(name, content)
    return target.getvalue()


@unittest.skipUnless(os.name == "nt", "Windows staging handles required")
class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 9, tzinfo=timezone.utc)
        self.policy = ArchivePolicy(policy_id="policy:fixture", created_at=self.now,
            max_archive_bytes=10000, max_entries=8, max_total_bytes=4096,
            max_entry_bytes=2048, max_path_depth=8, max_compression_ratio=100.,
            max_seconds=10., chunk_bytes=64, allowed_extensions=(".txt", ".json"), nested_archives="reject")
        self.temp = tempfile.TemporaryDirectory()
        self.root = NativeRoot(Path(self.temp.name))
        self.io_factory = WindowsIOFactory()
        self.registered = self.io_factory.open_registered_root("staging", Path(self.temp.name), purpose="staging")

    def tearDown(self):
        self.registered.close()
        self.root.close()
        self.temp.cleanup()

    def extract(self, source, **kwargs):
        return extract_zip(source, self.policy, self.registered, io_factory=self.io_factory, inventory_id="inventory:1", created_at=self.now, **kwargs)

    def test_valid_zip_is_hashed_and_written_without_activation(self):
        source = zipped([("folder/", b""), ("empty/", b""), ("folder/first.txt", b"abc"), ("second.json", b"{}")])
        inventory = self.extract(source)
        self.assertEqual(inventory.archive_sha256, hashlib.sha256(source).hexdigest())
        self.assertEqual((Path(self.temp.name) / "folder/first.txt").read_bytes(), b"abc")
        self.assertEqual(inventory.total_bytes, 5)
        self.assertTrue((Path(self.temp.name) / "empty").is_dir())

    def test_conflict_rolls_back_only_new_files(self):
        self.root.create_file("kept.txt", [b"original"], max_bytes=8)
        with self.assertRaises(ValueError):
            self.extract(zipped([("first.txt", b"new"), ("kept.txt", b"bad")]))
        self.assertFalse((Path(self.temp.name) / "first.txt").exists())
        self.assertEqual((Path(self.temp.name) / "kept.txt").read_bytes(), b"original")

    def test_corrupt_and_escape_archives_write_nothing(self):
        for source in (b"corrupt", zipped([("../sentinel.txt", b"bad")]),
                       zipped([("a.txt", b"a" * 3000)])):
            with self.assertRaises(ValueError):
                self.extract(source)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_cancel_after_first_file_rolls_back(self):
        def cancel():
            return (Path(self.temp.name) / "first.txt").exists()
        with self.assertRaises(ValueError):
            self.extract(zipped([("first.txt", b"a"), ("second.txt", b"b")]), cancelled=cancel)
        self.assertFalse((Path(self.temp.name) / "first.txt").exists())
        self.assertFalse((Path(self.temp.name) / "second.txt").exists())
