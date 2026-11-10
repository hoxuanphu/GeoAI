# Task 9 — Native storage, extraction and publication composition

Read AGENTS.md, SPEC-004/009, worker-resolver.md, importer-resolver-security.md,
architecture.md, existing storage/importer.py and resolver.py, task 6/7/8 code
and reports. No subagents/installations/commits/public job routes/live providers
or GIS parsers. Keep capability flags false and existing changes intact.

Implement storage I/O adapters using Windows native handle APIs. Managed roots
and external registrations are supplied internally; no public free-path input.
Validate names/ancestors/reparse, opened handle final path/volume/file ID/link
count, and actual bytes/hash while handle prevents modification/deletion. Do
not rely on resolve/commonprefix/check-then-reopen for Windows confinement.
Unsupported platforms/filesystems fail closed; portable fixture-only adapters
must be explicitly distinct. Open only an allowlisted read ref from an accepted
grant. External files outside project remain valid when identity/hash match;
do not achieve negative tests by refusing all input. No writable input handles.

Create fresh attempt staging with exclusive relative file creation and held
directory/ancestor identities. Bounded ZIP extraction consumes the same strict
inventory policy and actual bytes/deadline/cancel/CRC/hash accounting, no
extractall or trust in headers. Failure leaves no registered asset/pack and
cleans up only owned new staging. No executable/model activation or native
format loading. Explicitly unsupported formats/dependencies stay refused.

Implement jobs/publisher.py as composition of resolver, coordinator/repository
and storage. Storage never imports jobs. Candidate registration is immutable,
scoped to project/job/attempt/context/staging, with artifact/profile references.
Resolve by ID, verify file handle/bytes/hash and manifest relationship, require
explicit trusted validator for grid/coverage/profile (never pretend hash proves
GIS), prepare immutable no-overwrite same-volume output, then repository
transaction rechecks current full attempt key/owner/state/uniqueness. Cancel or
stale transaction leaves an unserved orphan; API availability requires DB
publication and valid bytes. Reconcile startup only under writer guard; missing
or modified publication becomes unavailable, never auto-promote orphan. GC
consults retained leases/pins, and rechecks ownership before removal.

Meaningful real filesystem/SQLite/process integration tests with small fixtures:
valid managed/external input, same-size modified file, hardlink/reparse and
ancestor swap, sentinel outside staging, extraction cancel/corrupt/quota/failure
rollback, candidate wrong project/attempt/token/hash, cancel-before-commit,
rename-before-crash and commit-before-UI, no-overwrite, restart/reconcile/missing
bytes, retained shared dependencies. DB tests skip explicitly only when its
dependency is missing. Windows tests run where available; keep cross-session
and machine-clean claims pending. Write task-9-report.md + RED/GREEN logs with
APIs, tests, exact remaining limitations. Parent handles status docs/review.
