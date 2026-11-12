#!/usr/bin/env python3
"""Read-only, allowlisted foundation environment probe; never installs packages."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = '.geoai-foundation-run'
OWNER = 'geoai-foundation-evidence-v1\n'


def prepare_output(path: Path) -> None:
    path = Path(path)
    if path.is_symlink():
        raise ValueError('output_symlink_rejected')
    path.mkdir(parents=True, exist_ok=True)
    marker = path / MARKER
    if marker.is_symlink():
        raise ValueError('output_marker_symlink_rejected')
    if any(path.iterdir()):
        if not marker.is_file() or marker.read_text(encoding='utf-8') != OWNER:
            raise ValueError('output_not_task_owned')
    else:
        with marker.open('x', encoding='utf-8') as stream:
            stream.write(OWNER)


def write_json_once(path: Path, data: dict) -> None:
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write('\n')


def _command(argv: list[str], *, accepted_codes: tuple[int, ...] = (0,)) -> str | None:
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                                timeout=4, errors='replace')
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode in accepted_codes else None


def _version(argv: list[str]) -> str | None:
    output = _command(argv)
    match = re.search(r'(?<![\w.])v?(\d+\.\d+(?:\.\d+)?(?:[-+][\w.]+)?)(?![\w.])', output or '')
    return match.group(1) if match else None


def probe_environment() -> dict:
    """Return only documented machine/version facts, never env or raw subprocess output."""
    try:
        release = platform.freedesktop_os_release()
    except OSError:
        release = {}
    libc_name, libc_version = platform.libc_ver()
    packages = {}
    for name in ('pydantic', 'fastapi', 'uvicorn', 'httpx', 'SQLAlchemy', 'alembic'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    fs = _command(['stat', '-f', '-c', '%T', str(ROOT)]) if sys.platform == 'linux' else None
    user_state = _command(['systemctl', '--user', 'is-system-running'], accepted_codes=(0, 1)) if sys.platform == 'linux' else None
    if user_state not in {'running', 'degraded', 'starting', 'initializing', 'maintenance', 'stopping', 'offline'}:
        user_state = 'not_accessible' if sys.platform == 'linux' else 'not_applicable'
    return {
        'schema_version': 1,
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'os': {key: release.get(key) for key in ('ID', 'VERSION_ID', 'PRETTY_NAME')},
        'platform': platform.system(), 'arch': platform.machine(), 'kernel': platform.release(),
        'libc': {'name': libc_name, 'version': libc_version},
        'filesystem': fs if fs and re.fullmatch(r'[\w-]{1,64}', fs) else None,
        'cgroup_v2': Path('/sys/fs/cgroup/cgroup.controllers').is_file(),
        'user_manager': user_state,
        'python': {'version': platform.python_version(), 'implementation': platform.python_implementation()},
        'toolchain': {name: _version(argv) for name, argv in {
            'node': ['node', '--version'], 'npm': ['npm', '--version'],
            'rustc': ['rustc', '--version'], 'cargo': ['cargo', '--version'],
            'gtk3': ['pkg-config', '--modversion', 'gtk+-3.0'],
            'webkitgtk41': ['pkg-config', '--modversion', 'webkit2gtk-4.1'],
        }.items()},
        'packages': packages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare_output(args.output)
        write_json_once(args.output / 'env.json', probe_environment())
    except (OSError, ValueError) as exc:
        parser.exit(2, f'preflight_output_rejected: {type(exc).__name__}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
