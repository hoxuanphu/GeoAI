# Independent Task 1 review — 09/11/2026

Scope: offline archive inspection, pure provider policy, canonical contracts and their tests under [review brief](review-brief.md). No production edits, extraction, native I/O, DNS/HTTP requests or activation were performed. Reviewed [task report](task-1-report.md), task brief/plan, SPEC-009, security/worker-resolver/contracts/architecture and implementation gaps. Parent owns status documents.

## Initial verdict: changes requested

Two reproducible P2 defects remain in the bounded offline implementation. Existing tests pass but do not cover these inputs. Neither finding asserts that extraction or native capabilities are enabled.

1. **P2 — validate one complete ZIP envelope, rather than accepting the last central directory.** `backend/geoai/storage/importer.py:151–156` only checks the first signature before delegating structure selection to `zipfile.ZipFile`; the later per-member checks operate on whichever archive the stdlib selects. `archive([("evil.exe", b"MZevil")]) + archive([("a.txt", b"abc")])` is accepted and returns only `a.txt`. Thus an inventory of the entire source silently omits an archive and its forbidden member. A normal ZIP followed by `b"TRAILING SECRET"` is also accepted. Patching EOCD disk-number or central-directory-disk to 1, or either EOCD entry count to 0, is accepted despite unsupported multivolume/invalid-structure claims. Require a consistent, single supported envelope: exact EOCD/comment extent, supported disk fields, matching counts/central-directory bounds, and no unaccounted prefix/local-record gaps or trailing bytes. Keep legal supported ZIP comments and normal archives working. Add byte-level negative fixtures for concatenation, suffix junk, EOCD disk/count inconsistencies, and local/central gaps or overlap.

2. **P2 — Windows reserved device aliases with a space before the extension pass.** `backend/geoai/storage/importer.py:49–51` compares the untrimmed pre-extension stem with `_RESERVED`. ZIP entries `CON .txt`, `NUL .json`, `COM1 .txt` and `LPT9 .json` are accepted and returned as valid paths; `pathlib.PureWindowsPath("CON .txt").is_reserved()` is true on the current Python. Reject reserved basenames after applying the Windows device-name space rule as well as current normalization. Add these variants to the existing Windows-name negative fixtures and retain a valid ordinary-name positive case.

## Reproduction and verification

Probes imported `archive`, `POLICY`, `NOW` from `tests/storage/test_importer_security.py`, constructed `ArchivePolicy(**POLICY)`, then called `inspect_zip(data, policy, inventory_id="inv:test", created_at=NOW)`. EOCD mutations used `bytearray(source)`, `end = source.index(b"PK\x05\x06")`, and `struct.pack_into("<H", altered, end + offset, value)` with `(offset, value)` equal to `(4,1)`, `(6,1)`, `(8,0)`, `(10,0)`. All unexpected acceptances above were reproduced directly, without extracting anything.

Independent runs on Windows/Python 3.12, with `PYTHONPATH=backend`, returned exit 0:

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests/storage -v` | 15 pass |
| `python -m unittest discover -s tests/catalog -v` | 9 pass |
| `python -m unittest discover -s tests/contracts -v` | 57 pass |
| `python -m unittest discover -s tests/architecture -v` | 2 pass |
| `python tools/export_contract_schemas.py --check` | Current |
| `python tools/export_api_client.py --check` | Current |

No additional blocking finding was identified in actual-byte decompression limits, size/CRC verification, immutable inventory, pure endpoint/IP/budget checks, sanitized public error messages, or canonical schema registration. Current tests meaningfully exercise forged-size output, content/extension exclusions, deadlines, failure byte accounting and supplied-address denial. Report boundaries correctly retain blocking iterator/transport enforcement, DNS rebinding, native confinement/extraction/activation and all corresponding acceptance as pending. An extension/signature check still provides no content-trust assertion.

Scoped re-review after the two fixes is pending. This initial review does not approve Task 1 or close SPEC-009/native IMP/NET acceptance.
