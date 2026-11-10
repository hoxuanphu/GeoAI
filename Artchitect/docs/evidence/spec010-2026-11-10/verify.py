"""Check the SPEC-010 documentation handoff; do not run product/runtime tests."""

from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import subprocess


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DOCS = ROOT / "Artchitect/docs"
BASELINE = json.loads((HERE / "baseline.json").read_text(encoding="utf-8-sig"))
ERRORS = []
INLINE = re.compile(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s)\n]+)(?:\s+["\'][^\n]*?["\'])?\)')
REFERENCE = re.compile(r'^\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)')
CODE_SPAN = re.compile(r'(`+)(.*?)\1')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})(.*)$')


def read(path):
    return path.read_text(encoding="utf-8-sig", errors="strict")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anchors(content):
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', content))
    used = {}
    fence = None
    for line in content.splitlines():
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r'^#{1,6}\s+(.+?)\s*#*\s*$', line)
        if heading:
            label = re.sub(r'<[^>]+>', '', heading[1]).lower()
            slug = re.sub(r'[^\w\- ]', '', label).replace(' ', '-')
            count = used.get(slug, 0)
            result.add(slug if count == 0 else f'{slug}-{count}')
            used[slug] = count + 1
    return result


def table_cells(line):
    # Markdown code spans may contain literal |, e.g. syscall flags/unions.
    clean = CODE_SPAN.sub('CODE', line).strip().strip('|')
    return re.split(r'(?<!\\)\|', clean)


files = sorted((ROOT / 'Artchitect').rglob('*.md')) + [ROOT / 'README.md', ROOT / 'AGENTS.md']
counts = dict(markdown_files=len(files), local_links=0, anchors_checked=0,
              tables=0, fenced_blocks=0, json_blocks=0)
anchor_cache = {}
for path in files:
    label = path.relative_to(ROOT).as_posix()
    try:
        content = read(path)
    except (OSError, UnicodeError) as exc:
        ERRORS.append(f'{label}: UTF-8 read failed: {exc}')
        continue
    if '\ufffd' in content:
        ERRORS.append(f'{label}: replacement character')
    fence = None
    block_language = ''
    block_lines = []
    table_width = None
    for number, line in enumerate(content.splitlines(), 1):
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker[1]
                block_language = marker[2].strip().lower()
                block_lines = []
                counts['fenced_blocks'] += 1
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                if block_language == 'json':
                    counts['json_blocks'] += 1
                    try:
                        json.loads('\n'.join(block_lines))
                    except ValueError as exc:
                        ERRORS.append(f'{label}:{number}: invalid JSON example: {exc}')
                fence = None
            else:
                block_lines.append(line)
            table_width = None
            continue
        if fence:
            block_lines.append(line)
            continue
        if line.lstrip().startswith('|') and line.rstrip().endswith('|'):
            cells = table_cells(line)
            if table_width is None:
                table_width = len(cells)
                counts['tables'] += 1
            elif len(cells) != table_width:
                ERRORS.append(f'{label}:{number}: table width {len(cells)} != {table_width}')
        else:
            table_width = None
        clean = CODE_SPAN.sub('', line)
        destinations = [match[1] for match in INLINE.finditer(clean)]
        reference = REFERENCE.match(clean)
        if reference:
            destinations.append(reference[1])
        for destination in destinations:
            raw = destination.strip('<>')
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
            counts['local_links'] += 1
            if not target.exists():
                ERRORS.append(f'{label}:{number}: missing local link {raw}')
            elif parts.fragment and target.is_file() and target.suffix.lower() == '.md':
                counts['anchors_checked'] += 1
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(read(target))
                if unquote(parts.fragment) not in anchor_cache[target]:
                    ERRORS.append(f'{label}:{number}: missing anchor {raw}')
    if fence:
        ERRORS.append(f'{label}: unclosed {fence} fence')

spec = read(DOCS / 'specs/010-ubuntu-foundation.md')
tracker = read(DOCS / 'task-tracker.md')
profile = read(DOCS / 'platforms/ubuntu/ubuntu-native-profile.md')
suite_ids = re.findall(r'^\| (010-T\d{2}) \|', spec, flags=re.M)
expected_ids = [f'010-T{i:02}' for i in range(1, 10)]
if suite_ids != expected_ids:
    ERRORS.append(f'SPEC-010 suite IDs not unique/ordered/complete: {suite_ids}')
milestones = re.findall(r'^- \[([ xX])\] (010\.[123])\b', tracker, flags=re.M)
if milestones != [(' ', f'010.{i}') for i in range(1, 4)]:
    ERRORS.append(f'Runtime milestones must remain unchecked: {milestones}')
required = ['specs/010-ubuntu-foundation.md',
            'platforms/ubuntu/ubuntu-native-profile.md',
            'platforms/ubuntu/ubuntu-adapter-interfaces.md']
for name in required:
    if not (DOCS / name).is_file():
        ERRORS.append(f'Missing required SPEC-010 document: {name}')
index = read(DOCS / 'specs/README.md')
if '(010-ubuntu-foundation.md)' not in index:
    ERRORS.append('SPEC index does not link to SPEC-010')
if 'PRIVATE_NATIVE_MODELS' not in profile or 'dự kiến' not in profile:
    ERRORS.append('Ledger must be documented as a proposed private model')
native_model = ROOT / 'backend/geoai/contracts/native.py'
if native_model.exists():
    ERRORS.append('Proposed product ledger source unexpectedly exists in docs-only task')

protected = {}
changed_markdown = []
for name, expected in BASELINE['files'].items():
    path = ROOT / name
    if not path.is_file():
        ERRORS.append(f'Pre-existing file removed: {name}')
        continue
    is_protected = (not name.endswith('.md') or
                    name.startswith('Artchitect/docs/evidence/') or
                    not name.startswith('Artchitect/'))
    unchanged = sha256(path) == expected
    if is_protected:
        protected[name] = unchanged
        if not unchanged:
            ERRORS.append(f'Protected file changed: {name}')
    elif not unchanged:
        changed_markdown.append(name)

inventory = subprocess.run(['git', 'ls-files', '-c', '-o', '--exclude-standard', '-z'],
                           cwd=ROOT, capture_output=True, check=True)
current = set(inventory.stdout.decode('utf-8', errors='strict').split('\0')) - {''}
new_files = sorted(current - set(BASELINE['files']))
allowed_evidence = HERE.relative_to(ROOT).as_posix() + '/'
for name in new_files:
    if not (name.startswith(allowed_evidence) or
            (name.startswith('Artchitect/') and name.endswith('.md'))):
        ERRORS.append(f'New file outside documentation scope: {name}')

diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True)
if diff.returncode:
    ERRORS.append({'git_diff_check': (diff.stdout + diff.stderr).decode('utf-8', errors='replace')})

results = {
    'date': '2026-11-10', 'timezone': 'Asia/Bangkok',
    'scope': 'SPEC-010 documentation only',
    'command': 'python -X utf8 Artchitect/docs/evidence/spec010-2026-11-10/verify.py',
    'status': 'pass' if not ERRORS else 'fail', 'errors': ERRORS, **counts,
    'baseline_files': len(BASELINE['files']),
    'baseline_sha256': sha256(HERE / 'baseline.json'),
    'protected_files': len(protected), 'protected_files_unchanged': sum(protected.values()),
    'modified_markdown': sorted(changed_markdown), 'new_files': new_files,
    'suite_ids': suite_ids, 'runtime_milestones_unchecked': len(milestones) == 3 and all(m[0] == ' ' for m in milestones),
    'git_diff_check_exit_code': diff.returncode,
    'product_runtime_checks_run': False,
    'limits': 'UTF-8, Markdown structure, local links/anchors, specification coverage and SHA-256 only; no external URL checks, Mermaid rendering, native/Linux/DB/GIS/model/installer or gate validation.',
}
(HERE / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, ensure_ascii=False, indent=2))
raise SystemExit(1 if ERRORS else 0)
