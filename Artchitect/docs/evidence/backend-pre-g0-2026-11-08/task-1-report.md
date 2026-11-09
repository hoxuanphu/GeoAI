# Task 1 — bounded offline import/provider policy

Started 08/11/2026, verification completed **09/11/2026**, Windows/Python 3.12. Evidence folder retains its start date. Scope: the independent pre-G0 policy/inventory foundation in [plan](plan.md) and [brief](task-1-brief.md), under SPEC-009. G0/G1, native IMP/NET acceptance and runtime dispatch remain open.

## Implemented interfaces

- `geoai.contracts.imports.ArchivePolicy`: versioned administrator configuration with every archive limit explicit: input bytes, entries, actual total/per-entry expanded bytes, path depth, compression ratio, total seconds, bounded chunk size and extension allowlist. Nested archives are explicitly unsupported. `ArchiveInventory` is an immutable Contract with UTC creation/version, policy ID/digest, source digest/size, immutable per-entry hashes/sizes/names and actual total. `ProviderPolicy` likewise has explicit endpoint/private-network/request/redirect/byte/chunk/address-count/URL-length/deadline limits. Policy metadata is **not** permission from a project file; trusted host configuration must supply it.
- `geoai.storage.importer.inspect_zip(source: bytes, policy, *, inventory_id, created_at, cancelled, monotonic) -> ArchiveInventory`: bytes-only inspection; never extracts, writes, registers AssetRef, invokes GIS parsing, executes payloads or activates a pack. Cancellation and a monotonic **total** deadline are checked between bounded operations. The stdlib parses archive structure/local member identity/overlap; bounded STORE/raw-DEFLATE processing independently counts actual expanded bytes, checks actual CRC and SHA-256, verifies size/stream EOF and refuses hidden output behind forged size/CRC headers. It returns only after all entries validate.
- `geoai.catalog.policy.ProviderTransfer(policy, binding, *, cancelled, monotonic)`: pure checks only, with immutable `ProviderAssetBinding(provider_id, asset_id, version_id)`. `check_request(binding, url, addresses, *, headers, redirect)` checks every endpoint/hop and supplied IP, request/redirect budgets and redirect loops; the adapter must replace its headers with the returned `ProviderRequestPlan.headers`. Cross-origin forwarding drops **all** headers. Private headers are excluded from plan repr/serialization. `inspect_stream(binding, chunks, *, declared_length)` counts/hash-checks actual bounded chunks under the same transfer total byte/time budget and returns a receipt only when complete; bytes consumed by a failed attempt still consume the budget. `classify_failure(binding, status)` classifies credential refresh, quota/provider retry or no retry without changing the asset/version. Every actual retry must call `check_request` again.
- `ImportRejected` / `NetworkRejected` expose stable code-only messages, suppressing raw path, URL, iterator/provider exception text and nested causes. No logging or network/DNS call is implemented.

## Bounds and exclusions

Archive names use NFKC normalization, separator canonicalization and casefold collision checks, including implicit directory/file conflicts. Absolute/drive/UNC/device/ADS/traversal names, Windows reserved names with extensions, control/NUL characters, trailing dot/space and special/link/reparse metadata fail closed. Unknown extra metadata is unsupported; only timestamp/UID-GID fields are allowed. First implementation supports STORE/DEFLATE ZIP only; encrypted members, ZIP64, data descriptors, multivolume members, prepended executable archives, other compressors, nested archives and unknown metadata are unsupported. Extension restrictions and small known archive/executable/pickle/VRT signature exclusions do **not** establish content trust or parser safety.

Supplied IPs must all be public, unless an administrator profile explicitly grants an RFC1918 subnet. Loopback/control API, link-local/metadata, multicast, unspecified, reserved, mapped IPv4 and selected IPv6 transition networks remain denied. Profiles cannot grant non-RFC1918 private ranges. Endpoint matching binds exact scheme, hostname and port, refuses userinfo/arbitrary hosts/ambiguous ports, and never returns or logs signed URLs.

All documented quotas in tests are **synthetic fixture policy**, not approved G0 budgets. Cooperative checks cannot interrupt stdlib central-directory parsing within the bounded source buffer, a blocking caller-owned iterator, DNS, connect or socket read. Source byte bounds cap ZIP parser input but do not constitute a native CPU/memory sandbox. Real adapters must enforce interruptible DNS/connect/read timeouts, pin validated resolved IPs to actual connections, recheck each redirect and prove transport behavior; supplied-DNS tests alone do not prevent rebinding. URL-to-asset correspondence is supplied by a trusted provider adapter and is not inferred from URL text.

## TDD and verification

Tests were written/run before implementation. Initial RED logs: [12 storage failures](task-1-storage-red.log), [2 contract failures](task-1-contract-red.log), [7 network failures](task-1-network-red.log), all due to missing intended implementation/contracts. Additional hardening RED logs caught serialization/header injection/ambiguous-port and executable-prefix issues: [network](task-1-network-hardening-red.log), [storage](task-1-storage-hardening-red.log), [descriptor restriction](task-1-zip-features-red.log). Fixes were then checked GREEN. PowerShell RED logs include its stderr wrapper; no credential/customer data is used.

With `$env:PYTHONPATH = 'backend'`, all commands returned exit 0 on 09/11/2026:

| Command | Result/evidence |
| --- | --- |
| `python -m unittest discover -s tests/contracts -v` | **57 pass**, [log](task-1-contract-green.log) (55 original + 2 new) |
| `python -m unittest discover -s tests/storage -v` | **15 pass**, [log](task-1-storage-green.log) |
| `python -m unittest discover -s tests/catalog -v` | **9 pass**, [log](task-1-network-green.log) |
| `python -m unittest discover -s tests/architecture -v` | **2 pass**, [log](task-1-architecture-green.log) |
| `python -m unittest discover -s tests/integration -v` | **14 pass**, [log](task-1-integration-green.log) |
| `python tools/export_contract_schemas.py` then `--check` | Regenerated canonical draft schema; [current](task-1-schema-check.log) |
| `python tools/export_api_client.py --check` | [Current](task-1-client-check.log); HTTP API/client unchanged |

Coverage maps to **offline subsets only**: IMP-01/02 name checks; IMP-03 archive metadata rejection only; IMP-05 actual count/byte/ratio/depth/deadline limits plus forged-size/CRC; IMP-06 corrupt/truncated/cancel failure without writes; IMP-09/11 disabled types/known signatures and no activation. NET-01/02 endpoint/every-hop/header policy, NET-03/04 supplied-address/RFC1918 checks only, NET-05 chunk/total/length/deadline/cancel checks only, NET-06 fixed-identity failure classification and total request budget. Real source bytes and sentinel file hashes/content remain unchanged in positive inspection. No test claims IMP-04 or IMP-07/08/10, actual extraction containment, cleanup/crash recovery, live transport, signed-pack trust or complete security acceptance.

## Exact changed files

- `backend/geoai/contracts/imports.py` (new contracts), `backend/geoai/contracts/__init__.py` (exports/canonical durable registry).
- `backend/geoai/storage/__init__.py`, `backend/geoai/storage/importer.py` (used offline package).
- `backend/geoai/catalog/__init__.py`, `backend/geoai/catalog/policy.py` (used pure policy package).
- `tests/contracts/test_import_contracts.py`, `tests/storage/test_importer_security.py`, `tests/catalog/test_resolver_network_policy.py`.
- `tests/fixtures/contracts/import-policy.json` (small synthetic policy/inventory record; fixture digest placeholders are not provenance from customer bytes).
- `schemas/contracts-v0.1.0.json` (generated, not hand edited).
- This report and `task-1-*.log`, `task-1-file-hashes.json` evidence files in this folder. [Final production/test/schema SHA-256 inventory](task-1-file-hashes.json).

## Handoff/pending

Parent owns tracker/roadmap/spec/security/implementation-gap notes. New canonical policies/inventory are durable draft records, with no wire/API shape change. Do not accept serialized project policy or inventory as native grants, trusted origin, registered assets or permission to activate a pack. No global install/Git/subagent work was performed. Existing unrelated data/work was preserved.

Next integration must still implement staged extraction/native handle identity and race/reparse/hardlink controls; registered external read/version checks; GDAL driver/sidecar confinement; rollback/recovery and transactional asset/model activation; signature/license/runtime trust; real provider adapters/transport/DNS rebinding defense/content validation; and worker/coordinator enforcement. This task enables none of those runtime capabilities and closes no native/security gate.
