# Task 1 — SPEC-001 contracts foundation

Read Artchitect/docs/specs/001-contracts-baseline.md first: it is the requirements. Also read contracts.md, domain-rules.md, prithvi-profile.md, ipc-protocol.md, worker-resolver.md and the existing Pydantic/test/fixture files. Implement existing design, not runtime or new architecture.

Complete missing runs.py, rpc.py, __init__.py public exports/registry and deterministic tools/export_contract_schemas.py plus generated schemas/contracts-v0.1.0.json. Extend typed access.py for the private WorkerAccessContext/read/bootstrap values in worker-resolver.md so start context ID/hash and full draft schema can be checked; no native I/O, resolver or importer in this task. Keep private runtime context clearly separate from durable project records.

Use existing 30 tests as RED baseline (missing exports/exporter observed); add meaningful missing invariant/positive/RPC/context tests before implementation, run them to observe RED. Validate full fields/enums and cross-field invariants from docs, finite JSON, UTC, strict IDs/integers, review/report/gate rules. Do not accept arbitrary physical provenance dictionaries: no PHY profile is selected; explicitly reject physical run provenance pending a typed feature-specific profile while leaving PhysicalModelSpec/JobSpec design supported. Document this limitation. Fix misleading affine comment. No GIS/model runtime deps.

Read_entries location is private, typed managed-local or external-registered-local; use location/file identity fields documented explicitly in worker-resolver.md, avoid path/URL fields on public RPC. Exact Windows path enforcement belongs to native resolver, not claims here.

Update synthetic workflow fixture including a valid complete start and private context fixture as needed. Keep no secrets/personal paths. Test positive method/event cases (start with context IDs/hash, matching job), result/error exclusivity, no bool ID, invalid progress. Exporter --check must detect missing/stale artifact without modifying it, usable offline from any CWD; deterministic generated definitions including public wire and private context models without duplicate divergent types. Keep Pydantic canonical. Never hand edit generated schema.

Workspace C:/Users/phuhx1/Documents/GeoAI has NO Git; do not init/commit. Use venv/Scripts/python.exe once parent installs dependencies. Do not edit roadmap/tracker/other docs (parent owns them); you may add a short implementation note to worker-resolver.md/contracts.md for exact draft fields chosen ONLY if necessary, tell parent which.

Do not spawn subagents. Follow TDD. Report to task-1-report.md in this folder with implementation, commands/results, limitations, changed files. Return short status. Run unittest contracts suite and exporter --check, record actual outputs. Parent will independently review.
