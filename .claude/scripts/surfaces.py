#!/usr/bin/env python3
"""Resolve declared workspace surfaces; never fall back to another workspace."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/todo/scripts'))
from todo_store import configuration
from wiring import inside, need, read_yaml, yaml


def resolve(root, day=None):
    root = Path(root).resolve()
    day = day or date.today()
    todo, active, archive = configuration(root)
    c = read_yaml(root / '00-system/선언-표면.yaml')
    for group in ['하루', '주간', '진행', '위키']:
        need(isinstance(c.get(group), dict), group + ' 선언 누락')
    for group, key in [('하루','위치'), ('하루','템플릿'), ('주간','위치'), ('진행','템플릿'), ('위키','위치')]:
        inside(root, c[group].get(key))
    roots = c['진행'].get('루트')
    need(isinstance(roots, list) and bool(roots), '진행 루트 누락')
    for item in roots: inside(root, item)
    filename = c['진행'].get('파일명')
    need(isinstance(filename, str) and Path(filename).name == filename and filename.endswith('.md'), '진행 파일명 오류')
    section = c['하루'].get('완료섹션')
    need(isinstance(section, str) and section.strip() and '\n' not in section, '하루 완료섹션 오류')
    need(type(c['하루'].get('캘린더조회')) is bool, '캘린더조회는 true/false')
    for group in ['하루', '진행']:
        need(inside(root, c[group]['템플릿']).is_file(), group + ' 템플릿 없음')
    for filename in ['SCHEMA.md', 'index.md', 'log.md']:
        need(inside(root, c['위키']['위치'] + '/' + filename).is_file(), '위키 시드 없음: ' + filename)
    template = inside(root, c['하루']['템플릿']).read_text(encoding='utf-8')
    need('## ' + section in template.splitlines(), '하루 완료섹션과 템플릿이 다릅니다')
    monday = day - timedelta(days=day.weekday())
    iso = day.isocalendar()
    def rel(path): return str(path.relative_to(root))
    return {'선언': c, '오늘': day.isoformat(), '요일': '월화수목금토일'[day.weekday()] + '요일',
            '하루파일': rel(inside(root, c['하루']['위치'] + '/' + day.strftime('%Y-%m/%Y-%m-%d.md'))),
            '주간파일': rel(inside(root, c['주간']['위치'] + '/' + f'{iso[0]}-W{iso[1]:02d}.md')),
            '주간시작': monday.isoformat(), '주간끝': (monday + timedelta(days=6)).isoformat(),
            '할일파일': rel(active), '완료보관': rel(archive)}


def daily(root, values):
    target = inside(root, values['하루파일'])
    if target.is_file(): return {'created': False, 'path': values['하루파일']}
    c = values['선언']['하루']
    content = inside(root, c['템플릿']).read_text(encoding='utf-8')
    content = content.replace('YYYY-MM-DD', values['오늘']).replace('(요일)', '(' + values['요일'] + ')')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as f: f.write(content)
    return {'created': True, 'path': values['하루파일']}


def progress(root, values, changed):
    path = inside(root, changed)
    targets = set()
    config = values['선언']['진행']
    for parent in path.parents:
        if parent == root: break
        for base in config['루트']:
            basepath = inside(root, base)
            if basepath in parent.parents or parent == basepath:
                candidate = parent / config['파일명']
                if candidate.is_file(): targets.add(str(candidate.relative_to(root)))
    # Wiring may explicitly name a nonstandard record file. That declaration wins.
    wiring_file = root / '00-system/wiring/선언.yaml'
    if wiring_file.is_file():
        wiring = read_yaml(wiring_file)
        for stream in wiring.get('줄기', []):
            record = stream.get('기록')
            if record:
                recordpath = inside(root, record)
                if path == recordpath or recordpath.parent in path.parents:
                    need(recordpath.is_file(), '선언된 줄기 기록 없음: ' + record)
                    targets.add(record)
    return sorted(targets)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--date', type=date.fromisoformat)
    p.add_argument('command', choices=['resolve', 'daily', 'progress'])
    p.add_argument('changed', nargs='?')
    args = p.parse_args(); root = args.root.resolve()
    try:
        need((root / 'CLAUDE.md').is_file(), '워크스페이스 루트가 아닙니다')
        values = resolve(root, args.date)
        if args.command == 'daily': result = daily(root, values)
        elif args.command == 'progress':
            need(bool(args.changed), '변경 파일 경로가 필요합니다')
            result = progress(root, values, args.changed)
        else: result = values
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError) as exc:
        print('오류: ' + str(exc), file=sys.stderr); return 1

if __name__ == '__main__': sys.exit(main())
