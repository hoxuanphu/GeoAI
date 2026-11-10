"""Versioned canonical encoding for immutable JobSpec intent."""
import hashlib
import json

from geoai.contracts import JobSpec

INTENT_DIGEST_PROFILE = "job-spec-json-v1"


def canonical_intent(spec: JobSpec) -> tuple[bytes, str]:
    if not isinstance(spec, JobSpec):
        raise TypeError("JobSpec required")
    dumped = spec.model_dump(mode="json")
    json.dumps(dumped, allow_nan=False)
    validated = JobSpec.model_validate(dumped)
    raw = json.dumps(validated.model_dump(mode="json"), sort_keys=True,
                     separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(INTENT_DIGEST_PROFILE.encode("ascii") + b"\0" + raw).hexdigest()
    return raw, digest
