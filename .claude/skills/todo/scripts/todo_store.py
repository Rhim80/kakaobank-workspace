#!/usr/bin/env python3
"""Local todo storage shared by Claude Code's todo/todos skills (single writer)."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'wiring/scripts'))
from wiring import inside, need, read_yaml, yaml

CONFIG = '00-system/선언-표면.yaml'
TASK = re.compile(r'^- \[([ xX])\] (.+)$')
MARKER = re.compile(r'<!-- todo:([a-f0-9]{64}) -->')


def configuration(root):
    data = read_yaml(root / CONFIG)
    need(isinstance(data, dict) and data.get('버전') == 1, '표면 선언 버전 오류')
    c = data.get('할일')
    need(isinstance(c, dict), '할일 선언 누락')
    sections = c.get('섹션')
    need(isinstance(sections, dict) and set(sections) == {'오늘', '이번주', '대기', '나중', '수집함'}, '할일 섹션 누락')
    need(all(isinstance(v, str) and v.strip() and '\n' not in v for v in sections.values()), '섹션 이름 오류')
    need(len(set(sections.values())) == len(sections), '섹션 이름 중복')
    route = c.get('새항목라우팅')
    need(isinstance(route, dict) and set(route) == {'high', 'normal', 'low', 'waiting'}, '우선순위 라우팅 누락')
    need(all(v in sections for v in route.values()), '라우팅이 없는 섹션을 가리킵니다')
    need(type(c.get('오래됨일수')) is int and c['오래됨일수'] > 0, '오래됨일수 오류')
    need(c.get('외부동기화') is False, '외부 동기화는 이 킷에서 구현되지 않았습니다')
    active, archive = inside(root, c.get('위치')), inside(root, c.get('완료보관'))
    need(active != archive, '활성 파일과 완료 보관은 달라야 합니다')
    return c, active, archive


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.todo-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def read(path):
    return path.read_text(encoding='utf-8') if path.exists() else ''


def parse(content):
    lines = content.splitlines(keepends=True)
    tasks = []; section = ''; i = 0
    while i < len(lines):
        if lines[i].startswith('## '): section = lines[i][3:].strip()
        match = TASK.match(lines[i].rstrip('\n'))
        if not match or not match[2].strip(): i += 1; continue
        start = i; i += 1
        while i < len(lines) and (lines[i].startswith(('  ', '\t')) or not lines[i].strip()): i += 1
        raw = ''.join(lines[start:i])
        mark = MARKER.search(raw)
        title = re.sub(r'\s*<!--.*?-->\s*', '', match[2]).strip()
        meta = dict(re.findall(r'^  - ([^:\n]+):\s*(.*)$', raw, re.M))
        uid = mark[1] if mark else hashlib.sha256(raw.strip().encode()).hexdigest()
        tasks.append({'id': uid, 'title': title, 'done': match[1].lower() == 'x', 'section': section, 'meta': meta, 'raw': raw, 'start': start, 'end': i})
    return tasks


def clean(value):
    return ' '.join(value.casefold().split())


def insert(content, section, block):
    lines = content.splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.rstrip('\n') == '## ' + section]
    need(len(indices) <= 1, '동일한 섹션이 둘 있습니다: ' + section)
    if not indices:
        return content.rstrip() + '\n\n## ' + section + '\n\n' + block.rstrip() + '\n'
    at = indices[0] + 1
    while at < len(lines) and not lines[at].startswith('## '): at += 1
    return ''.join(lines[:at]).rstrip() + '\n\n' + block.rstrip() + '\n\n' + ''.join(lines[at:])


def add(root, title, priority='normal', project='', source='', due='', key=''):
    c, active, archive = configuration(root)
    for value in [title, project, source, due, key]:
        need(isinstance(value, str) and '\n' not in value and '<!--' not in value, '항목 값은 한 줄로 적습니다')
    need(bool(title.strip()), '할 일 내용이 비었습니다')
    need(priority in c['새항목라우팅'], '알 수 없는 우선순위')
    if source: need(inside(root, source).is_file(), '원본 파일 없음 — 경로를 확인하세요')
    if due: datetime.fromisoformat(due)
    if key: need(re.fullmatch(r'[A-Za-z0-9가-힣_:.-]+', key), '중복 방지 키 형식 오류')
    basis = key or json.dumps([clean(title), source, project, due], ensure_ascii=False)
    uid = hashlib.sha256(basis.encode()).hexdigest()
    active_text, archive_text = read(active), read(archive)
    # A persisted key is authoritative, including after completion.
    for location, content in [('active', active_text), ('archive', archive_text)]:
        for item in parse(content):
            same = item['id'] == uid or (key and item['meta'].get('key') == key)
            # Legacy/local items without explicit occurrence keys also use exact normalized content.
            semantic = not key and not item['meta'].get('key') and [clean(item['title']), item['meta'].get('원본', ''), item['meta'].get('project', ''), item['meta'].get('due', '')] == [clean(title), source, project, due]
            if same or semantic:
                return {'added': False, 'id': item['id'], 'location': location, 'done': item['done']}
    now = datetime.now().astimezone().isoformat(timespec='seconds')
    block = '- [ ] ' + title.strip() + ' <!-- todo:' + uid + ' -->\n'
    if key.startswith('wiring:'):
        need(re.fullmatch(r'wiring:[a-f0-9]{64}:\d+', key), 'wiring 자료id·항목번호 형식 오류')
        block += '  <!-- ' + key + ' -->\n'
    fields = {'added': now, 'priority': priority, 'project': project, '원본': source, 'due': due, 'key': key}
    for name, value in fields.items():
        if value: block += '  - ' + name + ': ' + value + '\n'
    if not active_text.strip():
        active_text = '# Active Todos\n\n' + '\n\n'.join('## ' + s for s in c['섹션'].values()) + '\n'
    section = c['섹션'][c['새항목라우팅'][priority]]
    atomic(active, insert(active_text, section, block))
    return {'added': True, 'id': uid, 'section': section}


def complete(root, uid=None, cleanup=False):
    c, active, archive = configuration(root)
    original = read(active); items = parse(original)
    selected = [t for t in items if (cleanup and t['done']) or (not cleanup and t['id'] == uid)]
    need(cleanup or len(selected) <= 1, '같은 id가 중복되어 있어 먼저 대조해야 합니다')
    archived = read(archive) or '# Completed Todos\n'
    if not selected:
        if not cleanup and any(t['id'] == uid for t in parse(archived)):
            return {'completed': 0, 'already_completed': True}
        need(cleanup, '해당 할 일을 찾지 못했습니다')
    now = datetime.now().astimezone(); ids = {t['id'] for t in parse(archived)}
    for task in selected:
        if task['id'] in ids:
            prior = next(t for t in parse(archived) if t['id'] == task['id'])
            need(prior['title'] == task['title'] and prior['meta'].get('원본') == task['meta'].get('원본'), '완료 보관 내용과 다릅니다 — 제거하지 않았습니다')
            continue
        block = re.sub(r'^- \[[ xX]\]', '- [x]', task['raw'].rstrip(), count=1)
        if not MARKER.search(block): block += '\n  <!-- todo:' + task['id'] + ' -->'
        block += '\n  - completed: ' + now.isoformat(timespec='seconds') + '\n'
        archived = insert(archived, now.strftime('%Y-%m'), block); ids.add(task['id'])
    # Archive first: interruption before active-file update can safely be retried.
    if selected: atomic(archive, archived)
    lines = original.splitlines(keepends=True)
    for task in reversed(selected): del lines[task['start']:task['end']]
    if selected: atomic(active, ''.join(lines))
    return {'completed': len(selected)}


def timestamp(value):
    if not value: return None
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except ValueError: return None


def listing(root, mode='all'):
    c, active, archive = configuration(root)
    rows = []; now = datetime.now(timezone.utc)
    for item in parse(read(active)):
        if item['done']: continue
        meta = item['meta']; source = meta.get('원본'); basis = timestamp(meta.get('updated') or meta.get('added'))
        status = 'none'; changed = None
        if source:
            p = inside(root, source)
            status = 'missing' if not p.is_file() else 'unverified'
            if p.is_file():
                try:
                    result = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', source], cwd=root, capture_output=True, text=True, timeout=5)
                    changed = timestamp(result.stdout.strip()) if result.returncode == 0 else None
                except (OSError, subprocess.TimeoutExpired): changed = None
                if changed:
                    status = 'review' if basis is None or changed > basis else 'current'
                try:
                    dirty = subprocess.run(['git', 'status', '--porcelain', '--', source], cwd=root, capture_output=True, text=True, timeout=5)
                    if dirty.returncode != 0: status = 'unverified'
                    elif dirty.stdout.strip(): status = 'review'
                except (OSError, subprocess.TimeoutExpired): status = 'unverified'
        effective = max(t for t in [basis, changed] if t) if basis or changed else None
        age = (now - effective).days if effective else None
        row = {k: item[k] for k in ['id', 'title', 'section', 'meta']}
        row.update(source_status=status, age_days=age)
        if mode == 'today' and item['section'] != c['섹션']['오늘']: continue
        if mode == 'overdue' and not (status in ['missing', 'review', 'unverified'] or (age is not None and age >= c['오래됨일수'])): continue
        rows.append(row)
    if mode == 'stats':
        return {'total': len(rows), 'sections': {s: sum(t['section'] == s for t in rows) for s in set(c['섹션'].values()) | {t['section'] for t in rows}}}
    if mode == 'project':
        return {p: [t for t in rows if t['meta'].get('project', 'Unassigned') == p] for p in sorted({t['meta'].get('project', 'Unassigned') for t in rows})}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate')
    p = commands.add_parser('add'); p.add_argument('title')
    for field, default in [('priority','normal'),('project',''),('source',''),('due',''),('key','')]: p.add_argument('--'+field, default=default)
    p = commands.add_parser('list'); p.add_argument('--mode', choices=['all','today','project','overdue','stats'], default='all')
    p = commands.add_parser('done'); p.add_argument('id')
    commands.add_parser('cleanup')
    args = parser.parse_args(); root = args.root.resolve()
    try:
        need((root/'CLAUDE.md').is_file(), '워크스페이스 루트가 아닙니다')
        if args.command == 'validate': configuration(root); output = {'valid': True}
        elif args.command == 'add': output = add(root, args.title, args.priority, args.project, args.source, args.due, args.key)
        elif args.command == 'list': output = listing(root, args.mode)
        else: output = complete(root, getattr(args, 'id', None), args.command == 'cleanup')
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError) as exc:
        print('오류: '+str(exc), file=sys.stderr); return 1


if __name__ == '__main__': sys.exit(main())
