# Ubuntu foundation — checkpoint 11/11/2026

Working tree on feat/ubuntu-installer, baseline d4e0060; no commits/branch/push.
Existing user documentation and builder changes retained. This is an ongoing
execution checkpoint, not completion of the full 26-task plan.

| Task | Implementation / evidence | Remaining acceptance |
| --- | --- | --- |
| A-01/A-02 | [Handoff](A-02/handoff.md), Windows registry/purpose/deadline adapters; shared service injection and cancellation transaction regression; four Important review findings fixed RED→GREEN | Actual Windows native regression |
| A-03 | [Handoff](A-03/handoff.md), common process/owner boundaries, deadline facade, bootstrap pipe ownership and retained writer lease; focused 13 pass | Windows native process/owner acceptance |
| A-04 | [Handoff](A-04/handoff.md), private ledger/codec/schema; 66 contracts pass, independent review no Critical/Important | C-03 native journal writer/observer |
| A-05 | [Ubuntu22](A-05/ubuntu22-baseline/results.json), [Debian](A-05/debian-baseline/results.json), runner/probe implemented; independent review in progress | Ubuntu24.04/Windows executors not_run; native/desktop layers not yet provided |
| B-01 | Rust library/session/runtime paths in progress | Review and Linux compile; Windows compile not_run |
| B-02–E-05 | Pending | Continue plan dependencies |

Current portable baseline on each executor: 274 Python tests discovered, 207 pass,
67 Windows-specific skip, no failures/errors. Exporters, pip, seven frontend tests
and frontend build pass. These are portable checks, not native proof; 010.1–010.3,
G0–G4 and capability flags remain unchanged/open.

An internal shell preview `.deb` was built and installed in private Ubuntu22
builder. [Build/install/runtime logs](preview-build/handoff.md) record the actual
result and limits. It is a debug shell preview with no Linux backend included,
not an end-user Ubuntu release. No Debian fallback is needed to produce the shell
package; Debian portable tests supplement the available Ubuntu22 tests.

## Git checkpoint requested 12/11/2026

User requested committing/pushing the current work before completing the full plan.
Latest A05 reviewed-baseline directories on Ubuntu22 and Debian both report pass;
these supersede the original baseline version probes (which truncated Node).
Runner now records only derived fields, with no raw command log tails.
Fresh architecture suite: 11/11 pass; schema/API checks current. A05 scoped re-review
and final B01 expanded Rust checks remain pending. This commit is work in progress,
not completion of SPEC-010 or the implementation plan.
