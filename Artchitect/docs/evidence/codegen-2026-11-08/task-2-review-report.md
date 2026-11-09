# Task 2 - Independent SPEC-001 review

Date: 2026-11-08. Verdict: **PASS for the bounded draft contracts implementation; no blocking code findings.** Parent must finish documentation/status synchronization before closing SPEC-001. This review does not close G0/G1 or accept any native resolver, transport, GIS, model or installer behavior.

## Scope and sources

Read task-2-review-brief.md, task-1-brief.md and task-1-report.md; roadmap/spec index and SPEC-001; contracts.md, ipc-protocol.md, worker-resolver.md, domain-rules.md, prithvi-profile.md and source contract design. Inspected all contracts modules, exporter, generated schema structure, extension tests and workflow/wire/private fixtures. No Git operation, production edit or subagent delegation was performed.

## Findings

No actionable correctness/spec-compliance defect found within the agreed SPEC-001 type-validation boundary. The new RPC models enforce method/params agreement, strict nonboolean IDs and integer counts, required success result including null, result/error exclusivity, error ID/code rules, required start context ID/hash and matching job. Open JSON and metrics reject nonfinite numbers, including nested values. Model readiness, publish/fallback, review/report, and private context manifest bindings are covered and consistent with the bounded design.

**Handoff action (documentation, not a code blocker):** surrounding status prose still says implementation is absent at `Artchitect/docs/contracts.md:3`, `Artchitect/docs/ipc-protocol.md:3`, `Artchitect/docs/worker-resolver.md:3` and the roadmap SPEC-001 row (`Artchitect/docs/roadmap.md:38` at inspection). Parent already owns these changes; distinguish implemented/tested metadata schemas from pending native resolver/transport. SPEC-001 was being updated concurrently during review, so these are source locations at inspection, not a claim that parent has finished synchronization.

## Independent verification

Environment: global Python with `PYTHONPATH=backend`; task-1 records CPython 3.12.4/Pydantic 2.13.2. The reviewer ran:

```powershell
$env:PYTHONPATH = 'backend'
python -m unittest discover -s tests/contracts -v
python tools/export_contract_schemas.py --check
```

Actual results: **51 tests in 1.736s, OK**; **Contract schema is current**, exit 0. Existing suite includes exporter repeat determinism, missing/stale detection without writes, alternate CWD and generated definition coverage.

An additional read-only Python probe passed **30 assertions/cases**: every event's positive JSON case; rejection of all incompatible event/params pairings (artifact_candidate/completed intentionally share CandidateParams); null IDs accepted for parse/invalid-request failures; success results null/false/zero/list/object with integer ID zero; business segmentation with decoder removed rejected; nested Infinity/NaN rejected in parameters, per-class evaluation, metrics and coverage. These probes did not modify source, fixtures or generated artifacts.

## Accepted boundaries and remaining work

- Arbitrary PHY provenance and physical run manifests are explicitly rejected until a typed feature-specific profile exists. PhysicalModelSpec and physical/hybrid JobSpec remain design records. This matches the task-1 ruling rather than pretending physical execution exists.
- Private context locations/file identities are typed metadata and explicitly isolated in their registry; public start accepts IDs/hashes only. Actual Windows path validity/confinement, handles, dependency closure, real bytes/hashes, access rights, worker/project/owner binding, revocation and fencing remain SPEC-009/004 runtime acceptance work.
- GPU provenance recognizes documented declared backend labels/device identity; the service runtime registry must establish the actual execution backend/device. A schema-only label is not GPU validation evidence.
- Cross-field Pydantic validators are intentionally richer than generated JSON Schema. Generated schemas are a definition registry, not a replacement for canonical Pydantic/service validation.
- Durable fixtures remain structurally synthetic: one blue asset does not supply six-band HLS input; a technical model/evaluation is not a business-ready pipeline. Positive business-record probes demonstrate schema shape only.
- No evidence from these checks establishes model accuracy, CRS correctness, packaging, transport framing, native I/O or deep immutability after publication.
