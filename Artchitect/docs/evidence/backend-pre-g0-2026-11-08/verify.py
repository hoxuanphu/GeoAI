"""Reproduce available pre-G0 checks without installing dependencies."""
from __future__ import annotations

import importlib.metadata
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def documentation_check():
    """Check local Markdown link targets; rendering and GIS semantics are separate."""
    links = 0
    missing = []
    paths = sorted((ROOT / "Artchitect" / "docs").rglob("*.md"))
    for path in paths:
        content = path.read_text(encoding="utf-8-sig")
        for target in re.findall(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)", content):
            target = target.strip().strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            links += 1
            destination = (path.parent / unquote(target.split("#", 1)[0])).resolve()
            if not destination.exists():
                missing.append({"source": path.relative_to(ROOT).as_posix(), "target": target})
    protected = json.loads((OUT / "protected-input-hashes.json").read_text(encoding="utf-8-sig"))
    changed = [r["path"] for r in protected if not (ROOT / r["path"]).is_file()
               or hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest() != r["sha256"]]
    authorized = {"backend/geoai/contracts/access.py", "backend/geoai/contracts/__init__.py",
                  "schemas/contracts-v0.1.0.json"}
    unexpected = sorted(set(changed) - authorized)
    report = {"markdown_files": len(paths), "local_links": links,
              "missing_targets": missing, "protected_files": len(protected),
              "protected_changes": changed,
              "authorized_contract_extension": sorted(set(changed) & authorized),
              "unexpected_protected_changes": unexpected,
              "scope": "target existence and protected file hashes; anchors/rendering not checked"}
    (OUT / "final-documentation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"name": "documentation", "exit_code": int(bool(missing or unexpected)),
            "log": "final-documentation.json"}


def main() -> int:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "backend"), PYTHONIOENCODING="utf-8")
    records = []

    def run(name, args, cwd=ROOT, timeout=180):
        try:
            result = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=timeout)
            output = result.stdout + result.stderr
            code = result.returncode
        except subprocess.TimeoutExpired:
            output, code = "Verification timed out; result unavailable.\n", 124
        (OUT / f"final-{name}.log").write_text(output, encoding="utf-8")
        record = {"name": name, "command": args, "exit_code": code,
                  "log": f"final-{name}.log"}
        count = re.search(r"Ran (\d+) tests? in", output)
        if count:
            record["tests"] = int(count[1])
            skip = re.search(r"skipped=(\d+)", output)
            record["skipped"] = int(skip[1]) if skip else 0
        records.append(record)
        print(f"{name}: exit={code}" + (f" tests={record['tests']} skipped={record['skipped']}"
              if count else ""), flush=True)

    for suite in sorted((ROOT / "tests").iterdir()):
        if suite.is_dir() and any(suite.glob("test_*.py")):
            run(suite.name, [sys.executable, "-m", "unittest", "discover", "-s",
                             str(suite.relative_to(ROOT)), "-v"])
    run("syntax", [sys.executable, "-m", "compileall", "-q", "backend", "tests", "tools", "migrations"])
    for name, path in (("schema", "tools/export_contract_schemas.py"),
                       ("client", "tools/export_api_client.py")):
        run(name, [sys.executable, path, "--check"])
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm:
        for name, args in (("dom", ["test"]), ("typecheck", ["run", "typecheck"]),
                           ("frontend-build", ["run", "build"])):
            run(name, [npm, *args], ROOT / "apps" / "desktop")
    else:
        records.append({"name": "frontend", "not_run": "npm unavailable"})
    records.append(documentation_check())
    packages = {}
    for name in ("pydantic", "fastapi", "uvicorn", "httpx", "SQLAlchemy", "alembic"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    summary = {"date": datetime.now(timezone(timedelta(hours=7), "Asia/Bangkok")).isoformat(),
               "platform": platform.platform(), "python": platform.python_version(),
               "packages": packages, "checks": records,
               "native_rust": "not run: cargo unavailable" if not shutil.which("cargo") else "requires separate build",
               "scope": "synthetic foundation checks; no G0/G1/G2 closure"}
    summary["python_test_totals"] = {
        "discovered": sum(r.get("tests", 0) for r in records),
        "skipped": sum(r.get("skipped", 0) for r in records),
        "passed": (sum(r.get("tests", 0) - r.get("skipped", 0) for r in records)
                   if all(r.get("exit_code", 0) == 0 for r in records if "tests" in r) else None)}
    (OUT / "final-results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return int(any(r.get("exit_code", 0) for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
