"""Check this documentation change; never execute the runtime guide's commands."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
errors = []


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def names(raw):
    return [os.fsdecode(value) for value in raw.split(b"\0") if value]


changed = sorted(set(names(git("diff", "--name-only", "-z", "HEAD"))) |
                 set(names(git("ls-files", "--others", "--exclude-standard", "-z"))))
docs = [ROOT / name for name in changed if name.endswith(".md")]
if any(not name.startswith("Artchitect/") for name in changed):
    errors.append("Change outside authorized Artchitect documentation scope")
baseline = json.loads((EVIDENCE / "protected-baseline.json").read_text(encoding="utf-8"))
changed_protected = [name for name, digest in baseline["files"].items()
                     if not (ROOT / name).is_file() or
                     hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
if changed_protected:
    errors.append({"protected_files_changed": changed_protected})


def anchors(path):
    data = path.read_text(encoding="utf-8", errors="strict")
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', data))
    used = {}
    inside = False
    for line in data.splitlines():
        if re.match(r"^\s*```", line):
            inside = not inside
        if inside:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            heading = re.sub(r"<[^>]+>", "", match[1]).lower()
            slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
            count = used.get(slug, 0)
            result.add(slug if count == 0 else f"{slug}-{count}")
            used[slug] = count + 1
    return result


link_count = anchor_count = table_count = json_count = 0
mermaid = []
for path in docs:
    try:
        data = path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        errors.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
        continue
    label = path.relative_to(ROOT).as_posix()
    if "\ufffd" in data:
        errors.append(f"{label}: replacement character")
    fences = re.findall(r"^\s*```[^\n]*$", data, flags=re.M)
    if len(fences) % 2:
        errors.append(f"{label}: unbalanced code fence")
    for kind, body in re.findall(r"^```(\w+)\s*\n(.*?)^```\s*$", data, re.M | re.S):
        if kind == "json":
            try:
                json.loads(body)
                json_count += 1
            except ValueError as exc:
                errors.append(f"{label}: invalid JSON block: {exc}")
        if kind == "mermaid":
            mermaid.append({"file": label, "kind": body.splitlines()[0]})
    destinations = re.findall(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)", data)
    destinations += re.findall(r"^\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)", data, re.M)
    for destination in destinations:
        destination = destination.strip("<>")
        if urlsplit(destination).scheme or destination.startswith("//"):
            continue
        file_part, _, fragment = destination.partition("#")
        target = (path.parent / unquote(file_part)).resolve() if file_part else path
        link_count += 1
        if not target.exists():
            errors.append(f"{label}: missing target {destination}")
        elif fragment and target.is_file() and target.suffix.lower() == ".md":
            anchor_count += 1
            if unquote(fragment) not in anchors(target):
                errors.append(f"{label}: missing anchor {destination}")
    previous_columns = None
    inside = False
    for line in data.splitlines():
        if re.match(r"^\s*```", line):
            inside = not inside
        if inside or not line.startswith("|"):
            previous_columns = None
            continue
        clean = re.sub(r"`[^`]*`", "code", line)
        columns = len(re.split(r"(?<!\\)\|", clean)) - 2
        if previous_columns is None:
            table_count += 1
        elif columns != previous_columns:
            errors.append(f"{label}: table column mismatch: {line}")
        previous_columns = columns

matrix = (ROOT / "Artchitect/docs/ubuntu-validation-matrix.md").read_text(encoding="utf-8")
ids = re.findall(r"^\| (UB-\d{2}) \|", matrix, re.M)
if ids != [f"UB-{i:02}" for i in range(1, 21)]:
    errors.append("UB matrix must contain exactly UB-01 through UB-20 in order")
ubuntu_diagrams = [item for item in mermaid
                   if item["file"] == "Artchitect/docs/ubuntu-desktop-architecture.md"]
if [item["kind"] for item in ubuntu_diagrams] != ["flowchart TB", "flowchart TD", "sequenceDiagram"]:
    errors.append("Ubuntu architecture must contain its three documented diagrams")
for name in ["adr/ADR-012-ubuntu-desktop.md", "ubuntu-desktop-architecture.md",
             "ubuntu-development-and-packaging.md", "ubuntu-validation-matrix.md"]:
    data = (ROOT / "Artchitect/docs" / name).read_text(encoding="utf-8")
    if "22.04" not in data or "24.04" not in data:
        errors.append(f"{name}: both LTS targets required")

diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True)
if diff.returncode:
    errors.append({"git_diff_check": diff.stdout.decode("utf-8", errors="replace")})
result = {
    "date": "2026-11-10", "timezone": "Asia/Bangkok", "executor": "Windows / PowerShell / Python 3.12",
    "command": "python -X utf8 Artchitect/docs/evidence/ubuntu-2026-11-10/verify-docs.py",
    "status": "pass" if not errors else "fail", "errors": errors,
    "markdown_files": len(docs), "local_links": link_count, "markdown_anchors": anchor_count,
    "tables": table_count, "json_blocks": json_count, "mermaid_text_blocks": mermaid,
    "ubuntu_acceptance_ids": ids, "protected_file_count": len(baseline["files"]),
    "protected_files_changed": changed_protected, "git_diff_check_exit_code": diff.returncode,
    "checked_files": [path.relative_to(ROOT).as_posix() for path in docs],
    "limits": "Documentation only. Mermaid not parsed/rendered. No Linux/Cloud/runtime/native/GIS/model/GPU/installer tests. External URL reachability is not checked by this script."
}
(EVIDENCE / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in result.items()
                  if key not in {"checked_files", "mermaid_text_blocks", "ubuntu_acceptance_ids"}}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
