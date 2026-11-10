# Task 2 — metadata context/grant/reference foundation

Date: 2026-11-09. Scope complete for review: pure in-memory coordinator metadata only. No public routes/capabilities, new exchanged types/schema, native file opens, SQLite, workers, provider calls, installs, or Git operations.

## Files and interface

- `backend/geoai/storage/resolver.py`: `GrantRegistry`, sanitized `GrantError`, private ordinary `_Grant` helper.
- `tests/storage/test_grant_registry.py`: 13 metadata behavior tests, positive managed/external read entry resolution and negative matrices.
- This report and `task-2-*.log` evidence files. Parent owns roadmap/spec/tracker/status updates.

Internal integration example for Task 4 (trusted coordinator only):

```python
registry = GrantRegistry(
    worker_id=launch.worker_id, launch_nonce=launch.nonce,
    project_id=trusted_project_id, execution_owner_id=owner.id,
    owner_epoch=owner.epoch,
)
registry.register(
    context_bytes=context_bytes, job_bytes=job_bytes,
    snapshot_bytes=snapshot_bytes,
    expected_start=trusted_start,  # independent expected attempt/IDs/hash/budget
    required_ref_ids=trusted_dependency_closure,
)
registry.accept(received_start)  # exactly once, after binding validation
entry = registry.resolve(context_id, current_attempt, ref_id)
registry.register_candidate(
    coordinator_issued_candidate_id, context_id,
    project_id=trusted_project_id, attempt=current_attempt,
    staging_id=trusted_staging_id,
)
staging_id = registry.check_candidate(
    received_candidate_id, context_id,
    project_id=trusted_project_id, attempt=current_attempt,
)
registry.revoke(context_id)  # cancellation/end of attempt metadata
registry.close()            # end of launch lifetime
```

`register` returns SHA-256 of exact context bytes. `accept` returns no authority object; `resolve` returns a freshly parsed canonical `WorkerReadEntry`. Candidate check returns only registered staging ID, never a path. `GrantError.code` is `invalid_input`, `stale_attempt`, or `missing_resource`; stable text never includes caller path/nonce/token. Caller must serialize registry operations; this is not a thread-safe transactional store. Do not expose construction/registration to UI or reconstruct it from client project manifests. Coordinator must revoke the registry when the trusted owner epoch loses validity; constructor identity is not OS-lock proof. New launch/epoch requires a new registry and trusted bootstrap.

## Enforced semantics and dependency kinds

- Immutable `bytes` snapshots store exact context/job/snapshot and serialized validated expected start. No original nested mutable Pydantic object is retained as intent. Bytearray/memoryview inputs are rejected; no canonical reserialization is substituted for exact-byte hashing.
- Context matches trusted worker ID, nonce, project, execution owner ID/epoch and independent expected start (context ID/hash, complete AttemptKey job/attempt/token, job/snapshot IDs, resource budget). Job/snapshot bytes match context hashes; IDs/projects/grid and job budget agree; manifest read-entry sizes agree with actual supplied byte lengths.
- Both job/snapshot refs must be `kind=manifest`, enforced by existing canonical `WorkerAccessContext`. All entries use existing union of managed-local or external-registered-local metadata and `read_only` permission. Other supported kinds remain `input`, `model`, `checkpoint`, `profile`; registry does not infer a particular kind from an opaque ref ID or claim that kind proves native file content.
- Required read refs include explicit trusted closure plus job workflow/grid/models/physical models/parameter snapshots and input assets/QA policy/transforms/dependencies/optional mosaic recipe. Model/runtime/driver-specific transitive dependencies not represented by these contracts must be supplied explicitly in `required_ref_ids`; no latest/provider resolution or invented fallback occurs.
- Only one registered/accepted grant active per registry. Context IDs and job/attempt pairs and generation tokens remain consumed after revoke; a fresh context ID cannot replay a retired attempt. Failed registration does not consume IDs. Failed start validation does not consume the valid start. Successful start is one-use.
- Revoke marks the grant unusable for acceptance, resolution and candidate checks, freeing the active slot. A new attempt needs new context/attempt/token; it may share read refs/dependencies. Close revokes every grant and permanently ends registration for that launch. Revocation is metadata-only: it cannot close native handles or stop an existing process.
- Coordinator-issued candidate IDs bind to active accepted context/project/full attempt/staging ID. Duplicate IDs, path-shaped IDs, wrong project/staging/attempt, unknown IDs, and candidate use after revoke are rejected. This registry performs no file publication, checksum ownership inference or deletion. Shared bytes/dependency data are never deleted by close/revoke.

## TDD and verification evidence

Existing interpreter and packages, PowerShell, `PYTHONPATH=backend`. Test budgets/identities are synthetic fixtures only.

| Command | Result | Log |
| --- | --- | --- |
| `python -m unittest discover -s tests/storage -p test_grant_registry.py -v` before implementation | RED: 11 expected assertion failures (registry absent) | `task-2-red.log` |
| Same after adding replay behavior test | RED: 13 run, 1 failure: revoked attempt regranted via new context ID | `task-2-red-replay.log` |
| Same after implementation/fix | GREEN: 13 pass | `task-2-green.log` |
| `python -m unittest discover -s tests/contracts -v` | 57 pass | `task-2-contracts.log` |
| `python -m unittest discover -s tests/storage -v` | 32 pass (19 existing + 13 new) | `task-2-storage.log` |
| `python -m unittest discover -s tests/catalog -v` | 9 pass | `task-2-catalog.log` |
| `python -m unittest discover -s tests/integration -v` | 14 pass | `task-2-integration.log` |
| `python -m unittest discover -s tests/architecture -v` | 2 pass | `task-2-architecture.log` |
| `python tools/export_contract_schemas.py --check` | current | `task-2-schema-check.log` |
| `python tools/export_api_client.py --check` | current | `task-2-client-check.log` |

Total final relevant suites: 114 pass, no skips. No tests claim GIS/model/native or database functionality.

## RES coverage boundaries

- RES-01: metadata context hash/worker/nonce rejection verified; bootstrap handle identity, persistent/cross-process registry and native descriptor transfer pending.
- RES-02: manifest exact-byte hashes, dependency closure and bindings verified; actual file content/handle identity and complete adapter dependency discovery pending.
- RES-03: project/epoch/attempt/token, one-use and retired-context replay metadata verified; owner recovery across processes/restarts needs native/DB integration.
- RES-04: API returns only allowlisted read entries and scoped candidate/staging IDs; native write confinement/OS permissions/reparse checks pending.
- RES-05: candidate project/attempt/staging/ID/revoke metadata verified; physical staging ownership and publication remain pending.
- RES-06: no native checks here; hardlink/reparse/open-handle/content stability and commit-time revalidation pending.
- RES-07: grant metadata revocation verified; stopping workers, revoking open handles, waiting and resource reconciliation pending.
- RES-08: no deletion or I/O occurs and subsequent attempts can reuse dependency refs; real shared leases/pin/retention and concurrent native integration pending.

No RES native acceptance or G0/G1 closure is claimed. Task 4 must recheck current attempt/owner and candidate at its authoritative state/transaction boundary; metadata success alone cannot authorize publication.
