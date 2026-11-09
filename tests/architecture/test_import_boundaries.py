"""Enforce documented static package dependencies without importing runtimes."""
import ast
from importlib.util import resolve_name
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2] / "backend" / "geoai"
ALLOWED = {
    "contracts": set(), "storage": set(), "products": set(),
    "catalog": {"products", "storage"},
    "geoprocessing": {"products", "storage"},
    "models": {"products", "storage"}, "compute": {"models"},
    "analytics": {"geoprocessing", "models", "compute"}, "review": {"storage"},
    "reports": {"geoprocessing", "storage"}, "viewer": {"geoprocessing", "storage"},
    "jobs": {"compute", "storage"},
    "workflows": {"jobs", "catalog", "analytics", "geoprocessing", "review", "reports", "storage"},
    "domains": {"workflows", "analytics", "reports"},
    "api": {"workflows", "jobs", "catalog", "review", "viewer", "storage"},
}


def imported_modules(path):
    parts = ("geoai", *path.relative_to(ROOT).with_suffix("").parts)
    package = ".".join(parts[:-1])
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = resolve_name("." * node.level + (node.module or ""), package) if node.level else node.module or ""
            yield base
            # Also recognize `from geoai import bootstrap` and `from . import jobs`.
            yield from (base + "." + alias.name for alias in node.names if alias.name != "*")


class ImportBoundaryTests(unittest.TestCase):
    def test_internal_dependencies_follow_architecture(self):
        violations = []
        for path in ROOT.rglob("*.py"):
            relative = path.relative_to(ROOT)
            if len(relative.parts) < 2 or relative.parts[0] == "workers":
                continue  # Root bootstrap and worker entry points are composition roots.
            source = relative.parts[0]
            for name in imported_modules(path):
                parts = name.split(".")
                if len(parts) < 2 or parts[0] != "geoai":
                    continue
                target = parts[1]
                if target not in ALLOWED.get(source, set()) | {source, "contracts"}:
                    violations.append(f"{relative}: {source} -> {target}")
        self.assertEqual(violations, [], "Forbidden internal dependencies:\n" + "\n".join(violations))

    def test_contracts_require_only_standard_library_and_pydantic(self):
        violations = []
        for path in (ROOT / "contracts").rglob("*.py"):
            for name in imported_modules(path):
                package = name.split(".")[0]
                if package not in sys.stdlib_module_names | {"geoai", "pydantic"}:
                    violations.append(f"{path.name}: {name}")
        self.assertEqual(violations, [], "Contracts imported a runtime dependency")


if __name__ == "__main__":
    unittest.main()
