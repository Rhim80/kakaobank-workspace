#!/usr/bin/env python3
"""읽기 전용 워크스페이스 위키 검사 (Python 3.9+, 표준 라이브러리).

의미 판단·웹 접근·파일 수정은 하지 않는다.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from _wikilinks import link_index, link_target, link_alive

SKIP = {'SCHEMA.md', 'README.md', 'index.md', 'log.md'}
LINK = re.compile(r'\[\[([^\[\]]+)\]\]')
SOURCE = re.compile(r'\[source:\s*((?:[^\[\]]|\[[^\]]*\])*)\]')

def prose(text):
    """행 번호 보존. 코드펜스/인라인 코드/HTML 주석은 실제 지식으로 세지 않는다."""
    fence = None
    comment = False
    for num, line in enumerate(text.splitlines(), 1):
        if fence:
            if re.fullmatch(r'\s*'+re.escape(fence[0])+r'{'+str(len(fence))+r',}\s*', line):
                fence = None
            continue
        # 주석 밖의 양옆 텍스트와 원래 행 번호를 유지한다.
        visible = ''
        while line:
            if comment:
                end = line.find('-->')
                if end < 0: break
                line = line[end+3:]; comment = False
            else:
                token = re.search(r'(`+).*?\1|<!--', line)
                if token is None:
                    visible += line; break
                visible += line[:token.start()]
                if token[0] == '<!--':
                    comment = True
                else:
                    visible += token[0]  # 코드 안 주석 기호는 주석을 열지 않는다
                line = line[token.end():]
        line = visible
        m = re.match(r'^\s*(`{3,}|~{3,})', line)
        if m:
            fence = m[1]
            continue
        spans = [m.span() for m in SOURCE.finditer(line)]
        def inline(m):
            if any(start < m.start() and m.end() < end for start, end in spans):
                return m[0].strip('`')  # 출처 안의 경로 코드 표기는 보존
            return ''
        yield num, re.sub(r'(`+).*?\1', inline, line)

def rows(text):
    original = text.splitlines()
    for num, line in prose(text):
        if not line.lstrip().startswith('|'): continue
        cells = re.split(r'(?<!\\)\|', line.strip())[1:]
        if line.rstrip().endswith('|'): cells = cells[:-1]
        m = LINK.search(cells[0]) if cells else None
        if m:
            # 출력 후보는 원래 셀을 써서 설명의 코드·주석을 보존한다.
            raw = re.split(r'(?<!\\)\|', original[num-1].strip())[1:]
            if original[num-1].rstrip().endswith('|'): raw = raw[:-1]
            yield num, link_target(m[1]), [c.strip() for c in raw]

def enriched(text):
    for _, line in prose(text):
        m = re.match(r'^Last enriched:\s*(\d{4}-\d{2}-\d{2}|미확인)', line)
        if m: return m[1]
    return None

def valid_date(value):
    try: return date.fromisoformat(value)
    except (ValueError, TypeError): return None

def render_index(text, pages):
    lines = text.splitlines(keepends=True)
    for num, name, cells in rows(text):
        if len(cells) not in (4, 5): continue  # 잘못된 행을 자동 보정하지 않는다
        if len(cells) == 5: del cells[3]
        d = enriched(pages.get(name, ''))
        if d and (d == '미확인' or valid_date(d)): cells[-1] = d
        lines[num-1] = '| ' + ' | '.join(cells) + ' |\n'
    for num, line in prose(text):
        i = num - 1
        if line.lstrip().startswith('|') and re.search(r'\|\s*sources\s*\|', line, re.I):
            lines[i] = re.sub(r'\s*sources\s*\|', '', line, flags=re.I)
            if i+1 < len(lines):
                cells = lines[i+1].strip().split('|')
                if len(cells) == 7:
                    del cells[4]; lines[i+1] = '|'.join(cells)+'\n'
    return ''.join(lines)

def check(root, selected=None, today=None):
    today = today or date.today()
    root = Path(root).resolve()
    wiki = root / '30-knowledge/00-wiki'
    if not (root/'CLAUDE.md').is_file() or not (wiki/'SCHEMA.md').is_file():
        raise ValueError('워크스페이스 루트의 CLAUDE.md와 위키 SCHEMA.md가 필요합니다')
    wanted = None
    if selected is not None:
        wanted = set()
        for item in selected:
            path = Path(item)
            if path.is_absolute(): path = path.resolve().relative_to(wiki.resolve())
            elif '/' in item: path = (root/path).resolve().relative_to(wiki.resolve())
            if path.parent != Path('.') or path.suffix != '.md' or path.name in SKIP:
                raise ValueError('--files에는 위키 토픽 .md 파일을 지정하세요 (관련 index 항목은 자동 검사)')
            wanted.add(path.stem)
    pages = {p.stem: p.read_text(encoding='utf-8') for p in sorted(wiki.glob('*.md'))
             if p.name not in SKIP and (wanted is None or p.stem in wanted)}
    idx = (wiki/'index.md').read_text(encoding='utf-8')
    entries = list(rows(idx))
    byname = {}
    for row in entries: byname.setdefault(row[1], []).append(row)
    paths = [p for p in root.rglob('*') if '.git' not in p.parts]
    names, suffixes = link_index((str(p.relative_to(root)) for p in paths if p.is_file()),
                                 (str(p.relative_to(root)) for p in paths if p.is_dir()))
    issues = []
    def add(level, code, file, line, message):
        issues.append(dict(level=level, code=code, file=str(file), line=line, message=message))
    if wanted is None: wanted = set(pages)
    for n, name, cells in entries:
        if (selected is None or name in wanted) and len(cells) not in (4, 5):
            add('error','index_row','index.md',n,f'{name}: 열 {len(cells)}개 (4개 필요; 옛 sources 포함 5개 허용)')
    metrics = {}
    for name in sorted(wanted):
        rel = (wiki/(name+'.md')).relative_to(root)
        if name not in pages:
            add('error','missing_page',rel,0,'지정 토픽 파일 없음'); continue
        txt = pages[name]; lines = list(prose(txt)); body = [(n,l) for n,l in lines if not l.startswith(('Last enriched:', 'Sources:'))]
        entry = byname.get(name, [])
        if not entry: add('error','unregistered',rel,0,'index 등록 없음')
        if len(entry)>1: add('error','duplicate_index','index.md',entry[1][0],name)
        d = enriched(txt)
        if not valid_date(d): add('warning' if d=='미확인' else 'error','enriched_date',rel,0,'Last enriched 날짜 '+str(d))
        for n,_,cells in entry:
            if len(cells) not in (4, 5): continue
            if cells[-1] != d: add('error','date_mismatch','index.md',n,f'{name}: index={cells[-1]}, 본문={d}')
            typ = next(iter(cells[1].split()), '')
            if typ not in ('concept','entity','synthesis'): add('error','type','index.md',n,name+': '+typ)
            if len(cells[2])>70: add('warning','description_length','index.md',n,name)
            if valid_date(d) and typ in ('concept','entity','synthesis'):
                age=(today-valid_date(d)).days
                if age > {'concept':180,'entity':60,'synthesis':120}[typ]: add('warning','stale',rel,0,f'{age}일 미보강 — 내용 오류 판정 아님')
        if valid_date(d) and valid_date(d)>today: add('error','future_date',rel,0,d)
        root_style = bool(re.search(r'^Origin:\s*root',txt,re.M))
        if not any(re.match(r'^# ',l) for _,l in body): add('error','title',rel,0,'H1 없음')
        if not root_style:
            for section in ('핵심','근거','적용','Open Questions','Related'):
                if not any(re.match(r'^## '+section+r'(?:\s|$)',l) for _,l in body): add('error','section',rel,0,section+' 절 없음')
        related = [(n,l) for n,l in body if re.match(r'^>\s*\*\*관련\*\*:',l)]
        if not related: add('error','infobox',rel,0,'관련 줄 없음')
        for n,l in related:
            if len(LINK.findall(l))>6: add('error','infobox_limit',rel,n,'관련 링크 6개 초과')
        for n,l in body:
            if re.match(r'^>\s*\*\*Facets\*\*:',l) and len(l.split(':',1)[1].strip())>85: add('warning','facets',rel,n,'85자 권장 상한 초과')
            for raw in LINK.findall(l):
                target=link_target(raw)
                if not link_alive(target,str(rel),root,names,suffixes): add('error','dead_link',rel,n,target)
            if re.search(r'\bline \d+',l): add('warning','line_reference',rel,n,'줄 번호 참조: 안정된 소제목으로 대조 필요')
            for m in re.finditer(r'\[!(contradiction|superseded)([^\]]*)\]',l):
                stamp = re.search(r'\d{4}-\d{2}-\d{2}',m[2]); day=valid_date(stamp[0]) if stamp else None
                if not day: add('error','contradiction_date',rel,n,'모순 표시 날짜 없음/잘못된 날짜')
                elif day>today: add('error','contradiction_date',rel,n,'미래 날짜')
                elif m[1]=='contradiction': add('warning','open_contradiction',rel,n,f'{(today-day).days}일 열림'+(' (30일 초과)' if (today-day).days>30 else ''))
        count=0; in_evidence=False; seen=set()
        for offset,(n,l) in enumerate(body):
            if l.startswith('## '): in_evidence=bool(re.match(r'^## 근거(?:\s|$)',l))
            if in_evidence and l.startswith('- '):
                count+=1
                continuation = [l]
                for _, following in body[offset+1:]:
                    if following.strip() and not following.startswith(('  ', '\t')): break
                    continuation.append(following)
                if not SOURCE.search('\n'.join(continuation)):
                    add('warning','source_missing',rel,n,'근거 불릿과 이어지는 들여쓴 문단에 출처 없음')
                fingerprint=re.sub(r'\s+',' ',txt.splitlines()[n-1].strip())
                if fingerprint in seen: add('warning','duplicate_evidence',rel,n,'동일 근거 불릿 반복')
                seen.add(fingerprint)
            for m in SOURCE.finditer(l):
                citation=m[1]; locator=citation.split(',',1)[0].strip().strip('`')
                file_match = re.match(r'(.+?\.md)(?:\s|\(|$)', locator)
                file_locator = file_match[1] if file_match else locator
                if locator.startswith('대화 원문 미보존:'): state='conversation_unstored'
                elif urlparse(locator).scheme in ('http','https') and urlparse(locator).netloc: state='url'
                elif not Path(file_locator).is_absolute() and '..' not in Path(file_locator).parts and (root/file_locator).is_file(): state='file'
                else: state='source_unresolved'
                if state in ('source_unresolved','conversation_unstored'): add('warning',state,rel,n,citation)
                stamps = re.findall(r'(?<![\d-])\d{4}-\d{2}-\d{2}(?![\d-])', citation)
                if not stamps or not all(valid_date(stamp) for stamp in stamps):
                    add('warning','source_date',rel,n,citation)
                anchors = re.findall(r'(?:§|인용:)\s*([^,]*)',citation)
                if not any(a.strip(" \t\n`\"'“”‘’§:") for a in anchors):
                    add('warning','source_anchor',rel,n,citation)
        metrics[name]={'evidence_count':count,'last_enriched':d}
        if count>30: add('warning','evidence_size',rel,0,f'근거 {count}항목'+(' — 분리안 필요' if count>50 else ' — 정리 고려'))
    if selected is None:
        for n,name,cells in entries:
            if name not in pages: add('error','index_missing_page','index.md',n,name)
    return dict(root=str(root),scope='all' if selected is None else 'files',files_read=len(wanted & pages.keys()),topics=metrics,issues=issues,summary=dict(Counter(i['level'] for i in issues))),idx,pages

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[4], help='워크스페이스 루트 (기본: 이 스크립트가 설치된 워크스페이스)')
    p.add_argument('--files',nargs='+'); p.add_argument('--json',action='store_true'); p.add_argument('--index',action='store_true',help='본문 날짜를 반영한 index를 stdout으로 출력 (쓰기 없음)')
    args=p.parse_args()
    if args.index and args.files: p.error('--index와 --files는 함께 사용하지 않습니다')
    try: result,idx,pages=check(args.root,args.files)
    except (OSError,ValueError,KeyError) as e: p.exit(2,f'검사 실패: {e}\n')
    if args.index: print(render_index(idx,pages),end=''); return 0
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print(f"범위={result['scope']} root={result['root']} 토픽={result['files_read']}파일")
        for i in result['issues']: print(f"{i['level']} {i['file']}:{i['line']} [{i['code']}] {i['message']}")
        print(json.dumps(result['summary'],ensure_ascii=False))
    return 1 if result['summary'].get('error') else 0

if __name__=='__main__': sys.exit(main())
