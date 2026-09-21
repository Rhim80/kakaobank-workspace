#!/usr/bin/env python3
"""Validate one wiring declaration; preserve raw inputs and resumable work state.

No external calls or automatic approval. Python 3.9+. PyYAML is used from the system if
installed, otherwise from ./_vendor (pure-python copy, MIT) — no package install needed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / '_vendor'))
    import yaml

BASE = '00-system/wiring/'
DECL = BASE + '선언.yaml'
STATE = BASE + '실행상태.yaml'
PROPOSALS = BASE + '제안/'
DROP = '00-inbox/drop/'          # 직접 넣기: 본인이 파일을 두는 곳. intake가 원본함으로 등록·이동한다
STAGES = ['줄기', '길확인', '병목', '깔기', '한바퀴']
STATES = ['신규', '승인대기', '승인됨', '반영완료', '버림']
TRANSITIONS = {'신규': ['승인대기'], '승인대기': ['승인됨', '버림'], '승인됨': ['반영완료']}
RECORD_ROOTS = ['10-projects', '20-operations']
PLACEHOLDER = re.compile(r'<[^>]+>|\{\{|YOUR_|\.\.\.|…')
STORED_NAME = re.compile(r'^[0-9a-f]{64}\.md$')
SECRET = re.compile(r'(?i)(bearer|token|key|secret|password|authorization)([=: ]+).*')  # 낱말 뒤는 줄 끝까지 가린다
SKIP_DIRS = {'.claude', '.git', '00-inbox', '00-system', 'node_modules', '.venv', '90-archive'}  # 반영 표식은 기록·할 일·노트에만 유효


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError('YAML 키는 중복 없는 문자열이어야 합니다')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_yaml(path):
    return yaml.load(path.read_text(encoding='utf-8'), Loader=UniqueLoader)


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.wiring-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def inside(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('워크스페이스 상대 경로가 필요합니다')
    p = (root / name).resolve()
    if p == root or root not in p.parents:
        raise ValueError('워크스페이스 밖 경로는 허용하지 않습니다')
    return p


def need(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def mcp_servers(root):
    """.mcp.json에 적힌 서버 이름. 파일이 없으면 None(사용자 공통 등록은 여기서 알 수 없다)."""
    p = root / '.mcp.json'
    if not p.is_file():
        return None
    try:
        return set((json.loads(p.read_text(encoding='utf-8')).get('mcpServers') or {}).keys())
    except (ValueError, AttributeError):
        raise ValueError('.mcp.json을 읽지 못했습니다')


def check_call(root, row):
    call = row.get('호출')
    need(isinstance(call, dict), '호출 누락: ' + row['id'])
    if row['길'] == 'MCP':
        tool = call.get('도구')
        need(text(tool) and isinstance(call.get('인자'), dict), 'MCP 도구·인자 필요: ' + row['id'])
        m = re.fullmatch(r'mcp__([^_].*?)__.+', tool)
        need(m, 'MCP 도구 이름은 mcp__<서버>__<도구> 꼴이어야 합니다: ' + tool)
        servers = mcp_servers(root)
        if servers is not None:
            need(m.group(1) in servers, 'MCP 서버가 .mcp.json에 없습니다: ' + m.group(1) + ' (사용자 공통 등록이면 claude mcp list로 확인하고 .mcp.json에 옮기세요)')
    else:
        argv = call.get('argv')
        need(isinstance(argv, list) and argv and all(text(a) for a in argv), 'CLI argv 필요: ' + row['id'])
        exe = argv[0]
        need(shutil.which(exe) or (root / exe).is_file(), 'CLI 실행파일을 이 PC에서 찾지 못했습니다: ' + exe)
    found = PLACEHOLDER.search(json.dumps(call, ensure_ascii=False))
    need(not found, '호출에 자리표시자가 남았습니다: ' + found.group(0) if found else '')


def load(root, ready=False):
    d = read_yaml(root / DECL)
    need(isinstance(d, dict) and d.get('버전') == 1, '선언 버전 1이 필요합니다')
    need(text(d.get('주인')), '주인 누락 (CLAUDE.md 프로필의 이름. 비어 있으면 본인에게 묻는다)')
    progress = d.get('진행', {})
    need(isinstance(progress, dict) and set(progress) == set(STAGES), '진행 단계 누락/오타')
    need(all(type(progress[s]) is bool for s in STAGES), '진행은 true/false로 적습니다')
    seen_false = False
    for stage in STAGES:
        if not progress[stage]:
            seen_false = True
        need(not (seen_false and progress[stage]), '진행 단계가 앞 단계를 건너뛰었습니다')
    if ready:
        need(progress['깔기'], '깔기 미완료 — wiring부터 이어가세요')
    installed = ready or progress['깔기']
    streams, sources = d.get('줄기'), d.get('통로')
    need(isinstance(streams, list) and streams, '줄기가 필요합니다')
    need(isinstance(sources, list) and sources, '통로가 필요합니다')
    for rows, label in [(streams, '줄기'), (sources, '통로')]:
        ids = [row.get('id') if isinstance(row, dict) else None for row in rows]
        need(all(isinstance(i, str) and re.fullmatch(r'[a-z][a-z0-9_-]*', i) for i in ids), label + ' id 형식 오류')
        need(len(set(ids)) == len(ids), label + ' id 중복')
    source_ids = {s['id'] for s in sources}
    used = set()
    for row in streams:
        need(text(row.get('이름')), '줄기 이름 누락')
        refs = row.get('통로')
        need(isinstance(refs, list) and refs and all(i in source_ids for i in refs), '줄기의 통로 참조 오류')
        used.update(refs)
        if installed:
            path = inside(root, row.get('기록'))
            need(path.is_file(), '기록 파일 없음: ' + str(row.get('기록')))
            need(any((root / r).resolve() in path.parents for r in RECORD_ROOTS), '기록 파일은 10-projects/ 또는 20-operations/ 아래 progress.md여야 합니다: ' + row['기록'])
    need(used == source_ids, '어느 줄기에도 연결되지 않은 통로')
    for row in sources:
        need(text(row.get('이름')), '통로 이름 누락')
        need(type(row.get('섞임')) is bool, '섞임은 true/false')
        if sum(row['id'] in s['통로'] for s in streams) > 1:
            need(row['섞임'], '여러 줄기에 연결된 통로는 섞임이어야 합니다')
        raw = inside(root, row.get('원본함'))
        need((root / '00-inbox/raw').resolve() in raw.parents, '원본함은 00-inbox/raw 아래여야 합니다')
        if installed:
            need(raw.is_dir(), '원본함 폴더 없음: ' + row['원본함'])
        if progress['길확인']:
            need(row.get('길') in ['MCP', 'CLI', '직접 넣기'], '길은 MCP/CLI/직접 넣기')
            if row['길'] != '직접 넣기':
                check_call(root, row)
                evidence = inside(root, row.get('근거'))
                need(raw in evidence.parents and evidence.is_file(), '실제 가져온 원본 근거 없음: ' + row['id'])
                need(text(row.get('범위')) and text(row.get('고유키')), '수집 범위·원문 고유키 필요: ' + row['id'])
    if progress['병목']:
        b = d.get('병목', {})
        need(isinstance(b, dict), '병목은 YAML 매핑이어야 합니다')
        stream = next((s for s in streams if s['id'] == b.get('줄기')), None)
        need(stream is not None, '병목 줄기 참조 오류')
        lanes = b.get('통로')
        need(isinstance(lanes, list) and lanes and all(i in stream['통로'] for i in lanes), '병목.통로는 병목 줄기에 연결된 통로 id 목록이어야 합니다')
        need(b.get('실행') in ['아침', '직접'], '병목 실행은 아침/직접')
        for key in ['증상', '입력', '출력', '승인기준']:
            need(text(b.get(key)), '병목 ' + key + ' 누락')
    if installed:
        names = [d.get('수집스킬'), d.get('병목', {}).get('스킬')]
        for name in names:
            need(text(name) and '/' not in name and '\\' not in name and name not in ['.', '..'], '스킬 이름 오류')
            need(inside(root, '.claude/skills/' + name + '/SKILL.md').is_file(), '스킬 파일 없음: ' + name)
        need(names[0] != names[1], '수집 스킬과 병목 스킬은 서로 다른 스킬이어야 합니다')
    if progress['한바퀴']:
        need(isinstance(d.get('돌아보기'), dict), '돌아보기 선언 필요')
        need(text(d.get('돌아보기', {}).get('날짜')), '첫 돌아보기 날짜 필요')
        need((root / BASE / '한바퀴-기록.md').is_file(), '한바퀴 실행 기록 없음')
    return d


def state(root):
    p = root / STATE
    s = read_yaml(p) if p.exists() else {'버전': 1, '수집': {}, '자료': {}}
    need(isinstance(s, dict) and s.get('버전') == 1 and isinstance(s.get('수집'), dict) and isinstance(s.get('자료'), dict), '실행상태 형식 오류')
    for item in s['자료'].values():
        need(isinstance(item, dict) and item.get('상태') in STATES, '자료 상태 오류')
        inside(root, item.get('원본'))
    return s


def missing_originals(root, s):
    """원본이 지워진 자료 id. 한 건 때문에 전체를 멈추지 않고 표시만 한다."""
    return [uid for uid, item in s['자료'].items() if not (root / item['원본']).is_file()]


def unregistered(root, d):
    """원본함·drop 폴더에 있는데 실행상태에 없는 파일 — intake 대상."""
    result = {}
    for row in d['통로']:
        pending = []
        for folder in [root / DROP / row['id'], root / row['원본함']]:
            if folder.is_dir():
                pending += [str(p.relative_to(root)) for p in sorted(folder.iterdir()) if p.is_file() and not p.name.startswith('.') and not STORED_NAME.match(p.name)]
        if pending:
            result[row['id']] = pending
    return result


def source(d, sid):
    return next(row for row in d['통로'] if row['id'] == sid)


def store(root, d, sid, key, incoming):
    row = source(d, sid)
    need(text(key), '원문 고유키 필요')
    body = Path(incoming).read_bytes()
    need(bool(body.strip()), '빈 원문은 등록하지 않습니다: ' + str(incoming))
    try:
        body.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('원문이 UTF-8이 아닙니다(윈도우 메모장이면 "다른 이름으로 저장"에서 인코딩 UTF-8 선택): ' + str(incoming))
    digest = hashlib.sha256(body).hexdigest()
    uid = hashlib.sha256((sid + '\0' + key).encode()).hexdigest()
    relative = row['원본함'].rstrip('/') + '/' + uid + '.md'
    dest = inside(root, relative)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves the original even if a prior run stopped before state save.
    try:
        with dest.open('xb') as f:
            f.write(body)
    except FileExistsError:
        need(hashlib.sha256(dest.read_bytes()).hexdigest() == digest, '동일 고유키의 원문이 바뀜 — 덮어쓰지 않았습니다. 버전 식별자를 확인하세요: ' + key)
    s = state(root)
    added = uid not in s['자료']
    if added:
        s['자료'][uid] = {'통로': sid, '고유키': key, '원본': relative, '상태': '신규'}
        write_yaml(root / STATE, s)
    return {'id': uid, '신규등록': added, **s['자료'][uid]}


def intake(root, d, sid):
    """직접 넣기: drop/<통로>/ 와 원본함의 미등록 파일을 파일 이름을 고유키로 등록하고 원래 파일을 지운다(본문은 원본함에 그대로)."""
    source(d, sid)
    files = unregistered(root, d).get(sid, [])
    added, known, errors = [], [], []
    last = None
    for rel in files:
        p = root / rel
        try:
            out = store(root, d, sid, p.name, p)
        except ValueError as e:
            errors.append(str(e))
            break
        (added if out['신규등록'] else known).append(p.name)
        if (root / out['원본']).read_bytes() == p.read_bytes():
            p.unlink()
        last = p.name
    ok = not errors
    row = collection(root, d, sid, ok, last or (state(root)['수집'].get(sid, {}).get('이어받기') or '없음'), len(added), '; '.join(errors))
    return {'통로': sid, '등록': added, '이미등록': known, '실패': errors, '수집': row}


def queue(root, d):
    s = state(root)
    gone = set(missing_originals(root, s))
    b = d.get('병목', {}) if d['진행']['병목'] else {}
    lanes = b.get('통로') or []
    result = []
    for uid, item in s['자료'].items():
        if item['상태'] not in ['반영완료', '버림']:
            result.append({'id': uid, **item, '병목대상': item['통로'] in lanes, '원본없음': uid in gone})
    return result


def marker_found(root, uid):
    pattern = re.compile(r'wiring:' + re.escape(uid) + r':\d+')
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [n for n in dirnames if n not in SKIP_DIRS and not n.startswith('.')]
        for name in filenames:
            if name.endswith('.md'):
                try:
                    if pattern.search((Path(dirpath) / name).read_text(encoding='utf-8')):
                        return True
                except (UnicodeDecodeError, OSError):
                    continue
    return False


def transition(root, uid, target, proof=None):
    s = state(root)
    item = s['자료'][uid]
    need(target in TRANSITIONS.get(item['상태'], []), '상태를 건너뛰거나 완료 자료를 다시 처리할 수 없습니다')
    need(text(proof), '제안 파일·사용자 승인 원문·반영 위치 등 근거를 적으세요')
    if target == '승인대기':
        need((root / PROPOSALS / (uid + '.md')).is_file(), '제안 파일이 없습니다: ' + PROPOSALS + uid + '.md')
    if target == '반영완료':
        need(marker_found(root, uid), '반영 표식 <!-- wiring:' + uid + ':항목번호 --> 가 기록 파일·할 일 어디에도 없습니다 — 반영을 먼저 하세요')
    item.setdefault('이력', []).append({'이전': item['상태'], '다음': target, '근거': proof})
    item['상태'] = target
    write_yaml(root / STATE, s)
    return item


def collection(root, d, sid, ok, cursor, count, error):
    source(d, sid)
    need(count >= 0, '건수는 0 이상')
    need(ok or text(error), '실패 원인 필요')
    need(not ok or text(cursor), '성공한 수집 범위의 끝 지점 필요')
    s = state(root)
    row = s['수집'].setdefault(sid, {})
    row['최근시도'] = datetime.now(timezone.utc).isoformat()
    row['결과'] = '성공' if ok else '실패'
    row['건수'] = count
    row['오류'] = '' if ok else SECRET.sub(r'\1\2***', error)
    if ok:
        row['마지막성공'] = row['최근시도']
        row['이어받기'] = cursor
    write_yaml(root / STATE, s)
    return row


def render(root, d):
    # Mechanical view: full declaration retained, no second editable inventory.
    content = '# 배선도 — ' + d['주인'] + '\n\n'
    content += '> 선언.yaml에서 생성했습니다. 이 파일을 직접 고치지 않습니다.\n\n'
    content += '진행: ' + ' · '.join(s + (' [x]' if d['진행'][s] else ' [ ]') for s in STAGES) + '\n\n'
    def cell(value):
        return ('' if value is None else str(value)).replace('|', '\\|').replace('\n', '<br>')
    content += '## 일의 줄기\n\n| 줄기 | 들어오는 통로 | 내가 하는 것 | 나가는 곳 | 기록 |\n|---|---|---|---|---|\n'
    names = {row['id']: row['이름'] for row in d['통로']}
    for row in d['줄기']:
        values = [row['이름'], ', '.join(names[i] for i in row['통로']), row.get('내가하는것'), row.get('나가는곳'), row.get('기록')]
        content += '| ' + ' | '.join(cell(v) for v in values) + ' |\n'
    content += '\n## 선언 상세\n\n```yaml\n' + yaml.safe_dump(d, allow_unicode=True, sort_keys=False) + '```\n\n'
    content += '## 실행 결과\n\n실행상태.yaml이 원본입니다. 승인 대기는 queue 명령으로 확인합니다.\n'
    (root / BASE / '배선도.md').write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest='command', required=True)
    v = sub.add_parser('validate'); v.add_argument('--ready', action='store_true')
    sub.add_parser('render'); sub.add_parser('queue')
    a = sub.add_parser('store'); a.add_argument('source'); a.add_argument('key'); a.add_argument('file')
    a = sub.add_parser('intake'); a.add_argument('source')
    a = sub.add_parser('status'); a.add_argument('id'); a.add_argument('target'); a.add_argument('--proof', required=True)
    a = sub.add_parser('result'); a.add_argument('source'); a.add_argument('--ok', action='store_true'); a.add_argument('--cursor'); a.add_argument('--count', type=int, default=0); a.add_argument('--error', default='')
    args = parser.parse_args(); root = args.root.resolve()
    try:
        need((root / 'CLAUDE.md').is_file() and (root / '00-inbox').is_dir(), '워크스페이스 루트가 아닙니다')
        need((root / DECL).is_file(), '선언 없음: ' + DECL + ' — "배선도 그려줘"로 wiring부터')
        d = load(root, ready=getattr(args, 'ready', False) or args.command in ['queue', 'status', 'result', 'intake'])
        if args.command == 'validate':
            s = state(root)
            result = {'정상': True, '진행': d['진행'], '미등록원문': unregistered(root, d), '원본없음': missing_originals(root, s)}
        elif args.command == 'render':
            render(root, d); result = {'생성': BASE + '배선도.md'}
        elif args.command == 'queue': result = queue(root, d)
        elif args.command == 'store': result = store(root, d, args.source, args.key, args.file)
        elif args.command == 'intake': result = intake(root, d, args.source)
        elif args.command == 'status': result = transition(root, args.id, args.target, args.proof)
        else: result = collection(root, d, args.source, args.ok, args.cursor, args.count, args.error)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except (ValueError, OSError, KeyError, TypeError, StopIteration, yaml.YAMLError) as e:
        print('오류: ' + (str(e) or '선언에 없는 통로/자료'), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
