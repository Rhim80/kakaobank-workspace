#!/usr/bin/env python3
"""Isolated behavioral checks; never connects to participant services.

Each test names the case it must NOT let through (see references/declaration.md 「검사 범위」).
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wiring', HERE / 'wiring.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
yaml = w.yaml


class WiringTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ['00-inbox/raw/input', '00-system/wiring', '20-operations/21-work', '.claude/skills/collect', '.claude/skills/process']:
            (self.root / name).mkdir(parents=True)
        for name in ['CLAUDE.md', '20-operations/21-work/progress.md', '.claude/skills/collect/SKILL.md', '.claude/skills/process/SKILL.md']:
            (self.root / name).write_text('fixture\n', encoding='utf-8')
        self.d = yaml.safe_load((HERE.parent / 'assets/declaration-template.yaml').read_text(encoding='utf-8'))
        self.d['주인'] = '시험 참가자'
        self.d['진행'] = dict(zip(w.STAGES, [True, True, True, True, False]))
        self.d['줄기'][0].update(이름='문의', 기록='20-operations/21-work/progress.md')
        self.d['통로'][0].update(이름='메모', 길='직접 넣기')
        self.d['수집스킬'] = 'collect'
        self.d['병목'].update(스킬='process', 통로=['input'], 증상='누락', 입력='input', 출력='제안', 승인기준='본인 확인')
        self.save()
        self.incoming = self.root / 'incoming.md'
        self.incoming.write_text('테스트 원문\n', encoding='utf-8')

    def save(self):
        w.write_yaml(self.root / w.DECL, self.d)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(HERE / 'wiring.py'), '--root', str(self.root), *args], capture_output=True, text=True, encoding='utf-8')

    def proposal(self, uid):
        p = self.root / w.PROPOSALS / (uid + '.md')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('# 제안 ' + uid + '\n', encoding='utf-8')

    def mark(self, uid, n=1):
        progress = self.root / self.d['줄기'][0]['기록']
        progress.write_text(progress.read_text(encoding='utf-8') + '\n<!-- wiring:' + uid + ':' + str(n) + ' -->\n시험 반영\n', encoding='utf-8')

    def evidence(self, **lane):
        self.d['통로'][0].update(범위='채널 하나', 고유키='id', 근거='00-inbox/raw/input/evidence.md', **lane)
        (self.root / '00-inbox/raw/input/evidence.md').write_text('실제 호출 대역', encoding='utf-8')
        self.save()

    # --- 선언과 실물 ---
    def test_ready_and_render_cli(self):
        self.assertEqual(self.run_cli('validate', '--ready').returncode, 0)
        self.assertEqual(self.run_cli('render').returncode, 0)
        view = (self.root / w.BASE / '배선도.md').read_text(encoding='utf-8')
        self.assertIn('문의', view)
        self.d['줄기'][0]['이름'] = '수정된 이름'; self.d['줄기'][0]['내가하는것'] = None; self.save()
        self.assertEqual(self.run_cli('render').returncode, 0)
        view = (self.root / w.BASE / '배선도.md').read_text(encoding='utf-8')
        self.assertIn('수정된 이름', view)
        self.assertNotIn('None', view)  # 빈 칸이 None으로 찍히면 안 된다

    def test_missing_skill_or_same_skill_blocks_ready(self):
        (self.root / '.claude/skills/process/SKILL.md').unlink()
        self.assertNotEqual(self.run_cli('validate', '--ready').returncode, 0)
        self.d['병목']['스킬'] = 'collect'; self.save()
        self.assertNotEqual(self.run_cli('validate', '--ready').returncode, 0)

    def test_unknown_source_and_path_escape(self):
        self.d['줄기'][0]['통로'] = ['unrelated']; self.save()
        self.assertNotEqual(self.run_cli('validate').returncode, 0)
        self.d['줄기'][0]['통로'] = ['input']
        self.d['통로'][0]['원본함'] = '../outside'; self.save()
        self.assertNotEqual(self.run_cli('validate').returncode, 0)

    def test_record_file_must_be_progress_under_projects_or_operations(self):
        self.d['줄기'][0]['기록'] = 'CLAUDE.md'; self.save()
        self.assertNotEqual(self.run_cli('validate', '--ready').returncode, 0)

    def test_duplicate_yaml_key_rejected(self):
        p = self.root / w.DECL
        p.write_text(p.read_text(encoding='utf-8') + '\n주인: 다른 사람\n', encoding='utf-8')
        self.assertNotEqual(self.run_cli('validate').returncode, 0)

    def test_stage_order_and_unfinished(self):
        self.d['진행']['줄기'] = False; self.save()
        self.assertNotEqual(self.run_cli('validate').returncode, 0)
        self.d['진행'] = dict.fromkeys(w.STAGES, False); self.save()
        self.assertNotEqual(self.run_cli('validate', '--ready').returncode, 0)

    def test_missing_declaration_message_points_to_wiring(self):
        (self.root / w.DECL).unlink()
        out = self.run_cli('validate')
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('배선도 그려줘', out.stderr)

    # --- 호출이 실제로 실행 가능한가 ---
    def test_actual_evidence_required(self):
        self.d['통로'][0].update(길='MCP', 호출={'도구': 'mcp__wiki__read', '인자': {'id': 'real-id'}}, 범위='채널 하나', 고유키='id')
        self.save()
        self.assertNotEqual(self.run_cli('validate').returncode, 0)  # 근거 파일 없음
        self.evidence()
        self.assertEqual(self.run_cli('validate', '--ready').returncode, 0)

    def test_placeholders_in_call_rejected(self):
        for ph in ['<시트ID>', 'YOUR_SHEET_ID', '{{시트ID}}', '...']:
            self.evidence(길='CLI', 호출={'argv': [sys.executable, '-c', ph]})
            self.assertNotEqual(self.run_cli('validate').returncode, 0, ph)
        self.evidence(길='CLI', 호출={'argv': [sys.executable, '-c', 'print(1)']})
        self.assertEqual(self.run_cli('validate').returncode, 0)

    def test_cli_executable_must_exist(self):
        self.evidence(길='CLI', 호출={'argv': ['no-such-binary-xyz', 'a']})
        self.assertNotEqual(self.run_cli('validate').returncode, 0)

    def test_mcp_tool_name_and_server(self):
        self.evidence(길='MCP', 호출={'도구': 'read', '인자': {'id': 1}})
        self.assertNotEqual(self.run_cli('validate').returncode, 0)  # mcp__ 접두 없음
        self.evidence(길='MCP', 호출={'도구': 'mcp__wiki__read', '인자': {'id': 1}})
        self.assertEqual(self.run_cli('validate').returncode, 0)  # .mcp.json 없으면 서버 대조 생략
        (self.root / '.mcp.json').write_text(json.dumps({'mcpServers': {'jira': {}}}), encoding='utf-8')
        self.assertNotEqual(self.run_cli('validate').returncode, 0)  # 등록 안 된 서버
        (self.root / '.mcp.json').write_text(json.dumps({'mcpServers': {'wiki': {}}}), encoding='utf-8')
        self.assertEqual(self.run_cli('validate').returncode, 0)

    def test_bottleneck_lanes_must_belong_to_stream(self):
        self.d['병목']['통로'] = []; self.save()
        self.assertNotEqual(self.run_cli('validate').returncode, 0)
        self.d['병목']['통로'] = ['nope']; self.save()
        self.assertNotEqual(self.run_cli('validate').returncode, 0)

    def test_malformed_bottleneck_fails_cleanly(self):
        self.d['병목'] = 'not-a-map'; self.save()
        out = self.run_cli('validate')
        self.assertNotEqual(out.returncode, 0)
        self.assertNotIn('Traceback', out.stderr)

    # --- 수집 재실행·원문 보존 ---
    def test_idempotent_store_preserves_pending(self):
        a = w.store(self.root, self.d, 'input', 'message-1', self.incoming)
        self.proposal(a['id'])
        w.transition(self.root, a['id'], '승인대기', 'proposal.md')
        b = w.store(self.root, self.d, 'input', 'message-1', self.incoming)
        self.assertTrue(a['신규등록']); self.assertFalse(b['신규등록'])
        self.assertEqual(b['상태'], '승인대기')
        self.assertEqual(len(list((self.root / '00-inbox/raw/input').glob('*.md'))), 1)
        self.assertEqual(len(w.queue(self.root, self.d)), 1)

    def test_changed_original_is_not_overwritten(self):
        a = w.store(self.root, self.d, 'input', 'message-1', self.incoming)
        self.incoming.write_text('別の内容', encoding='utf-8')
        with self.assertRaises(ValueError):
            w.store(self.root, self.d, 'input', 'message-1', self.incoming)
        self.assertEqual((self.root / a['원본']).read_text(encoding='utf-8'), '테스트 원문\n')

    def test_non_utf8_original_gets_guidance(self):
        self.incoming.write_bytes('한글'.encode('cp949'))
        out = self.run_cli('store', 'input', 'k', str(self.incoming))
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('UTF-8', out.stderr)

    def test_empty_and_unregistered_source_rejected(self):
        self.incoming.write_text('', encoding='utf-8')
        self.assertNotEqual(self.run_cli('store', 'input', 'empty', str(self.incoming)).returncode, 0)
        self.incoming.write_text('sample', encoding='utf-8')
        self.assertNotEqual(self.run_cli('store', 'unrelated', 'key', str(self.incoming)).returncode, 0)

    def test_intake_registers_dropped_files_once(self):
        drop = self.root / w.DROP / 'input'; drop.mkdir(parents=True)
        (drop / '회의.txt').write_text('회의 원문\n', encoding='utf-8')
        (self.root / '00-inbox/raw/input/메모.md').write_text('원본함에 직접 넣은 것\n', encoding='utf-8')
        self.assertEqual(json.loads(self.run_cli('validate').stdout)['미등록원문'], {'input': ['00-inbox/drop/input/회의.txt', '00-inbox/raw/input/메모.md']})
        out = self.run_cli('intake', 'input')
        self.assertEqual(out.returncode, 0, out.stderr)
        r = json.loads(out.stdout)
        self.assertEqual(sorted(r['등록']), ['메모.md', '회의.txt']); self.assertEqual(r['실패'], [])
        self.assertFalse((drop / '회의.txt').exists()); self.assertFalse((self.root / '00-inbox/raw/input/메모.md').exists())
        self.assertEqual(len([p for p in (self.root / '00-inbox/raw/input').iterdir() if w.STORED_NAME.match(p.name)]), 2)
        self.assertEqual(json.loads(self.run_cli('validate').stdout)['미등록원문'], {})
        again = json.loads(self.run_cli('intake', 'input').stdout)
        self.assertEqual(again['등록'], []); self.assertEqual(again['수집']['건수'], 0); self.assertEqual(again['수집']['결과'], '성공')
        self.assertEqual(len(w.queue(self.root, self.d)), 2)

    def test_intake_failure_keeps_cursor(self):
        drop = self.root / w.DROP / 'input'; drop.mkdir(parents=True)
        (drop / 'a.txt').write_text('a\n', encoding='utf-8')
        first = json.loads(self.run_cli('intake', 'input').stdout)
        self.assertEqual(first['수집']['이어받기'], 'a.txt')
        (drop / 'b.txt').write_bytes('깨진'.encode('cp949'))
        second = json.loads(self.run_cli('intake', 'input').stdout)
        self.assertEqual(second['수집']['결과'], '실패'); self.assertEqual(second['수집']['이어받기'], 'a.txt')
        self.assertTrue((drop / 'b.txt').exists())  # 실패한 파일은 지우지 않는다

    def test_failed_collection_preserves_cursor_and_masks_secrets(self):
        w.collection(self.root, self.d, 'input', True, 'cursor-1', 1, '')
        out = w.collection(self.root, self.d, 'input', False, None, 0, 'Authorization: Bearer sk-live-ABCDEF')
        self.assertEqual(out['이어받기'], 'cursor-1')
        self.assertEqual(out['결과'], '실패')
        self.assertNotIn('sk-live-ABCDEF', (self.root / w.STATE).read_text(encoding='utf-8'))
        out = w.collection(self.root, self.d, 'input', True, 'cursor-2', 0, '')
        self.assertEqual(out['결과'], '성공'); self.assertEqual(out['건수'], 0)

    # --- 승인·재개 ---
    def test_resume_all_nonterminal_states_and_bottleneck_flag(self):
        ids = [w.store(self.root, self.d, 'input', str(i), self.incoming)['id'] for i in range(4)]
        for uid in ids[1:]:
            self.proposal(uid)
            w.transition(self.root, uid, '승인대기', 'proposal')
        for uid in ids[2:]:
            w.transition(self.root, uid, '승인됨', 'test user approval')
        self.mark(ids[3])
        w.transition(self.root, ids[3], '반영완료', 'progress marker')
        q = w.queue(self.root, self.d)
        self.assertEqual({row['상태'] for row in q}, {'신규', '승인대기', '승인됨'})
        self.assertTrue(all(row['병목대상'] for row in q))
        with self.assertRaises(ValueError):
            w.transition(self.root, ids[0], '반영완료', 'no approval')
        with self.assertRaises(ValueError):
            w.transition(self.root, ids[1], '승인됨', '')

    def test_pending_needs_proposal_file_and_done_needs_marker(self):
        uid = w.store(self.root, self.d, 'input', 'k', self.incoming)['id']
        with self.assertRaises(ValueError):
            w.transition(self.root, uid, '승인대기', '없는 제안')
        self.proposal(uid)
        w.transition(self.root, uid, '승인대기', 'proposal')
        w.transition(self.root, uid, '승인됨', 'user said yes')
        with self.assertRaises(ValueError):
            w.transition(self.root, uid, '반영완료', '아무 말')  # 표식 없이 완료 금지
        (self.root / w.BASE / '한바퀴-기록.md').write_text('wiring:' + uid + ':1 은 여기 있어도 반영이 아니다', encoding='utf-8')
        with self.assertRaises(ValueError):
            w.transition(self.root, uid, '반영완료', '00-system 안의 언급')
        self.mark(uid)
        self.assertEqual(w.transition(self.root, uid, '반영완료', 'progress')['상태'], '반영완료')

    def test_missing_original_is_reported_not_fatal(self):
        a = w.store(self.root, self.d, 'input', 'k1', self.incoming)
        w.store(self.root, self.d, 'input', 'k2', self.incoming)
        (self.root / a['원본']).unlink()
        out = self.run_cli('queue')
        self.assertEqual(out.returncode, 0, out.stderr)
        rows = {r['id']: r['원본없음'] for r in json.loads(out.stdout)}
        self.assertEqual(rows[a['id']], True); self.assertEqual(sum(rows.values()), 1)
        self.assertEqual(json.loads(self.run_cli('validate').stdout)['원본없음'], [a['id']])
        self.assertEqual(self.run_cli('store', 'input', 'k3', str(self.incoming)).returncode, 0)

    def test_roundtrip_via_cli(self):
        out = self.run_cli('store', 'input', 'id-1', str(self.incoming))
        self.assertEqual(out.returncode, 0, out.stderr)
        uid = json.loads(out.stdout)['id']
        self.proposal(uid)
        for target, proof in [('승인대기', '제안 파일'), ('승인됨', '시험 승인')]:
            self.assertEqual(self.run_cli('status', uid, target, '--proof', proof).returncode, 0)
        self.assertEqual(len(json.loads(self.run_cli('queue').stdout)), 1)
        self.mark(uid)
        self.assertEqual(self.run_cli('status', uid, '반영완료', '--proof', '반영 위치').returncode, 0)
        self.assertEqual(json.loads(self.run_cli('queue').stdout), [])

    # --- 래퍼·연결 검사 ---
    def test_wrapper_runs_with_picked_python(self):
        out = subprocess.run(['/bin/bash', str(HERE / 'wiring.sh'), '--root', str(self.root), 'validate'], capture_output=True, text=True, encoding='utf-8', cwd=self.root)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(json.loads(out.stdout)['정상'])

    def test_connection_report_hides_config_values(self):
        bins = self.root / 'bin'; bins.mkdir()
        fake_home = self.root / 'fake-home'; fake_home.mkdir()
        for command in ['bash', 'dirname', 'grep', 'head', 'sed', 'tr', 'python3']:
            exe = shutil.which(command)
            if exe:
                (bins / command).symlink_to(exe)
        cli = bins / 'claude'
        cli.write_text('#!/bin/sh\necho "fake list failure" >&2\nexit 7\n'); cli.chmod(0o755)
        marker = 'SYNTHETIC_CREDENTIAL_NOT_A_REAL_SECRET'
        (self.root / '.mcp.json').write_text(json.dumps({'mcpServers': {'test-server': {'env': {'TOKEN': marker}, 'headers': {'Authorization': marker}}}}))
        env = dict(os.environ, PATH=str(bins), HOME=str(fake_home))
        out = subprocess.run(['/bin/bash', str(HERE / 'check_lanes.sh')], cwd=self.root, env=env, capture_output=True, text=True, timeout=10)
        self.assertIn('test-server', out.stdout)
        self.assertNotIn(marker, out.stdout)
        self.assertIn('종료 코드 7', out.stdout)


if __name__ == '__main__':
    unittest.main()
