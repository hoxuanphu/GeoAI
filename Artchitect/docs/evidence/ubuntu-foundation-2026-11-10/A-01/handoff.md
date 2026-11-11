# A-01 ? b?n giao t?ng ph?n, 10/11/2026

Tr?ng th?i: **partial**, ch?a ho?n t?t A-01 ho?c m?c 010.1. Baseline commit `3aade2b`, worktree s?ch tr??c thay ??i; Windows Python 3.12.4. Worktree nh?nh `codex/ubuntu-foundation`.

?? t?ch `NativeIdentity` v? `StorageIOError` sang `backend/geoai/storage/native_io.py`; `windows_io` re-export ??ng c?ng object. Ch?a c? protocol, registration, WindowsIOFactory, deadline hay external reader. Ch?a d?ng k?t qu? n?y l?m ch?ng c? Linux native.

TDD: `python -m unittest discover -s tests/storage -p test_native_factory.py -v` ban ??u l?i `ModuleNotFoundError: geoai.storage.native_io`, sau thay ??i 1 test pass ([log](shared-types.log)). Windows: `python -m unittest discover -s tests/storage -p test_windows_io.py -v`, 7 pass, 0 skip ([log](windows-io.log)). Contracts: `python -m unittest discover -s tests/contracts -v`, 58 pass ([log](contracts.log)); `PYTHONPATH=backend`.

Ruling c?n gi?i quy?t trong A-01: catalog ghi `StorageIOError(RuntimeError)`, implementation Windows hi?n h?u k? th?a `ValueError`; t?m gi? base c? ?? kh?ng thay compatibility khi m?i t?ch type. C?n ki?m tra to?n b? catch v? quy?t ??nh theo spec tr??c ho?n th?nh adapter; n?u gi? kh?c catalog ph?i ghi r?. Kh?ng c? ch?ng c? factory authorization hay deadline.

M?i tr??ng WSL ki?m ???c Ubuntu 22.04.1, Python 3.10.12, checkout `/mnt/c` d?ng v9fs v? `systemctl --user is-system-running` b?o offline. Ch?a ph?i executor theo profile Python 3.12, ext4, user manager; ch?a ki?m Ubuntu 24.04, Rust, native lifecycle, process/SQLite. Chu?n b? executor h?p l?; kh?ng d?ng c?c ki?m tr?n ?? ??ng 010.1?010.3.

Ti?p t?c A-01 t?i Step 1: th?m ki?m registry root gi?, purpose, root ??ng, strong references v? monotonic deadline; tri?n khai protocols/factory v? ch?y regression theo plan tr??c A-02. C?c task A-02?E-05 ch?a b?t ??u.

Ng?y 11/11/2026: theo y?u c?u ng??i d?ng, chuy?n c?c thay ??i ch?a commit t? worktree `codex/ubuntu-foundation` sang workspace nh?nh `feat/ubuntu-installer`; gi? nguy?n thay ??i `AGENTS.md` c? s?n. Ch?y l?i test shared types 1/1 v? Windows I/O 7/7 pass t?i workspace ch?nh. C?c m?c c?n m? nh? tr?n.

??nh ch?nh b?ng ch?ng: log contracts ???c l?u ng?y 10/11 trong worktree ri?ng th?c t? c? 1 l?i stale OpenAPI; [log g?c](contracts-worktree-failure.log). M?nh ?? 58 pass ? tr?n ch? ??ng v?i l?n ki?m baseline workspace ch?nh tr??c ??, kh?ng ??ng v?i log worktree g?c. Ng?y 11/11 ch?y l?i t?i workspace ch?nh: 58/58 pass trong [log hi?n t?i](contracts.log).
