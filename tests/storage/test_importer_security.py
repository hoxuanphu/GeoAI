"""Offline subsets of IMP-01/02/03/05/06/09/11; no native acceptance."""
from datetime import datetime, timezone
import hashlib
import importlib
import io
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import zipfile
import zlib

from pydantic import ValidationError

try:
    importer = importlib.import_module("geoai.storage.importer")
except ModuleNotFoundError:
    importer = None

NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)
POLICY = dict(policy_id="archive:fixture-v1", created_at=NOW,
              max_archive_bytes=10000, max_entries=8, max_total_bytes=4096,
              max_entry_bytes=2048, max_path_depth=4, max_compression_ratio=50.0,
              max_seconds=1.0, chunk_bytes=64, allowed_extensions=(".txt", ".json"),
              nested_archives="reject")


def archive(entries, compression=zipfile.ZIP_DEFLATED):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as output:
        for name, data in entries:
            output.writestr(name, data)
    return buffer.getvalue()


def alter_size_and_crc(data, size, crc):
    value = bytearray(data)
    central = value.index(b"PK\x01\x02")
    struct.pack_into("<II", value, 14, crc, struct.unpack_from("<I", value, 18)[0])
    struct.pack_into("<I", value, 22, size)
    struct.pack_into("<I", value, central + 16, crc)
    struct.pack_into("<I", value, central + 24, size)
    return bytes(value)


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importer, "offline archive inspector is missing")
        from geoai.contracts.imports import ArchivePolicy
        self.Policy = ArchivePolicy

    def inspect(self, data, **overrides):
        policy_values = {**POLICY, **overrides.pop("policy", {})}
        return importer.inspect_zip(data, self.Policy(**policy_values),
                                    inventory_id="inventory:fixture", created_at=NOW, **overrides)

    def reject(self, data, code, **kwargs):
        with self.assertRaises(importer.ImportRejected) as caught:
            self.inspect(data, **kwargs)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)
        self.assertIsNone(caught.exception.__cause__)

    def test_inventory_hashes_actual_bytes_without_touching_source_or_sentinel(self):
        source = archive([("folder/", b""), ("folder/readme.txt", b"abc"), ("data.json", b"{}")])
        before = hashlib.sha256(source).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "sentinel.txt"
            sentinel.write_bytes(b"untouched")
            result = self.inspect(source)
            self.assertEqual(sentinel.read_bytes(), b"untouched")
            self.assertEqual(list(Path(directory).iterdir()), [sentinel])
        self.assertEqual(hashlib.sha256(source).hexdigest(), before)
        self.assertEqual(result.archive_sha256, before)
        self.assertEqual(result.total_bytes, 5)
        self.assertEqual(result.entries[1].sha256, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertEqual(result.entries[1].size_bytes, 3)
        self.assertIsInstance(result.entries, tuple)
        self.assertEqual(type(result).model_validate_json(result.model_dump_json()), result)
        with self.assertRaises(ValidationError):
            result.total_bytes = 6

    def test_windows_path_escapes_devices_ads_controls_and_ambiguous_names_rejected(self):
        for name in ("../secret.txt", "..\\secret.txt", "/a.txt", "C:/a.txt", "C:a.txt",
                     "\\\\host\\a.txt", "\\\\?\\C:\\a.txt", "a:ads.txt", "CON.txt", "aux.txt",
                     "COM1.txt", "LPT9.json", "CONIN$.txt", "folder./a.txt", "folder /a.txt",
                     "a\x01.txt", "a//b.txt", "./a.txt", "a/../b.txt", "a. "):
            with self.subTest(name=name):
                self.reject(archive([(name, b"abc")]), "invalid_path")

    def test_nul_name_in_central_directory_is_not_silently_truncated(self):
        source = archive([("x.txt!hidden", b"abc")]).replace(b"x.txt!hidden", b"x.txt\x00hidden")
        self.reject(source, "invalid_path")

    def test_case_unicode_and_implicit_directory_collisions_fail_entire_inventory(self):
        for names in (("a.txt", "A.TXT"), ("caf\u00e9.txt", "cafe\u0301.txt"),
                      ("a.txt", "a.txt/child.txt"), ("A.txt/child.txt", "a.txt"),
                      ("folder/", "Folder/")):
            with self.subTest(names=names):
                self.reject(archive([(name, b"" if name.endswith("/") else b"x") for name in names]), "path_conflict")

    def test_safe_backslash_and_unicode_are_canonical_inventory_names(self):
        result = self.inspect(archive([("folder\\caf\u0065\u0301.txt", b"abc")]))
        self.assertEqual(result.entries[0].relative_path, "folder/caf\u00e9.txt")

    def test_symlinks_special_files_reparse_and_link_extra_metadata_are_rejected(self):
        for mode, attrs, extra in ((stat.S_IFLNK | 0o777, 0, b""), (stat.S_IFIFO | 0o600, 0, b""),
                                  (stat.S_IFREG | 0o600, 0x400, b""),
                                  (stat.S_IFREG | 0o600, 0, struct.pack("<HH", 0x000d, 4) + b"link")):
            item = zipfile.ZipInfo("file.txt")
            item.create_system = 3
            item.external_attr = (mode << 16) | attrs
            item.extra = extra
            self.reject(archive([(item, b"target")]), "unsupported_metadata")

    def test_every_explicit_quota_is_enforced(self):
        source = archive([("a.txt", b"abc"), ("b.txt", b"def")])
        for limits in ({"max_entries": 1}, {"max_archive_bytes": len(source)-1},
                       {"max_entry_bytes": 2}, {"max_total_bytes": 5},
                       {"max_path_depth": 1}):
            candidate = archive([("a/b.txt", b"abc")]) if "max_path_depth" in limits else source
            with self.subTest(limits=limits):
                self.reject(candidate, "resource_exhausted", policy=limits)
        self.reject(archive([("a.txt", b"a" * 1000)]), "resource_exhausted", policy={"max_compression_ratio": 2.0})

    def test_actual_deflate_stream_cannot_hide_bytes_behind_forged_size_and_crc(self):
        source = archive([("a.txt", b"abc" * 100)])
        forged = alter_size_and_crc(source, 3, zlib.crc32(b"abc"))
        self.reject(forged, "invalid_archive")
        self.reject(forged, "resource_exhausted", policy={"max_entry_bytes": 20})

    def test_truncation_crc_corruption_and_malformed_archive_are_sanitized(self):
        source = archive([("a.txt", b"abc")], compression=zipfile.ZIP_STORED)
        corrupt = source.replace(b"abc", b"abd", 1)
        for candidate in (source[:-10], corrupt, b"not zip", alter_size_and_crc(source, 9, zlib.crc32(b"abc"))):
            with self.subTest(candidate=candidate):
                self.reject(candidate, "invalid_archive")

    def test_encrypted_and_unsupported_compression_rejected(self):
        source = bytearray(archive([("a.txt", b"abc")]))
        central = source.index(b"PK\x01\x02")
        struct.pack_into("<H", source, 6, 1)
        struct.pack_into("<H", source, central+8, 1)
        self.reject(bytes(source), "unsupported_archive")
        self.reject(archive([("a.txt", b"abc")], compression=zipfile.ZIP_BZIP2), "unsupported_archive")

    def test_prepended_executable_and_zip64_or_unknown_metadata_are_unsupported(self):
        source = archive([("a.txt", b"abc")])
        self.reject(b"MZstub" + source, "unsupported_archive")
        info = zipfile.ZipInfo("a.txt")
        info.extract_version = 45
        self.reject(archive([(info, b"abc")]), "unsupported_archive")

    def test_data_descriptor_and_multivolume_features_fail_closed(self):
        source = bytearray(archive([("a.txt", b"abc")]))
        central = source.index(b"PK\x01\x02")
        struct.pack_into("<H", source, 6, 8)
        struct.pack_into("<H", source, central+8, 8)
        self.reject(bytes(source), "unsupported_archive")
        source = bytearray(archive([("a.txt", b"abc")]))
        central = source.index(b"PK\x01\x02")
        struct.pack_into("<H", source, central+34, 1)
        self.reject(bytes(source), "unsupported_archive")

    def test_windows_reserved_basename_aliases_are_rejected_after_trimming(self):
        for name in ("CON .txt", "NUL .json", "COM1 .txt", "LPT9 .json", "con... .txt"):
            with self.subTest(name=name):
                self.reject(archive([(name, b"abc")]), "invalid_path")

    def test_concatenated_archives_trailing_data_and_unaccounted_local_bytes_rejected(self):
        source = archive([("a.txt", b"abc")])
        self.reject(archive([("evil.exe", b"MZevil")]) + source, "invalid_archive")
        self.reject(source + b"TRAILING SECRET", "invalid_archive")
        # A member followed by an adjusted central directory cannot hide padding.
        central = source.index(b"PK\x01\x02")
        padded = bytearray(source[:central] + b"HIDDEN" + source[central:])
        eocd = padded.index(b"PK\x05\x06")
        struct.pack_into("<I", padded, eocd+16, central+6)
        self.reject(bytes(padded), "invalid_archive")

    def test_eocd_disk_and_member_counts_are_validated(self):
        source = archive([("a.txt", b"abc")])
        for offset in (4, 6):
            candidate = bytearray(source)
            struct.pack_into("<H", candidate, candidate.index(b"PK\x05\x06")+offset, 1)
            with self.subTest(offset=offset):
                self.reject(bytes(candidate), "unsupported_archive")
        for offset in (8, 10):
            candidate = bytearray(source)
            struct.pack_into("<H", candidate, candidate.index(b"PK\x05\x06")+offset, 0)
            with self.subTest(offset=offset):
                self.reject(bytes(candidate), "invalid_archive")

    def test_valid_archive_comment_and_empty_archive_remain_supported(self):
        source = archive([("a.txt", b"abc")])
        buffer = io.BytesIO(source)
        with zipfile.ZipFile(buffer, "a") as output:
            output.comment = b"fixture comment"
        self.assertEqual(self.inspect(buffer.getvalue()).total_bytes, 3)
        self.assertEqual(self.inspect(archive([])).entries, ())

    def test_local_central_compression_flags_and_trailing_deflate_bytes_must_match(self):
        source = bytearray(archive([("a.txt", b"abc")]))
        struct.pack_into("<H", source, 6, 8)
        self.reject(bytes(source), "invalid_archive")
        source = bytearray(archive([("a.txt", b"abc")]))
        central = source.index(b"PK\x01\x02")
        size = struct.unpack_from("<I", source, central+20)[0]
        # Reclassify the final compressed byte as two: overlap must reject.
        struct.pack_into("<I", source, central+20, size+1)
        self.reject(bytes(source), "invalid_archive")

    def test_nested_archives_vrt_code_and_model_files_stay_disabled_even_if_allowlisted(self):
        for name in ("a.zip", "a.vrt", "a.pkl", "a.exe", "a.py", "a.pt", "a.onnx", "a.dll"):
            with self.subTest(name=name):
                self.reject(archive([(name, b"abc")]), "unsupported_content", policy={"allowed_extensions": ("." + name.split(".")[-1],)})
        for payload in (archive([("inner.txt", b"abc")]), b"MZexecutable", b"\x80\x04pickle", b"<VRTDataset></VRTDataset>"):
            self.reject(archive([("a.txt", payload)]), "unsupported_content")
        self.reject(archive([("a.csv", b"abc")]), "unsupported_content")

    def test_total_deadline_cancel_and_bytes_only_input_fail_closed(self):
        source = archive([("a.txt", b"abc" * 40)])
        self.reject(source, "cancelled", cancelled=lambda: True)
        ticks = iter((0.0, 0.0, 0.2, 0.4, 1.1, 1.2, 1.3))
        self.reject(source, "deadline_exceeded", monotonic=lambda: next(ticks))
        self.reject(io.BytesIO(source), "invalid_source")


if __name__ == "__main__":
    unittest.main()
