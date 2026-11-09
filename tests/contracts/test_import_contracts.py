"""Explicit finite fixture policy and persisted inspection metadata."""
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unittest

from pydantic import ValidationError

c = importlib.import_module("geoai.contracts")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/contracts/import-policy.json"


class ImportContractTests(unittest.TestCase):
    def test_explicit_policy_is_versioned_and_fails_closed_for_missing_or_invalid_limits(self):
        self.assertTrue(hasattr(c, "ArchivePolicy"), "archive policy contract missing")
        POLICY = dict(policy_id="archive:fixture-v1", created_at=datetime(2026, 11, 8, tzinfo=timezone.utc),
                      max_archive_bytes=10000, max_entries=8, max_total_bytes=4096,
                      max_entry_bytes=2048, max_path_depth=4, max_compression_ratio=50.0,
                      max_seconds=1.0, chunk_bytes=64, allowed_extensions=(".txt", ".json"),
                      nested_archives="reject")
        policy = c.ArchivePolicy(**POLICY)
        self.assertEqual(policy.policy_id, "archive:fixture-v1")
        for field in ("max_entries", "max_total_bytes", "max_entry_bytes", "max_path_depth", "max_archive_bytes", "max_seconds", "max_compression_ratio", "chunk_bytes", "allowed_extensions", "nested_archives"):
            values = dict(POLICY); del values[field]
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                c.ArchivePolicy(**values)
        for values in ({"max_entries": True}, {"max_seconds": float("inf")}, {"max_entry_bytes": 0},
                       {"allowed_extensions": ()}, {"allowed_extensions": ("*",)}, {"nested_archives": "allow"}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                c.ArchivePolicy(**{**POLICY, **values})

    def test_canonical_inventory_and_policy_fixture_roundtrips(self):
        self.assertTrue(FIXTURE.is_file(), "canonical import policy fixture missing")
        for name, payload in json.loads(FIXTURE.read_text(encoding="utf-8")).items():
            model = c.CONTRACT_MODELS[name]
            value = model.model_validate(payload)
            self.assertEqual(model.model_validate_json(value.model_dump_json()), value)
            self.assertEqual(value.schema_version, "0.1.0")
            self.assertIsNotNone(value.created_at.tzinfo)


if __name__ == "__main__":
    unittest.main()
