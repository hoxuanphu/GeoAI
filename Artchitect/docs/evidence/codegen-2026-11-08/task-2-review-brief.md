# Task 2 — independent review of SPEC-001

Read task-1-brief.md and task-1-report.md in this directory, SPEC-001, contracts.md, ipc-protocol.md, worker-resolver.md, Pydantic sources, test/fixture/exporter. Workspace has no Git; compare baseline-inventory.json if needed and inspect current files directly. No commit claims. Parent owns docs status. Review both spec compliance and correctness/maintainability, with emphasis on validation boundaries.

Run global python with PYTHONPATH=backend (Pydantic 2.13.2 installed); new venv package install blocked by wheel HTTP403. Contracts suite, offline exporter/check and extra narrow probes as needed. No application runtime required yet. No GIS/ML performance claims.

Check RPC method/params discriminants, bool/null IDs, finite values, result/error envelope exclusivity, nested dictionaries, model readiness, publish/provenance, review metadata, context private/public separation, schema consistency/determinism and stale detection. Check positive cases, not only negative tests; fixture not secretly treated as business-ready. No generic PHY provenance allowed before a typed feature-specific profile.

Exact context path/file identity fields not specified in prose originally; implementer may add explicit draft note to worker-resolver.md. Private typed values do not claim native path enforcement. This is a bounded implementation decision, not unauthorized new architecture.

Report actionable issues with severity and exact file/line/evidence to task-2-review-report.md; do not edit production files. Do not spawn subagents. Return short findings summary and pass/needs fixes. Distinguish SPEC-009 runtime acceptance (intentionally pending) from missing required SPEC-001 type validation.
