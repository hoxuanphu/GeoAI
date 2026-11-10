"""Verify documentation organization without changing historical results."""

from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit
import hashlib
import json
import os
import re
import subprocess


ROOT = Path(__file__).resolve().parents[4]
DOCS = ROOT / "Artchitect/docs"
HERE = Path(__file__).resolve().parent
mapping = json.loads((HERE / "moves.json").read_text(encoding="utf-8-sig"))
baseline = json.loads((HERE / "baseline.json").read_text(encoding="utf-8-sig"))
inverse = {(DOCS / new).resolve(): (DOCS / old).resolve() for old, new in mapping.items()}
errors = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def matches_baseline(text, expected):
    # Original links may leave Unicode literal while escaping spaces; relocation
    # URI-encodes both spellings. Compare both representations and line endings.
    literal_unicode = re.sub(
        r"(?:%[0-9A-Fa-f]{2})+",
        lambda match: "".join(char if ord(char) > 127 else quote(char, safe="")
                              for char in unquote(match.group())),
        text,
    )
    return expected in {digest(candidate.encode("utf-8"))
                        for variant in (text, literal_unicode)
                        for candidate in (variant, variant.replace("\n", "\r\n"))}


def convert(destination, source, original_source):
    angle = destination.startswith("<") and destination.endswith(">")
    raw = destination[1:-1] if angle else destination
    parts = urlsplit(raw)
    if parts.scheme or parts.netloc or not parts.path:
        return destination
    target = (source.parent / unquote(parts.path)).resolve()
    original_target = inverse.get(target, target)
    if source == original_source and target == original_target:
        return destination
    relative = os.path.relpath(original_target, original_source.parent).replace("\\", "/")
    result = urlunsplit(("", "", quote(relative, safe="/-._~"), parts.query, parts.fragment))
    return f"<{result}>" if angle else result


inline = re.compile(r'(!?\[[^\]\n]*\]\()(<[^>\n]+>|[^\s)\n]+)((?:\s+["\'][^\n]*?["\'])?\))')
reference = re.compile(r'^(\[[^\]\n]+\]:\s*)(<[^>\n]+>|\S+)(.*)$')


def reverse_links(content, source, original_source):
    result = []
    in_fence = False
    for line in content.splitlines(keepends=True):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            result.append(line)
            continue
        if not in_fence:
            line = inline.sub(lambda m: m[1] + convert(m[2], source, original_source) + m[3], line)
            match = reference.match(line.rstrip("\r\n"))
            if match:
                eol = line[len(line.rstrip("\r\n")):]
                line = match[1] + convert(match[2], source, original_source) + match[3] + eol
        result.append(line)
    return "".join(result)


for old, new in mapping.items():
    oldpath = DOCS / old
    newpath = DOCS / new
    key = oldpath.relative_to(ROOT).as_posix()
    if not oldpath.is_file() or not newpath.is_file():
        errors.append(f"Missing original compatibility page or moved document: {old} -> {new}")
        continue
    if "đường dẫn tương thích" not in oldpath.read_text(encoding="utf-8"):
        errors.append(f"Missing compatibility marker: {old}")
    restored = reverse_links(newpath.read_text(encoding="utf-8"), newpath.resolve(), oldpath.resolve())
    if not matches_baseline(restored, baseline[key]):
        errors.append(f"Moved document differs from baseline beyond link relocation: {new}")

rewritten_links_only = 0
edited_navigation = {"Artchitect/docs/README.md", "Artchitect/docs/roadmap.md",
                     "Artchitect/docs/task-tracker.md", "Artchitect/docs/specs/000-documentation-baseline.md"}
old_documents = {(DOCS / old).relative_to(ROOT).as_posix() for old in mapping}
for name, expected in baseline.items():
    if (not name.endswith(".md") or name.startswith("Artchitect/docs/evidence/") or
            name in edited_navigation or name in old_documents):
        continue
    path = ROOT / name
    if not path.is_file():
        errors.append(f"Pre-existing Markdown file missing: {name}")
        continue
    if digest(path.read_bytes()) != expected:
        restored = reverse_links(path.read_text(encoding="utf-8"), path.resolve(), path.resolve())
        if not matches_baseline(restored, expected):
            errors.append(f"Markdown differs from baseline beyond link relocation: {name}")
        else:
            rewritten_links_only += 1

protected = {}
for name, expected in baseline.items():
    if name.endswith(".md") and not name.startswith("Artchitect/docs/evidence/") and name != "AGENTS.md":
        continue
    path = ROOT / name
    protected[name] = path.is_file() and digest(path.read_bytes()) == expected
    if not protected[name]:
        errors.append(f"Protected file changed or missing: {name}")

required = ["roadmap.md", "task-tracker.md", "architecture.md", "contracts.md", "domain-rules.md",
            "prithvi-profile.md", "ipc-protocol.md", "worker-resolver.md", "importer-resolver-security.md",
            "physical-models.md", "adr/README.md", "adr/ADR-011-local-execution-owner.md",
            "specs/README.md", "specs/003-desktop-shell.md", "specs/004-jobs-and-publish.md",
            "specs/008-training-evaluation-model-pack.md", "specs/009-importer-worker-resolver.md"]
for name in required:
    path = DOCS / name
    if not path.is_file() or "đường dẫn tương thích" in path.read_text(encoding="utf-8"):
        errors.append(f"AGENTS required document missing or replaced by compatibility page: {name}")


def anchors(path):
    data = path.read_text(encoding="utf-8-sig", errors="strict")
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', data))
    used = {}
    inside = False
    for line in data.splitlines():
        if re.match(r"^\s*```", line):
            inside = not inside
            continue
        if inside:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"<[^>]+>", "", match[1]).lower()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        count = used.get(slug, 0)
        result.add(slug if count == 0 else f"{slug}-{count}")
        used[slug] = count + 1
    return result


files = sorted((ROOT / "Artchitect").rglob("*.md")) + [ROOT / "README.md", ROOT / "AGENTS.md"]
anchor_cache = {}
links = anchor_checks = 0
for path in files:
    label = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_text(encoding="utf-8-sig", errors="strict")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{label}: {exc}")
        continue
    if "\ufffd" in text:
        errors.append(f"{label}: replacement character")
    inside = False
    for line in text.splitlines():
        if re.match(r"^\s*```", line):
            inside = not inside
            continue
        if inside:
            continue
        destinations = [m[2] for m in inline.finditer(line)]
        match = reference.match(line)
        if match:
            destinations.append(match[2])
        for destination in destinations:
            raw = destination.strip("<>")
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
            links += 1
            if not target.exists():
                errors.append(f"{label}: missing link {raw}")
            elif parts.fragment and target.is_file() and target.suffix.lower() == ".md":
                anchor_checks += 1
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(target)
                if unquote(parts.fragment) not in anchor_cache[target]:
                    errors.append(f"{label}: missing anchor {raw}")
    if inside:
        errors.append(f"{label}: unbalanced code fence")

diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True)
if diff.returncode:
    errors.append({"git_diff_check": diff.stdout.decode("utf-8", errors="replace")})
results = {
    "date": "2026-11-10", "timezone": "Asia/Bangkok", "scope": "documentation organization",
    "command": "python -X utf8 Artchitect/docs/evidence/docs-organization-2026-11-10/verify.py",
    "status": "pass" if not errors else "fail", "errors": errors,
    "moved_documents": len(mapping), "required_agents_documents": len(required),
    "preexisting_markdown_rewritten_links_only": rewritten_links_only,
    "protected_files": len(protected), "protected_files_unchanged": sum(protected.values()),
    "markdown_files": len(files), "local_links": links, "anchors_checked": anchor_checks,
    "git_diff_check_exit_code": diff.returncode,
    "limits": "Markdown structure and SHA-256 only; no Mermaid rendering, external link, Linux, runtime, model, installer, or gate validation."
}
(HERE / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
