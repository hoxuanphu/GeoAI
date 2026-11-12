"""Portable evidence records execution without promoting it to native acceptance."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import ubuntu_foundation_check as runner
from ubuntu_foundation_preflight import prepare_output, write_json_once


class FoundationRunnerTests(unittest.TestCase):
    def test_classifies_actual_counts_and_exit(self):
        self.assertEqual(runner.classify(0, {'testsRun': 4, 'skipped': 4}), 'skip')
        self.assertEqual(runner.classify(0, {'testsRun': 0, 'skipped': 0}), 'fail')
        self.assertEqual(runner.classify(1, {'testsRun': 4, 'skipped': 0}), 'fail')
        self.assertEqual(runner.classify(None), 'not_run')
        self.assertEqual(runner.classify(0, {'testsRun': 4, 'skipped': 1}), 'pass')
        self.assertEqual(runner.classify(0, {'testsRun': 4, 'skipped': 0, 'unexpectedSuccesses': 1}), 'fail')

    def test_counts_come_from_unittest_result(self):
        @unittest.skip('fixture unavailable')
        class Skipped(unittest.TestCase):
            def test_fixture(self):
                self.fail('must skip')
        result = runner.run_suite(unittest.defaultTestLoader.loadTestsFromTestCase(Skipped))
        self.assertEqual(result['counts']['testsRun'], 1)
        self.assertEqual(result['counts']['skipped'], 1)
        self.assertEqual(result['status'], 'skip')
        self.assertEqual(runner.run_suite(unittest.TestSuite())['status'], 'fail')

    def test_command_output_never_persists_env_argv_or_secrets(self):
        secret = 'synthetic_only_' + 'z' * 30
        raw = json.dumps({'ENV': {'API_KEY': secret}, 'ARGV': ['--credential', secret]})
        with patch.object(runner.subprocess, 'run', return_value=SimpleNamespace(
                returncode=1, stdout=raw, stderr='Bearer ' + secret)):
            report = runner.run_command('schemas', [sys.executable, 'unused'])
        encoded = json.dumps(report)
        self.assertNotIn(secret, encoded)
        self.assertNotIn('ENV', encoded)
        self.assertNotIn('ARGV', encoded)
        self.assertEqual(report['status'], 'fail')

    def test_suite_summary_omits_extra_untrusted_fields(self):
        secret = 'synthetic-only-value'
        counts = dict(testsRun=1, skipped=0, failures=0, errors=0,
                      expectedFailures=0, unexpectedSuccesses=0, ENV=secret)
        raw = json.dumps({'counts': counts, 'ARGV': [secret]})
        with patch.object(runner.subprocess, 'run', return_value=SimpleNamespace(
                returncode=0, stdout=raw, stderr=secret)):
            report = runner.run_command('contracts', [sys.executable, 'unused'], suite=True)
        self.assertEqual(report['status'], 'pass')
        self.assertNotIn(secret, json.dumps(report))

    def test_full_node_version(self):
        import ubuntu_foundation_preflight as preflight
        with patch.object(preflight, '_command', return_value='v22.22.1'):
            self.assertEqual(preflight._version(['node', '--version']), '22.22.1')
    def test_degraded_manager_state(self):
        import ubuntu_foundation_preflight as preflight
        with patch.object(preflight.subprocess, 'run', return_value=SimpleNamespace(
                returncode=1, stdout='degraded\n')):
            self.assertEqual(preflight._command(['systemctl', '--user', 'is-system-running'],
                                                 accepted_codes=(0, 1)), 'degraded')

    def test_output_cannot_overwrite_history_or_existing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'fresh'
            prepare_output(target)
            write_json_once(target / 'env.json', {'safe': True})
            prepare_output(target)
            with self.assertRaises(FileExistsError):
                write_json_once(target / 'env.json', {})
            historical = Path(tmp) / 'history'
            historical.mkdir()
            (historical / 'report.md').write_text('original')
            with self.assertRaises(ValueError):
                prepare_output(historical)
            linked = Path(tmp) / 'link'
            linked.symlink_to(target, target_is_directory=True)
            with self.assertRaises(ValueError):
                prepare_output(linked)

    def test_unknown_layer_is_input_error_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'not-created'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/ubuntu_foundation_check.py'),
                                     '--layer', 'desktop', '--output', str(target)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())
