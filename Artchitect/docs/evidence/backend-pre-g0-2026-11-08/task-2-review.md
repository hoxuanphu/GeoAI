# Task 2 independent review

Date: 2026-11-09. Verdict: **approved for the bounded metadata foundation**. No actionable correctness or spec-compliance findings remain in the reviewed Task 2 source. This does not approve native RES acceptance or the whole SPEC-009 implementation.

Reviewed the entire `task-2-review-package.txt`, current resolver/tests, numbered brief, review brief, implementation plan, relevant contract models, SPEC-009, worker resolver/security requirements, IPC start contract, implementation gaps, and completed `task-2-report.md`. No production files were edited by this review.

The implementation checks exact manifest/context bytes, independently supplied trusted start intent and launch identity, explicit/represented dependency closure, project/grid/budget bindings, one-use starts, retired attempt/token/context replay, revocation, and candidate project/attempt/staging association. Bytes retained internally and fresh parsed read-entry views avoid nested caller-mutation changes to registered intent. The coordinator-only serialized-call requirement and metadata-only owner identity are stated explicitly. Report coverage boundaries correctly leave native bootstrap, file/handle stability, process shutdown, OS ownership, persistent/cross-process grants, and publish transaction checks pending.

## Independent verification

PowerShell with `$env:PYTHONPATH='backend'`; global existing interpreter/packages, no installs. All commands exited 0:

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests/storage -p test_grant_registry.py -v` | 13 pass |
| `python -m unittest discover -s tests/contracts -v` | 57 pass |
| `python -m unittest discover -s tests/storage -v` | 32 pass, including the 13 focused tests |
| `python -m unittest discover -s tests/integration -v` | 14 pass |
| `python -m unittest discover -s tests/architecture -v` | 2 pass |
| `python tools/export_contract_schemas.py --check` | current |
| `python tools/export_api_client.py --check` | current |

These independent suite runs total 105 distinct passing tests, no skips; catalog was not rerun by this reviewer. The implementer's report separately records 9 catalog tests and its 114-test total.

Four additional independent probes ran via a PowerShell here-string piped to `python -`, importing `GrantTests` fixture setup from `tests/storage/test_grant_registry.py`:

1. After registration/acceptance, forcibly mutate a returned entry's nested location with `object.__setattr__`; a subsequent resolve retains the original location.
2. Register an old candidate, revoke its context, register/accept a new context/attempt/token/staging; checking the old candidate through the new context raises `GrantError`.
3. The new attempt still resolves the same external input dependency after old-context revocation.
4. Closing the launch rejects new candidate registration even with the last valid context and attempt.

All four probes passed. They exercise metadata state only and create/open/delete no candidate or input files. The existing native acceptance matrix remains outstanding as documented; no absent native behavior is treated as a Task 2 defect.
