#!/usr/bin/env python3
"""워크스페이스 업데이트 적용 — 3자 비교(지난번 받은 것 / 지금 내 파일 / 이번에 받은 것).

표준 라이브러리만 쓴다. 참가자 기계에 pandas 같은 게 없어도 돈다.

  plan  <zip> [--root DIR]                     무엇이 바뀌는지 JSON으로 출력 (파일은 안 건드림)
  apply <zip> [--root DIR] [--take PATH]...    실제로 적용한다
        [--drop PATH]... [--take-all] [--drop-all]

plan이 내는 갈래:
  add            이번에만 있다 → 넣는다
  update         킷이 바뀌었고 내 파일은 그대로 → 갱신한다
  same           내용이 같다 → 할 일 없음
  yours_modified 킷은 그대로인데 내가 고쳤다 → 안 건드린다
  conflict       킷도 바뀌고 나도 고쳤다 → 물어본다
  unknown        지난번 기록이 없어 누가 고쳤는지 모른다 → 물어본다
  gone           킷에서 없어졌다 → 지우지 않는다. 알리기만
  yours          내가 만든 것 → 안 건드린다

apply는 add·update만 자동으로 한다. **지우는 일은 자동으로 하지 않는다.**
conflict·unknown은 --take, gone은 --drop을 준 것만 처리한다.
덮어쓰거나 지우는 파일은 먼저 .claude/.dbt-backup/<시각>/ 으로 복사한다.

킷에서 빠진 스킬을 자동으로 안 지우는 이유 (이림 2026-08-19):
  "안 고쳤다"는 "안 쓴다"가 아니다. 고치지 않고 그대로 잘 쓰는 게 오히려 정상이고,
  이림이 킷에서 뺀 이유(내가 안 써서)는 참가자 사정과 무관하다.
  남겨서 치르는 값은 안 쓰는 파일 하나가 폴더에 남는 것뿐인데, 지워서 치르는 값은
  잘 쓰던 도구가 말없이 사라지는 것이다. 한쪽이 훨씬 무겁다.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

MANIFEST = ".dbt-version.json"
BACKUP_DIR = ".dbt-backup"
# 비교에서 빼는 것 — 내 기계에만 있는 것, 이 스킬이 만든 것
IGNORE_PREFIX = (BACKUP_DIR + "/",)
IGNORE_NAMES = {MANIFEST, ".DS_Store", "settings.local.json"}


def die(msg):
    print(json.dumps({"error": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ignored(rel: str) -> bool:
    if rel.startswith(IGNORE_PREFIX):
        return True
    return Path(rel).name in IGNORE_NAMES


def read_zip(zip_path: Path):
    """압축을 열어 {상대경로: bytes} 와 매니페스트를 돌려준다."""
    if not zip_path.is_file():
        die(f"압축파일이 없습니다: {zip_path}")
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile:
        die(f"압축파일을 열 수 없습니다: {zip_path}")

    names = [n for n in zf.namelist() if not n.endswith("/")]
    if not names:
        die("압축파일이 비어 있습니다.")

    # 실수로 .claude/ 째로 말린 압축이면 그 한 겹만 벗긴다
    strip = ".claude/"
    if all(n.startswith(strip) for n in names):
        names = [n[len(strip):] for n in names]
        offset = strip
    else:
        offset = ""

    files = {}
    for rel in names:
        # 압축 안 경로로 바깥에 쓰지 못하게 (zip slip)
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts:
            die(f"압축 안에 이상한 경로가 있습니다: {rel}")
        files[rel] = zf.read(offset + rel)

    if MANIFEST not in files:
        die(
            f"이 압축파일에는 {MANIFEST}이 없습니다. "
            "워크스페이스 업데이트 압축파일이 맞는지 확인하세요 "
            "(스킬 하나짜리 압축파일은 그냥 풀어서 .claude/skills 에 넣으면 됩니다)."
        )
    try:
        manifest = json.loads(files[MANIFEST].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        die(f"{MANIFEST}을 읽지 못했습니다: {e}")
    if not isinstance(manifest.get("files"), dict):
        die(f"{MANIFEST}에 files 항목이 없습니다.")
    return files, manifest


def local_files(claude: Path):
    out = {}
    for path in claude.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(claude).as_posix()
        if ignored(rel):
            continue
        out[rel] = sha(path.read_bytes())
    return out


def build_plan(zip_path: Path, root: Path):
    claude = root / ".claude"
    # .claude 만 보면 안 된다 — 클로드 코드를 쓰는 사람은 누구나 홈에 ~/.claude 가 있어서
    # 홈에서 그냥 실행하면 글로벌 설정에 킷이 통째로 들어간다. CLAUDE.md 를 같이 본다.
    if not claude.is_dir() or not (root / "CLAUDE.md").is_file():
        die(f"워크스페이스가 아닙니다: {root} "
            f"(CLAUDE.md·.claude 둘 다 있어야 합니다 — 워크스페이스 폴더를 --root 로 주세요)")

    incoming, manifest = read_zip(zip_path)
    new_hashes = {r: sha(b) for r, b in incoming.items() if not ignored(r)}

    old_path = claude / MANIFEST
    old_manifest = {}
    if old_path.is_file():
        try:
            old_manifest = json.loads(old_path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            old_manifest = {}
    baseline = old_manifest.get("files", {})
    if not isinstance(baseline, dict):
        baseline = {}
    first_run = not baseline

    mine = local_files(claude)
    buckets = {k: [] for k in (
        "add", "update", "same", "yours_modified", "conflict",
        "unknown", "gone", "yours")}

    for rel, new_h in sorted(new_hashes.items()):
        base_h = baseline.get(rel)
        my_h = mine.get(rel)
        if my_h is None:
            buckets["add"].append(rel)
        elif my_h == new_h:
            buckets["same"].append(rel)
        elif base_h is None:
            buckets["unknown"].append(rel)
        elif base_h == my_h:
            buckets["update"].append(rel)
        elif base_h == new_h:
            buckets["yours_modified"].append(rel)
        else:
            buckets["conflict"].append(rel)

    for rel, base_h in sorted(baseline.items()):
        if rel in new_hashes or ignored(rel):
            continue
        if rel in mine:
            buckets["gone"].append(rel)

    for rel in sorted(mine):
        if rel not in new_hashes and rel not in baseline:
            buckets["yours"].append(rel)

    return {
        "root": str(root),
        "zip": str(zip_path),
        "first_run": first_run,
        "incoming": {
            "generated": manifest.get("generated"),
            "commit": manifest.get("commit"),
            "note": manifest.get("note"),
            "file_count": len(new_hashes),
        },
        "baseline": {
            "generated": old_manifest.get("generated"),
            "file_count": len(baseline),
        },
        "counts": {k: len(v) for k, v in buckets.items()},
        "plan": buckets,
    }, incoming, manifest


def apply_plan(plan, incoming, manifest, root: Path, take, drop):
    claude = root / ".claude"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = claude / BACKUP_DIR / stamp
    p = plan["plan"]

    write = list(p["add"]) + list(p["update"])
    write += [r for r in p["conflict"] + p["unknown"] if r in take]
    # 지우는 일은 참가자가 콕 집어 준 것만 (--drop). 자동 삭제 없음
    remove = [r for r in p["gone"] if r in drop]

    unresolved_conflict = [r for r in p["conflict"] if r not in take]
    unresolved_unknown = [r for r in p["unknown"] if r not in take]
    unresolved_gone = [r for r in p["gone"] if r not in drop]

    backed_up = []
    for rel in write + remove:
        src = claude / rel
        if src.is_file():
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up.append(rel)

    for rel in write:
        dst = claude / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(incoming[rel])
        # 실행 권한 유지 (스크립트가 있다)
        if rel.endswith(".sh") or rel.endswith(".py"):
            os.chmod(dst, 0o755)

    for rel in remove:
        target = claude / rel
        if target.is_file():
            target.unlink()
            parent = target.parent
            while parent != claude and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

    # 다음 비교의 기준 = 이번에 킷이 보낸 내용 그대로
    (claude / MANIFEST).write_bytes(incoming[MANIFEST])

    return {
        "applied": {
            "added": p["add"],
            "updated": p["update"],
            "resolved_take": [r for r in write if r in take],
            "deleted": remove,
        },
        "left_alone": {
            "conflict": unresolved_conflict,
            "unknown": unresolved_unknown,
            "gone": unresolved_gone,
            "yours": p["yours"],
            "yours_modified": p["yours_modified"],
        },
        "backup": str(backup) if backed_up else None,
        "version_now": manifest.get("generated"),
    }


def main():
    ap = argparse.ArgumentParser(description="워크스페이스 업데이트 적용")
    ap.add_argument("command", choices=["plan", "apply"])
    ap.add_argument("zip")
    ap.add_argument("--root", default=".", help="워크스페이스 루트 (기본: 현재 폴더)")
    ap.add_argument("--take", action="append", default=[],
                    help="충돌 파일 중 킷 것으로 받을 경로 (여러 번 가능)")
    ap.add_argument("--drop", action="append", default=[],
                    help="킷에서 빠진 파일 중 참가자가 지우기로 한 경로 (여러 번 가능)")
    ap.add_argument("--take-all", action="store_true", help="충돌 전부 킷 것으로")
    ap.add_argument("--drop-all", action="store_true", help="없어진 것 전부 지움")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    plan, incoming, manifest = build_plan(Path(args.zip).resolve(), root)

    if args.command == "plan":
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    take = set(args.take)
    drop = set(args.drop)
    if args.take_all:
        take |= set(plan["plan"]["conflict"]) | set(plan["plan"]["unknown"])
    if args.drop_all:
        drop |= set(plan["plan"]["gone"])

    result = apply_plan(plan, incoming, manifest, root, take, drop)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
