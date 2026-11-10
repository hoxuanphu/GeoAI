"""Check planning artifacts without executing the planned product tests."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import ast
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DOCS = ROOT / 'Artchitect/docs'
PLANS = DOCS / 'superpowers/plans'
PARTS = PLANS / '2026-11-10-ubuntu-foundation'
BASELINE = json.loads((HERE / 'baseline.json').read_text(encoding='utf-8-sig'))
ALLOWED_EDITS = {f'Artchitect/docs/{name}' for name in (
    'README.md', 'platforms/README.md', 'specs/README.md',
    'specs/010-ubuntu-foundation.md', 'specs/000-documentation-baseline.md',
    'roadmap.md', 'task-tracker.md')}
ERRORS = []
INLINE = re.compile(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s)\n]+)(?:\s+["\'][^\n]*?["\'])?\)')
REFERENCE = re.compile(r'^\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)')
CODE = re.compile(r'(`+)(.*?)\1')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})(.*)$')


def read(path):
    return path.read_text(encoding='utf-8-sig', errors='strict')


def digest(path):
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
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*\s*$', line)
        if match and not fence:
            title = re.sub(r'<[^>]+>', '', match[1]).lower()
            slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
            count = used.get(slug, 0)
            result.add(slug if count == 0 else f'{slug}-{count}')
            used[slug] = count + 1
    return result


files = sorted((ROOT / 'Artchitect').rglob('*.md')) + [ROOT / 'README.md', ROOT / 'AGENTS.md']
counts = dict(markdown_files=len(files), local_links=0, anchors_checked=0,
              tables=0, fenced_blocks=0, json_blocks=0, plan_python_snippets_parsed=0)
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
    language = ''
    block = []
    width = None
    for number, line in enumerate(content.splitlines(), 1):
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker[1]
                language = marker[2].strip().lower()
                block = []
                counts['fenced_blocks'] += 1
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                try:
                    if language == 'json':
                        counts['json_blocks'] += 1
                        json.loads('\n'.join(block))
                    elif language == 'python' and path.is_relative_to(PLANS):
                        ast.parse('\n'.join(block))
                        counts['plan_python_snippets_parsed'] += 1
                except (ValueError, SyntaxError) as exc:
                    ERRORS.append(f'{label}:{number}: invalid {language} snippet: {exc}')
                fence = None
            else:
                block.append(line)
            width = None
            continue
        if fence:
            block.append(line)
            continue
        if line.lstrip().startswith('|') and line.rstrip().endswith('|'):
            cells = re.split(r'(?<!\\)\|', CODE.sub('CODE', line).strip().strip('|'))
            if width is None:
                width = len(cells)
                counts['tables'] += 1
            elif len(cells) != width:
                ERRORS.append(f'{label}:{number}: table has {len(cells)} columns; expected {width}')
        else:
            width = None
        clean = CODE.sub('', line)
        destinations = [match[1] for match in INLINE.finditer(clean)]
        match = REFERENCE.match(clean)
        if match:
            destinations.append(match[1])
        for destination in destinations:
            raw = destination.strip('<>')
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
            counts['local_links'] += 1
            if not target.exists():
                ERRORS.append(f'{label}:{number}: missing link {raw}')
            elif parts.fragment and target.is_file() and target.suffix.lower() == '.md':
                counts['anchors_checked'] += 1
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(read(target))
                if unquote(parts.fragment) not in anchor_cache[target]:
                    ERRORS.append(f'{label}:{number}: missing anchor {raw}')
    if fence:
        ERRORS.append(f'{label}: unclosed code fence')

expected = [f'{letter}-{number:02}'
            for letter, size in [('A', 5), ('B', 7), ('C', 4), ('D', 5), ('E', 5)]
            for number in range(1, size + 1)]
part_files = sorted(PARTS.glob('[0-9][0-9]-*.md'))
task_ids = []
step_count = 0
for path in [PLANS / '2026-11-10-ubuntu-foundation.md', *part_files]:
    content = read(path)
    for required in ['For agentic workers:', '**Goal:**', '**Architecture:**', '**Tech Stack:**',
                     '**Spec:**', '## Global Constraints', '## Review Focus']:
        if required not in content:
            ERRORS.append(f'{path.name}: missing plan header/section {required}')
    if re.search(r'^- \[[xX]\]', content, re.M):
        ERRORS.append(f'{path.name}: implementation checkbox already completed')
    tasks = re.split(r'^### Task ([A-E]-\d{2}):[^\n]*\n', content, flags=re.M)
    for index in range(1, len(tasks), 2):
        task_id, task_body = tasks[index:index + 2]
        task_ids.append(task_id)
        if '**Files:**' not in task_body or '**Interfaces:**' not in task_body:
            ERRORS.append(f'{task_id}: missing Files/Interfaces')
        steps = re.findall(r'^- \[ \] \*\*Step (\d+):', task_body, re.M)
        step_count += len(steps)
        if len(steps) < 5 or list(map(int, steps)) != list(range(1, len(steps) + 1)):
            ERRORS.append(f'{task_id}: incomplete or unordered steps {steps}')
if len(part_files) != 5 or task_ids != expected:
    ERRORS.append(f'Expected five plans and 26 unique ordered tasks; got {task_ids}')
main = read(PLANS / '2026-11-10-ubuntu-foundation.md')
suites = re.findall(r'^\| (010-T\d{2}) \|', main, re.M)
if suites != [f'010-T{i:02}' for i in range(1, 10)]:
    ERRORS.append(f'Incomplete spec-suite coverage: {suites}')
tracker = read(DOCS / 'task-tracker.md')
milestones = re.findall(r'^- \[([ xX])\] (010\.[123])\b', tracker, re.M)
if milestones != [(' ', f'010.{i}') for i in range(1, 4)]:
    ERRORS.append(f'Runtime milestones changed: {milestones}')
catalog = read(PARTS / 'interfaces-and-handoff.md')
for required in ['## 3. Mẫu prompt', '## 4. Mẫu handoff', '## 5. Quy tắc resume',
                 'runtime-test-harness', 'FoundationFixture', 'API child']:
    if required not in catalog:
        ERRORS.append(f'Missing implementer guidance: {required}')

protected = {}
changed = []
for name, expected_hash in BASELINE['files'].items():
    path = ROOT / name
    if not path.is_file():
        ERRORS.append(f'Pre-existing file removed: {name}')
        continue
    unchanged = digest(path) == expected_hash
    if name not in ALLOWED_EDITS:
        protected[name] = unchanged
        if not unchanged:
            ERRORS.append(f'Protected pre-existing file changed: {name}')
    elif not unchanged:
        changed.append(name)
inventory = subprocess.run(['git', 'ls-files', '-c', '-o', '--exclude-standard', '-z'],
                           cwd=ROOT, capture_output=True, check=True)
current = set(inventory.stdout.decode('utf-8', errors='strict').split('\0')) - {''}
new_files = sorted(current - set(BASELINE['files']))
for name in new_files:
    if not (name.startswith('Artchitect/docs/superpowers/plans/') and name.endswith('.md') or
            name.startswith('Artchitect/docs/evidence/ubuntu-plan-2026-11-10/')):
        ERRORS.append(f'New file outside planning scope: {name}')
diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True)
if diff.returncode:
    ERRORS.append({'git_diff_check': (diff.stdout + diff.stderr).decode('utf-8', errors='replace')})
results = {
    'date': '2026-11-10', 'timezone': 'Asia/Bangkok', 'scope': 'implementation planning documents only',
    'command': 'python -X utf8 Artchitect/docs/evidence/ubuntu-plan-2026-11-10/verify.py',
    'status': 'pass' if not ERRORS else 'fail', 'errors': ERRORS, **counts,
    'subplans': len(part_files), 'tasks': len(task_ids), 'task_ids': task_ids,
    'implementation_steps_unchecked': step_count, 'spec_suite_ids': suites,
    'runtime_milestones_unchecked': milestones == [(' ', f'010.{i}') for i in range(1, 4)],
    'baseline_files': len(BASELINE['files']), 'baseline_sha256': digest(HERE / 'baseline.json'),
    'protected_files': len(protected), 'protected_files_unchanged': sum(protected.values()),
    'modified_markdown': sorted(changed), 'new_files': new_files,
    'git_diff_check_exit_code': diff.returncode, 'product_runtime_checks_run': False,
    'limits': 'Local Markdown checks, Python snippet syntax and SHA-256 only; no planned test execution, Rust compilation, external link check, Mermaid rendering, dependency resolve, Linux/Cloud/DB/GIS/model/installer or gate validation.',
}
(HERE / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, ensure_ascii=False, indent=2))
raise SystemExit(1 if ERRORS else 0)
