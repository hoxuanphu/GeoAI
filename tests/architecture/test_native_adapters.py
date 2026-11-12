"""Shared services must import in a fresh interpreter without Win32 adapters."""
import json
import subprocess
import sys
import unittest


class NativeAdapterImportTests(unittest.TestCase):
    def test_shared_imports_do_not_load_windows_adapters(self):
        code = '''
import importlib, json, sys
for name in ('geoai.storage.io_resolver', 'geoai.storage.extraction', 'geoai.storage.gc', 'geoai.jobs.publisher'):
    importlib.import_module(name)
print(json.dumps(sorted(name for name in sys.modules if name in
    ('geoai.storage.windows_io', 'geoai.storage.windows_owner', 'geoai.jobs.native_process'))))
'''
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])
