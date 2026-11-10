# Task 7 native preflight — 09/11/2026

Read-only review of SPEC-003, ADR-011, architecture, IPC, worker resolver,
Task 7 brief and the Python/Rust/bootstrap contracts currently present. No
runtime code changed, binaries installed or native acceptance executed. This
report is implementation guidance, not proof of Windows guarantees.

## Current integration points

- Rust `bootstrap_session` currently always returns
  `native_launcher_unavailable`; it must return the existing private
  `SessionDescriptor` shape `{base_url, token}`. Do not add a schema-version
  field without changing Pydantic and generated clients together.
- `geoai.bootstrap` currently accepts only two explicit dev flags and enables
  production plus development Origins. Add a separate native mode using only
  `PRODUCTION_ORIGINS`; preserve dev behavior/tests. Metadata API capability
  flags remain false pending integration acceptance.
- Production Origins are `tauri://localhost` and `http://tauri.localhost`;
  development Origin is exactly `http://127.0.0.1:1420`.
- Python/ctypes is present on the observed Windows 11 host. That observation
  does not test any lock, ACL, process-containment or lifecycle code.

## Narrow adapter interfaces

| Interface | Required lifetime and authority |
| --- | --- |
| `ExecutionOwner.acquire()` | Derive SID and private root from OS identity; acquire one machine-local lock shared by this account's sessions/installations. Return an internal guard with owner ID/epoch/PID/creation-time/session metadata. |
| `owner.acquire_writer(project_id, trusted_project_root)` | Separate project writer lock, acquired after owner. Bind canonical local volume/root identity as well as project ID. |
| `writer.assert_held(project_id)` | Repository calls before migration/write/backup/reconcile; reject closed guard, wrong project, changed owner epoch or unresolved recovery. It is an internal object, never request input. |
| `writer.retain(project_id)` / lease close | Return a lifetime-bearing internal lease; keep writer/owner alive until DB connections are closed. Releasing writer with a live repository or owner with a live managed workload must fail. |
| `ManagedProcess.launch(executable, argv, environment, child_handles, job)` | Absolute trusted runtime, explicit handle/environment allowlists, atomic job assignment. Return owned process/pipe handles; thread handle is closed after successful creation/resume. |
| `process.wait(deadline)` / `terminate_group(deadline)` | Observe group termination separately from token revocation and root-process exit; return explicit stopped/unknown outcome. No unbounded waits or unrelated PID kills. |
| `launch_session()` / `stop_session()` | Serialize one sidecar generation, bounded descriptor startup, reuse only a live session, and cleanup all owned children before retry. |

Internal dataclasses/protocols need no new exchange schema. Keep storage native
primitives free of imports from jobs. Bootstrap is the composition root.

### WriterGuard contract for repository Task 6

Define this narrow protocol in storage so Task 6 and the Task 7 native adapter
can consume it without a circular dependency:

```python
class WriterGuard(Protocol):
    @property
    def owner_id(self) -> str: ...
    @property
    def owner_epoch(self) -> int: ...  # strictly positive, read-only
    def assert_held(self, project_id: str) -> None: ...
    def retain(self, project_id: str) -> GuardLease: ...
    def close(self) -> None: ...

class GuardLease(Protocol):
    def assert_held(self, project_id: str) -> None: ...
    def close(self) -> None: ...  # idempotent, releases one retain
```

`assert_held` raises a stable internal error unless the native owner and writer
are still held for that project and owner generation, and recovery has resolved.
It returns no success boolean and cannot be created from a client assertion.
Expose owner ID/epoch as scalar read-only values; allocate a new owner ID and
increment persisted positive epoch only under exclusive ownership, never reuse
an old generation after recovery. A protocol object alone is not OS proof; only
the trusted composition root supplies the native implementation. Test doubles
are explicitly fixture guards, not native acceptance.

Repository open first checks `assert_held`, obtains one lease with `retain`,
and holds it through migrations, all live connections and backup/reconcile.
Repository close rejects active transactions, disposes connections, then closes
the lease. Migration code similarly retains its own lease for its operation.
Use a thread-safe refcount/registry so `WriterGuard.close()` refuses while leases
exist, while `ExecutionOwner.close()` refuses with writer handles or any
managed group not observed stopped. A failed/uncertain close never decrements
the counter as if the resource were released. A lease also rechecks current
generation on every transaction; retaining an object is not permission to use a
stale epoch. This contract supports lock-file handles across threads; mutex
implementations must marshal native release to the acquiring thread.

## Windows APIs and implementation constraints

1. **Identity and private runtime directory.** Use `OpenProcessToken` +
   `GetTokenInformation(TokenUser)` + `ConvertSidToStringSidW` for current SID;
   `ProcessIdToSessionId` and `GetProcessTimes` for process identity. Resolve
   `FOLDERID_LocalAppData` with `SHGetKnownFolderPath`, not arbitrary environment
   values. Use a stable GeoAI/protocol/SID namespace independent of install
   path. Free OS-allocated strings/descriptors using the matching allocator.

2. **ACL and locks.** Build a protected SID-only DACL with
   `ConvertStringSecurityDescriptorToSecurityDescriptorW`; pass the resulting
   `SECURITY_ATTRIBUTES` to `CreateDirectoryW`/`CreateFileW`/`CreateMutexW` at
   creation, rather than creating a permissive object and fixing ACL afterward.
   Validate existing objects, reject reparse ancestors and keep handles
   non-inheritable. An exclusive lock file opened through `CreateFileW` with
   `dwShareMode=0` can be closed from a different thread and naturally excludes
   all sessions sharing that user profile. Keep durable owner metadata in a
   separate protected file; an unclean previous record always enters recovery.
   If using `Global\\GeoAI...SID` mutexes instead, remember mutex ownership is
   **thread-affine**: `ReleaseMutex` must run on the acquiring thread, including
   after `WAIT_ABANDONED`. A Tauri command cannot acquire on one pool thread and
   later release from an arbitrary shutdown thread. A dedicated lifetime thread
   or explicit lock-file primitive avoids this trap. Do not fall back to
   `Local\\` namespace after global acquisition failure.

3. **Containment.** `CreateJobObjectW`, then
   `SetInformationJobObject(JobObjectExtendedLimitInformation)` with
   `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and no breakaway flags. The sole root
   lifetime handle must be non-inheritable; a child inheriting that handle would
   defeat kill-on-parent-death. Prefer `InitializeProcThreadAttributeList` +
   `UpdateProcThreadAttribute(PROC_THREAD_ATTRIBUTE_JOB_LIST)` and
   `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` on `STARTUPINFOEXW`, then `CreateProcessW`
   with `EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT |
   CREATE_NO_WINDOW`. `CREATE_SUSPENDED` may help initialization, but suspended
   creation followed by assignment alone still has a parent-crash orphan gap.
   If the OS rejects job-list attributes/nested-job constraints, fail closed;
   never retry with plain spawn-then-assign. Check all native return values.

4. **Handle and environment allowlists.** Build stdin/stdout/stderr/bootstrap
   pipes with `CreatePipe`, clear inheritance on parent ends with
   `SetHandleInformation`, and list only intended child ends in the process
   attribute list. Set `STARTF_USESTDHANDLES`; job/owner/DB and unrelated sentinel
   handles must not reach the child. `bInheritHandles=TRUE` is required for the
   explicit handle-list mechanism, not permission to omit that list. Serialize
   process creation/temporary inheritance changes if any handles are reused.
   Pass `lpApplicationName` explicitly and quote each argument using Windows
   argument rules; do not use a shell or PATH search. Build an explicit Unicode
   environment block with double-NUL termination, safe Windows OS variables and
   trusted runtime paths only. Exclude ambient credentials, proxy settings,
   arbitrary `PYTHONPATH` and DLL/search paths.

5. **Stop/recovery.** `WaitForSingleObject` on a retained process handle is
   stronger than checking PID or `GetExitCodeProcess==STILL_ACTIVE`. For groups,
   use `QueryInformationJobObject` accounting/process lists and
   `TerminateJobObject`, then bounded observation of zero active processes.
   Compare PID **and creation time** before acting on a durable identity. Root
   exit alone does not prove descendants stopped. A failed/absent named-job
   lookup must not silently turn uncertainty into compute permission; record
   recovery-required unless the supported implementation can prove complete
   old-group termination. Never kill a PID solely from a metadata file. Record
   intended job identity before process creation so an owner crash during
   launch cannot produce an untracked workload.

6. **ctypes correctness.** Set `argtypes` and `restype` for every Win32 call;
   default `c_int` truncates 64-bit handles/pointers. Use WinDLL with
   `use_last_error=True`, capture error before cleanup calls, check
   `INVALID_HANDLE_VALUE` distinctly from NULL and close only owned handles.
   Validate structure sizes/field alignment and bounded dynamic buffers for
   SID/process/job queries. Convert native errors into stable sanitized errors;
   do not return raw paths, environment or token-bearing descriptor text.

## Rust/Tauri handoff

Use `windows-sys`/`windows` bindings for the APIs above, plus serde/serde_json
for the existing descriptor; no hand-written lockfile. A non-Debug secret-bearing
descriptor with `deny_unknown_fields` should validate exact loopback host,
HTTP scheme, port 1–65535 and the current token alphabet/length. The command must
check both main-window identity and its current trusted local URL; a main label
alone does not authorize a webview navigated to a remote page. Restrict
navigation too. Never accept executable, argv, project path or URL from invoke
params.

Own lifecycle state behind a serialized session state machine. Launch the
trusted resource sidecar (or explicit compile-time dev runtime), read one
bounded descriptor line through a dedicated pipe reader and deadline channel,
drain stderr independently with a fixed memory cap, and suppress raw diagnostic
text. Startup timeout/parse failure/early exit must terminate and wait for the
owned group before a later invocation may retry. On exit, send private graceful
shutdown, wait until deadline, terminate group if necessary, then observe stop
before closing writer/owner. The Rust root Job Object lifetime handle covers
shell crash; backend-created worker groups may be nested only on supported,
tested Windows behavior. Keep token solely in memory/private IPC.

## Acceptance traps to target

Two processes/projects and alternate install paths; same-account cross-session
contention; lock release from actual lifecycle thread; abandoned record with
live descendant; PID reuse; release while repository/child remains live;
atomic-assignment failure; unrelated inheritable sentinel; parent crash before
and during launch; stderr beyond pipe capacity; descriptor timeout/malformed
input; Unicode paths; native stdout/CRT/Win32 logs; nested jobs; startup cleanup
before retry. Tests use a private temporary test namespace and only own child
processes. Same-session ctypes tests cannot close cross-session, WebView2,
unbuilt Rust or clean-bundle acceptance.
