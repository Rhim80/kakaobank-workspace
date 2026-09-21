"""임시 위키에서 오탐·미탐·읽기 전용 경계를 검증한다."""
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
import hashlib
import json
import os
import subprocess
import sys
import unittest
from wiki_check import check, render_index, prose, enriched, SOURCE
from _wikilinks import link_index, link_target, link_alive

class WikiCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.wiki=self.root/'30-knowledge/00-wiki';self.wiki.mkdir(parents=True)
        (self.root/'CLAUDE.md').write_text('# Workspace')
        (self.wiki/'SCHEMA.md').write_text('# Schema')
        (self.root/'raw').mkdir();(self.root/'raw/source.md').write_text('# 원문\n첫 판단이다.\n새 반례다.\n')
        self.base='# A\n> **관련**: [[raw/source]]\n\n## 핵심\n요약\n## 근거\n- 첫 판단이다. [source: raw/source.md, 2026-09-01, §원문]\n## 적용\n## Open Questions\n## Related\nLast enriched: 2026-09-01\n'
        (self.wiki/'A.md').write_text(self.base)
        (self.wiki/'index.md').write_text('# Index\n## 분류\n| 토픽 | 유형 | 한 줄 설명 | sources | enriched |\n|---|---|---|---|---|\n| ↳ [[A]] | concept (hub) | 설명은 그대로다 | 1 | 2026-09-01 |\n')
        (self.wiki/'log.md').write_text('# Log\n')
    def runcheck(self,selected=None):return check(self.root,selected,date(2026,9,21))[0]
    def codes(self,selected=None):return [i['code'] for i in self.runcheck(selected)['issues']]
    def write(self,t): (self.wiki/'A.md').write_text(t)
    def test_clean_readonly(self):
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.codes(),[])
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before})
    def test_missing_link_and_examples(self):
        self.write(self.base+'\n[[없음]]\n```md\n[[예시]]\n[!contradiction]\n```\n~~~md\n[[예시2]]\n~~~\n`[[인라인]]`\nSources: [[과거]] [!contradiction]\n')
        issues=self.runcheck()['issues'];self.assertEqual([i['message'] for i in issues if i['code']=='dead_link'],['없음'])
        self.assertNotIn('contradiction_date',self.codes())
    def test_mismatch_and_partial_scope(self):
        self.write(self.base.replace('Last enriched: 2026-09-01','Last enriched: 2026-09-02'))
        (self.wiki/'B.md').write_text('# B\n[[누락]]')
        self.assertIn('date_mismatch',self.codes(['A.md']))
        self.assertNotIn('dead_link',self.codes(['A.md']))
        self.assertEqual(self.runcheck(['A.md'])['files_read'],1)
        self.assertIn('dead_link',self.codes())
    def test_index_preserves_metadata(self):
        idx=(self.wiki/'index.md').read_text();out=render_index(idx,{'A':self.base})
        self.assertIn('| ↳ [[A]] | concept (hub) | 설명은 그대로다 | 2026-09-01 |',out)
        self.assertIn('## 분류',out);self.assertNotIn('sources',out);self.assertEqual(out,render_index(out,{'A':self.base}))
    def test_open_closed_and_history(self):
        self.write(self.base+'\n> [!contradiction 2026-09-21] 오늘\n> [!contradiction 2026-06-01] 옛날\n> [!superseded 2026-09-01 → 근거] 닫힘\n> [!contradiction] 날짜없음\n')
        issues=self.runcheck()['issues'];opened=[i for i in issues if i['code']=='open_contradiction']
        self.assertEqual(len(opened),2);self.assertEqual(sum('30일 초과' in i['message'] for i in opened),1)
        self.assertIn('contradiction_date',self.codes())
    def test_missing_ambiguous_source_never_guessed(self):
        (self.root/'other').mkdir();(self.root/'other/source.md').write_text('다른 자료')
        self.write(self.base.replace('raw/source.md','source.md'))
        self.assertIn('source_unresolved',self.codes());self.assertIn('source: source.md',(self.wiki/'A.md').read_text())
    def test_same_source_different_evidence(self):
        line='- 새 반례다. [source: raw/source.md, 2026-09-01, §원문]\n'
        self.write(self.base.replace('## 적용',line+'## 적용'))
        self.assertNotIn('duplicate_evidence',self.codes());self.assertEqual(self.runcheck()['topics']['A']['evidence_count'],2)
        self.write(self.base.replace('## 적용',line+line+'## 적용'))
        self.assertIn('duplicate_evidence',self.codes())
    def test_count_only_evidence(self):
        self.write(self.base.replace('## 적용','```md\n- 예시\n```\n## 적용\n- 적용\n'))
        self.assertEqual(self.runcheck()['topics']['A']['evidence_count'],1)
    def test_footer_code_not_date(self):
        t='```\nLast enriched: 2020-01-01\n```\n'+self.base+'Sources: old\n'
        self.assertEqual(enriched(t),'2026-09-01')
    def test_shared_link_rules(self):
        names,suffixes=link_index(['project/16.26-progress.md','raw/source.md'])
        self.assertTrue(link_alive(link_target('project/16.26-progress\\|별칭'), 'wiki/A.md',self.root,names,suffixes))
        self.assertTrue(link_alive('../../raw/source','30-knowledge/00-wiki/A.md',self.root,names,suffixes))
        self.assertTrue(link_alive('raw/','wiki/A.md',self.root,names,suffixes))
        self.assertFalse(link_alive('16.26-missing','wiki/A.md',self.root,names,suffixes))
    def test_annotated_source_retains_timestamp(self):
        line='- 근거 [source: `raw/source.md` §원문 [22:02], 2026-09-01]'
        clean=list(prose(line))[0][1];self.assertIn('[22:02]',SOURCE.search(clean)[1])
    def test_inline_source_example_and_distinct_code_evidence(self):
        self.assertEqual(list(prose('`[source: missing, 2026-09-01]`'))[0][1], '')
        self.write(self.base.replace('## 적용', '- `첫 코드`\n- `다른 코드`\n## 적용'))
        self.assertNotIn('duplicate_evidence', self.codes())

    def test_blank_type_reports_error(self):
        p=self.wiki/'index.md';p.write_text(p.read_text().replace('concept (hub)', ' '))
        self.assertIn('type',self.codes())

    def test_malformed_index_is_not_silently_skipped(self):
        p=self.wiki/'index.md';original=p.read_text()
        for row in ('| [[missing]] | concept | 설명 |',
                    '| [[missing]] | concept | 설명 | x | y | z |'):
            with self.subTest(row=row):
                p.write_text(original+row+'\n')
                self.assertIn('index_row',self.codes())
                self.assertIn('index_missing_page',self.codes())
                self.assertNotIn('index_row',self.codes(['A.md']))
        p.write_text(original.replace('| ↳ [[A]] | concept (hub) | 설명은 그대로다 | 1 | 2026-09-01 |',
                                      '| [[A]] | concept | 설명 |'))
        self.assertIn('index_row',self.codes(['A.md']))

    def test_comment_neighbors_and_multiline(self):
        self.write(self.base+'[[before]] <!-- [[hidden]] --> [[after]]\n<!--\n```\n[[hidden2]]\n--> [[last]]\n')
        self.assertEqual([i['message'] for i in self.runcheck()['issues'] if i['code']=='dead_link'],
                         ['before','after','last'])
        self.write(self.base+'`<!--` [[visible]]\n[[next]]\n')
        self.assertEqual([i['message'] for i in self.runcheck()['issues'] if i['code']=='dead_link'],['visible','next'])

    def test_index_examples_are_not_rows_or_rewritten(self):
        p=self.wiki/'index.md'
        example='```md\n| 토픽 | 유형 | 설명 | sources | enriched |\n|---|---|---|---|---|\n| [[example]] | concept | 예시 | 1 | 2000-01-01 |\n```\n'
        p.write_text(p.read_text()+example+'`| [[inline]] | concept | 예시 | 2000-01-01 |`\n')
        self.assertEqual(self.codes(),[])
        out=render_index(p.read_text(),{'A':self.base})
        self.assertIn(example,out)

    def test_source_dates_and_empty_anchors(self):
        for value in ('2026-99-99','2026-02-30','날짜 미확인'):
            with self.subTest(date=value):
                self.write(self.base.replace('source.md, 2026-09-01','source.md, '+value))
                self.assertIn('source_date',self.codes())
        for value in ('§', '인용:', '인용: ""'):
            with self.subTest(anchor=value):
                self.write(self.base.replace('§원문',value))
                self.assertIn('source_anchor',self.codes())
        for value in ('§원문', '인용: 첫 판단이다.'):
            self.write(self.base.replace('§원문',value));self.assertEqual(self.codes(),[])

    def test_continuation_source_stays_with_its_bullet(self):
        self.write(self.base.replace('- 첫 판단이다. [source:', '- 첫 판단이다.\n  [source:'))
        self.assertNotIn('source_missing',self.codes())
        self.write(self.base.replace('- 첫 판단이다.', '- 출처 없는 근거\n- 첫 판단이다.'))
        self.assertEqual(self.codes().count('source_missing'),1)
        self.write(self.base.replace('- 첫 판단이다.', '- 출처 없는 근거\n## 다른 절\n- 첫 판단이다.'))
        self.assertEqual(self.codes().count('source_missing'),1)

    def test_empty_folder_and_suffix(self):
        (self.root/'raw/empty').mkdir()
        self.write(self.base+'[[raw/empty/]] [[empty/]] [[missing/]]\n')
        self.assertEqual([i['message'] for i in self.runcheck()['issues'] if i['code']=='dead_link'],['missing/'])

    def test_cli_modes_and_exit_status(self):
        script=Path(__file__).with_name('wiki_check.py')
        env={**os.environ,'PKM_ROOT':str(self.root/'unrelated-pkm')}
        def run(*args):
            return subprocess.run([sys.executable,"-S",str(script),"--root",str(self.root),*args],env=env,capture_output=True,text=True)
        self.assertEqual(run('--json').returncode,0)
        self.write(self.base+'<!-- note --> [[missing]]\n')
        for args in (('--json',),('--files','A.md','--json')):
            result=run(*args)
            self.assertEqual(result.returncode,1)
            self.assertIn('dead_link',[i['code'] for i in json.loads(result.stdout)['issues']])
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        rendered=run('--index')
        self.assertEqual(rendered.returncode,0)
        self.assertNotIn('| sources |',rendered.stdout)
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.assertEqual(run('--files','../outside.md','--json').returncode,2)

    def test_future_date_and_unknown_root(self):
        self.write(self.base.replace('2026-09-01', '2099-01-01'))
        self.assertIn('future_date', self.codes())
        (self.root/'CLAUDE.md').unlink()
        with self.assertRaises(ValueError): self.runcheck()

    def test_root_exception_requires_marker(self):
        self.write('# A\n> **관련**: \nLast enriched: 2026-09-01\n')
        self.assertIn('section', self.codes())
        self.write('Origin: root\n'+(self.wiki/'A.md').read_text())
        self.assertNotIn('section', self.codes())

    def test_missing_input_is_error(self):
        self.assertIn('missing_page',self.codes(['missing.md']))
        with self.assertRaises(ValueError):self.codes(['../outside.md'])

if __name__=='__main__':unittest.main()
