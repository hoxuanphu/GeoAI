#!/usr/bin/env python3
"""Run portable checks and record counts; native acceptance is never inferred."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from ubuntu_foundation_preflight import ROOT, prepare_output, probe_environment, write_json_once

SUITES = ('contracts', 'integration', 'architecture', 'catalog', 'storage', 'jobs')


def classify(exit_code: int | None, counts: dict | None = None) -> str:
    if exit_code is None:
        return 'not_run'
    if exit_code != 0:
        return 'fail'
    if counts is not None:
        total, skipped = counts.get('testsRun', 0), counts.get('skipped', 0)
        if total <= 0 or skipped < 0 or skipped > total or any(counts.get(k, 0) for k in
                ('failures', 'errors', 'unexpectedSuccesses', 'expectedFailures')):
            return 'fail'
        if total == skipped:
            return 'skip'
    return 'pass'


def run_suite(suite: unittest.TestSuite) -> dict:
    log = io.StringIO()
    with redirect_stdout(log), redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    counts = {'testsRun': result.testsRun, 'skipped': len(result.skipped),
              'failures': len(result.failures), 'errors': len(result.errors),
              'expectedFailures': len(result.expectedFailures), 'unexpectedSuccesses': len(result.unexpectedSuccesses)}
    exit_code = 0 if result.wasSuccessful() else 1
    return {'exit_code': exit_code, 'counts': counts, 'status': classify(exit_code, counts)}


def _child(suite: str) -> int:
    sys.path.insert(0, str(ROOT / 'backend'))
    # Discovery imports can print; capture them too so stdout stays one JSON document.
    imports = io.StringIO()
    with redirect_stdout(imports), redirect_stderr(imports):
        discovered = unittest.defaultTestLoader.discover(str(ROOT / 'tests' / suite))
    result = run_suite(discovered)
    print(json.dumps(result))
    return result['exit_code']


def run_command(command_id: str, argv: list[str], *, suite: bool = False) -> dict:
    npm = command_id.startswith('frontend-')
    if npm:
        executable = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        if executable is None:
            return {'id': command_id, 'exit_code': None, 'status': 'not_run', 'reason': 'binary_missing'}
        argv = [executable, *argv[1:]]
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'backend')
    try:
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True,
                                errors='replace', timeout=300)
    except FileNotFoundError:
        return {'id': command_id, 'exit_code': None, 'status': 'not_run', 'reason': 'binary_missing'}
    except subprocess.TimeoutExpired:
        return {'id': command_id, 'exit_code': None, 'status': 'fail', 'reason': 'timeout'}
    except OSError:
        return {'id': command_id, 'exit_code': None, 'status': 'not_run', 'reason': 'spawn_failed'}
    if suite:
        try:
            summary = json.loads(result.stdout)
            counts = summary['counts']
            if not isinstance(counts, dict) or any(type(counts.get(k)) is not int or counts[k] < 0
                    for k in ('testsRun', 'skipped', 'failures', 'errors', 'expectedFailures', 'unexpectedSuccesses')):
                raise ValueError('invalid_counts')
            counts = {key: counts[key] for key in ('testsRun', 'skipped', 'failures', 'errors',
                                                   'expectedFailures', 'unexpectedSuccesses')}
            return {'id': command_id, 'exit_code': result.returncode, 'counts': counts,
                    'status': classify(result.returncode, counts)}
        except (ValueError, KeyError, TypeError):
            return {'id': command_id, 'exit_code': result.returncode, 'status': 'fail', 'reason': 'invalid_test_summary'}
    return {'id': command_id, 'exit_code': result.returncode, 'status': classify(result.returncode)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layer', choices=('portable',), required=True)
    parser.add_argument('--output', type=Path, required=True)
    # Child mode has no file-writing options and is not a selectable acceptance layer.
    if len(sys.argv) == 3 and sys.argv[1] == '--_unittest' and sys.argv[2] in SUITES:
        return _child(sys.argv[2])
    args = parser.parse_args()
    try:
        prepare_output(args.output)
        if (args.output / 'results.json').exists() or (args.output / 'results.json').is_symlink():
            raise FileExistsError('results_exist')
    except (OSError, ValueError) as exc:
        parser.exit(2, f'runner_output_rejected: {type(exc).__name__}\n')
    checks = [run_command(name, [sys.executable, str(Path(__file__).resolve()), '--_unittest', name], suite=True)
              for name in SUITES]
    for name, argv in (
        ('schemas', [sys.executable, 'tools/export_contract_schemas.py', '--check']),
        ('api-client', [sys.executable, 'tools/export_api_client.py', '--check']),
        ('pip', [sys.executable, '-m', 'pip', 'check']),
        ('frontend-tests', ['npm', '--prefix', 'apps/desktop', 'test']),
        ('frontend-build', ['npm', '--prefix', 'apps/desktop', 'run', 'build']),
    ):
        checks.append(run_command(name, argv))
    status = 'fail' if any(c['status'] in {'fail', 'not_run'} for c in checks) else 'pass'
    report = {'schema_version': 1, 'layer': args.layer, 'status': status,
              'recorded_at': datetime.now(timezone.utc).isoformat(), 'environment': probe_environment(),
              'native_acceptance': 'not_evaluated', 'gates': 'not_evaluated', 'checks': checks}
    try:
        write_json_once(args.output / 'results.json', report)
    except OSError as exc:
        parser.exit(2, f'runner_output_rejected: {type(exc).__name__}\n')
    print(json.dumps({'layer': args.layer, 'status': status, 'checks': {c['id']: c['status'] for c in checks}}))
    return 0 if status == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
