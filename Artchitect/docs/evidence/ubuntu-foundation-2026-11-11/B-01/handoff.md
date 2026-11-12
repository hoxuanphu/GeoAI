# B-01 — shared Rust session and trusted runtime paths

Status: source implemented, final verification pending host I/O recovery; DONE_WITH_CONCERNS. Full report: `.superpowers/sdd/2026-11-10-ubuntu-foundation/task-b01-report.md`.

Baseline `d4e00607a2be36267842d8289fe3912286f8af4f`, existing dirty branch `feat/ubuntu-installer`; preserved main.rs lifetime fixes and all other tasks. No commit, branch, push, or subagent. Input interfaces: plan catalog and A-03/Ubuntu builder handoffs. Output: shared session::SessionDescriptor; Linux runtime::RuntimePaths, DevRuntimePaths, resolve_runtime, from_build_environment; filtered NativeError.

Confirmed actual Ubuntu22 builder results: 11/11 library tests, 0 failed/ignored; separately 11/11 with package debug_assertions disabled to execute release cfg. Session/library missing-function reds and actual containment/permission assertion reds are in this directory. Final expanded 14-test run (`ownership-green.log`) and desktop Cargo check (`desktop-check.log`) were launched but have not returned completion during the host I/O stall. They are pending, not pass. rustfmt is absent and formatting is not_run.

Trust policy: root/current UID ownership, no group/other writable ancestor even sticky /tmp, canonical component containment of fixed packaged executables, regular executable/no setid, native compile-time dev config only and no release dev override. Tests use private real files under work/. UID predicate coverage is unit policy verification, not multi-user chown proof. Paths are not pinned launch bytes: B-02/B-04 must revalidate at launch and enforce runtime replacement rules. Temporary/AppImage layouts under shared directories are unsupported by this first profile.

Native Windows, systemd lifecycle, GUI startup, Ubuntu24, installer and full acceptance remain not_run. Capabilities stay disabled; non-Windows desktop bootstrap is unchanged. Dependency versions/toolchain/license are recorded in dependencies.json and real Cargo.lock. Parent owns review, combined regressions, tracker/spec/roadmap updates; no acceptance gate is closed here.
