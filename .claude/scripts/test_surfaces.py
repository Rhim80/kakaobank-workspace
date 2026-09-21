#!/usr/bin/env python3
"""Temporary-workspace tests for shared surfaces and todo persistence."""
from datetime import date
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import surfaces as s
import todo_store as t
from wiring import yaml

KIT = Path(__file__).resolve().parents[2]

class SurfacesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for path in ['CLAUDE.md', '00-system/선언-표면.yaml']:
            target = self.root/path; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(KIT/path,target)
        for path in ['00-system/01-templates','30-knowledge/00-wiki']:
            shutil.copytree(KIT/path,self.root/path)
        self.c = s.resolve(self.root)['선언']
    def save(self):
        (self.root/'00-system/선언-표면.yaml').write_text(yaml.safe_dump(self.c,allow_unicode=True,sort_keys=False))
    def source(self):
        path=self.root/'source.md';path.write_text('근거 원문\n');return path
    def test_daily_idempotent_and_iso_year(self):
        v=s.resolve(self.root,date(2021,1,1))
        self.assertTrue(v['주간파일'].endswith('2020-W53.md'))
        self.assertEqual(v['주간시작'],'2020-12-28')
        self.assertTrue(s.daily(self.root,v)['created'])
        p=self.root/v['하루파일'];p.write_text(p.read_text()+'\n수기 기록\n')
        before=p.read_bytes();self.assertFalse(s.daily(self.root,v)['created'])
        self.assertEqual(before,p.read_bytes())
    def test_custom_paths_and_section(self):
        self.c['할일']['위치']='custom/todos.md'
        self.c['할일']['완료보관']='custom/done.md'
        self.c['할일']['섹션']['오늘']='지금 할 일'
        self.c['하루']['위치']='custom/daily'
        self.c['주간']['위치']='custom/weekly';self.save()
        result=t.add(self.root,'자료 대조',priority='high')
        self.assertEqual(result['section'],'지금 할 일')
        self.assertEqual(t.listing(self.root,'today')[0]['title'],'자료 대조')
        s.daily(self.root,s.resolve(self.root))
        self.assertFalse((self.root/'40-personal').exists())
        self.assertEqual(len(list((self.root/'custom/daily').rglob('*.md'))),1)
    def test_wiring_duplicate_and_completed_retry(self):
        self.source();key='wiring:'+'a'*64+':1'
        task=t.add(self.root,'검토',source='source.md',key=key)
        self.assertFalse(t.add(self.root,'검토',source='source.md',key=key)['added'])
        t.complete(self.root,task['id'])
        again=t.add(self.root,'검토',source='source.md',key=key)
        self.assertEqual(again['location'],'archive');self.assertTrue(again['done'])
        self.assertEqual(t.listing(self.root),[])
        archive=t.configuration(self.root)[2].read_text()
        self.assertEqual(archive.count('<!-- '+key+' -->'),1)
        self.assertTrue(t.add(self.root,'검토',source='source.md',key='wiring:'+'a'*64+':2')['added'])
    def test_completion_interrupted_after_archive(self):
        task=t.add(self.root,'보관 시험');real=t.atomic;active=t.configuration(self.root)[1]
        def interrupted(path,body):
            if path==active: raise OSError('interrupted')
            real(path,body)
        with patch.object(t,'atomic',side_effect=interrupted):
            with self.assertRaises(OSError):t.complete(self.root,task['id'])
        t.complete(self.root,task['id'])
        self.assertEqual(t.listing(self.root),[])
        self.assertEqual(len(t.parse(t.configuration(self.root)[2].read_text())),1)
    def test_preserve_legacy_and_empty_placeholders(self):
        active=t.configuration(self.root)[1];active.parent.mkdir(parents=True)
        active.write_text('# My todos\n\n메모 보존\n\n## Inbox\n\n- [ ]\n\n- [ ] 이전 할 일\n  - project: alpha\n')
        t.add(self.root,'새 할 일')
        self.assertIn('메모 보존',active.read_text())
        before=active.read_bytes()
        self.assertEqual(t.listing(self.root,'stats')['total'],2)
        self.assertEqual(before,active.read_bytes())
    def test_missing_and_dirty_source(self):
        p=self.source();task=t.add(self.root,'검토',source='source.md')
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        subprocess.run(['git','add','source.md'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','-c','commit.gpgsign=false','commit','-qm','fixture'],cwd=self.root,check=True)
        p.write_text('변경된 원문\n')
        self.assertEqual(t.listing(self.root)[0]['source_status'],'review')
        p.unlink()
        self.assertEqual(t.listing(self.root,'overdue')[0]['source_status'],'missing')
    def test_operations_and_explicit_record(self):
        base=self.root/'20-operations/21-support';base.mkdir(parents=True)
        (base/'progress.md').write_text('# 운영 기록')
        (base/'log.md').write_text('# 별도 기록')
        (base/'artifacts').mkdir();(base/'artifacts/report.md').write_text('보고')
        wire=self.root/'00-system/wiring/선언.yaml';wire.parent.mkdir()
        wire.write_text(yaml.safe_dump({'줄기':[{'기록':'20-operations/21-support/log.md'}]},allow_unicode=True))
        found=s.progress(self.root,s.resolve(self.root),'20-operations/21-support/artifacts/report.md')
        self.assertEqual(found,['20-operations/21-support/log.md','20-operations/21-support/progress.md'])
    def test_invalid_configuration(self):
        for bad in ['../outside.md','/tmp/outside.md']:
            self.c['할일']['위치']=bad;self.save()
            with self.assertRaises(ValueError):s.resolve(self.root)
        self.c['할일']['위치']='todo.md'
        self.c['하루']['템플릿']='missing.md';self.save()
        with self.assertRaises(ValueError):s.resolve(self.root)
    def test_duplicate_yaml_and_sections(self):
        cfg=self.root/'00-system/선언-표면.yaml';cfg.write_text(cfg.read_text()+'\n버전: 1\n')
        with self.assertRaises(ValueError):s.resolve(self.root)
        self.save();active=t.configuration(self.root)[1];active.parent.mkdir(parents=True)
        active.write_text('## This Week\n\n## This Week\n')
        with self.assertRaises(ValueError):t.add(self.root,'추가 안 됨')
    def test_cli_readonly_and_malformed(self):
        cmd=[sys.executable,str(KIT/'.claude/scripts/surfaces.py'),'--root',str(self.root),'resolve']
        result=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.root/'40-personal').exists())
        (self.root/'00-system/선언-표면.yaml').write_text('버전: [')
        result=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertNotIn('Traceback',result.stderr)
    def test_shell_entrypoints(self):
        script=str(KIT/'.claude/scripts/surfaces.sh')
        for args in [['resolve'],['todo','validate'],['todo','list','--mode','stats']]:
            result=subprocess.run(['bash',script]+args,cwd=self.root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run(['bash',script,'todo','add','래퍼로 추가'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(t.listing(self.root)[0]['title'],'래퍼로 추가')

    def test_relocated_wiki_cli_and_escape(self):
        self.c['위키']['위치']='knowledge/wiki';self.save()
        (self.root/'knowledge').mkdir()
        shutil.move(str(self.root/'30-knowledge/00-wiki'),str(self.root/'knowledge/wiki'))
        s.resolve(self.root)
        cmd=[sys.executable,str(KIT/'.claude/skills/wiki-lint/scripts/wiki_check.py'),'--root',str(self.root),'--wiki-dir','knowledge/wiki','--json']
        result=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        cmd[-2] = '../outside'
        result=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(result.returncode,2)

if __name__=='__main__':unittest.main()
