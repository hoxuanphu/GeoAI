"""Generate draft JSON Schema offline, or check it without modifying files."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pydantic.json_schema import models_json_schema

from geoai.contracts import (
    CONTRACT_MODELS, PRIVATE_CONTEXT_MODELS, SCHEMA_VERSION, WIRE_MODELS,
)


def schema_bytes() -> bytes:
    models = {**CONTRACT_MODELS, **WIRE_MODELS, **PRIVATE_CONTEXT_MODELS}
    _, schema = models_json_schema(
        [(model, "validation") for _, model in sorted(models.items())],
        title=f"GeoAI draft contracts {SCHEMA_VERSION}",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$comment"] = (
        "Generated from Pydantic; cross-field and live authorization checks remain required. "
        "Private runtime context definitions are not public RPC or durable project records."
    )
    schema["x-geoai-registries"] = {
        "durable": sorted(CONTRACT_MODELS), "wire": sorted(WIRE_MODELS),
        "private_runtime": sorted(PRIVATE_CONTEXT_MODELS),
    }
    return (json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "schemas" / f"contracts-v{SCHEMA_VERSION}.json")
    parser.add_argument("--check", action="store_true", help="fail on a missing/stale artifact without writing")
    args = parser.parse_args()
    expected = schema_bytes()
    if args.check:
        if not args.output.is_file():
            print("Missing generated contract schema", file=sys.stderr)
            return 1
        if args.output.read_bytes() != expected:
            print("Stale generated contract schema", file=sys.stderr)
            return 1
        print("Contract schema is current")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(expected)
    print("Generated contract schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
