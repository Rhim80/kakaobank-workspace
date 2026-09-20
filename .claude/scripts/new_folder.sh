#!/usr/bin/env bash
# 번호 붙은 폴더를 만든다 — 번호는 사람도 Claude도 세지 않는다, 이 스크립트가 센다.
# 쓰는 법:  bash .claude/scripts/new_folder.sh <상위폴더> <이름> [progress]
#   10-projects 아래     → 11-이름, 12-이름 …  (영역 10 → 항목 11부터)
#   10-projects/11-x 아래 → 11.01-이름, 11.02-이름 …
#   세 번째 인자 progress 를 주면 00-system/01-templates/progress-template.md 를 복사해 progress.md 를 만든다.
# 만든 경로를 마지막 줄에 찍는다. 실패하면 종료 코드 1 + 이유.
set -u
parent="${1:-}"; name="${2:-}"; want_progress="${3:-}"
[ -z "$parent" ] || [ -z "$name" ] && { echo "쓰는 법: new_folder.sh <상위폴더> <이름> [progress]"; exit 1; }
[ -d "$parent" ] || { echo "상위 폴더가 없다: $parent"; exit 1; }
name="${name// /-}"
base=$(basename "$parent")
if [[ "$base" =~ ^([0-9])0-[^/]+$ ]]; then
  # 영역 폴더(10-projects 등): 자식은 두 자리 번호, 영역 첫 자리+1 부터
  first="${BASH_REMATCH[1]}"; start=$((first*10+1))
  last=$(ls -1 "$parent" | sed -n 's/^\([0-9][0-9]\)-.*/\1/p' | sort -n | tail -1)
  if [ -z "$last" ]; then n=$start; else n=$((10#$last+1)); fi
  [ $n -gt $((first*10+9)) ] && { echo "영역 $base 에 자리가 없다(마지막 $last). 사람이 정리해야 한다"; exit 1; }
  prefix=$(printf '%02d' "$n")
elif [[ "$base" =~ ^([0-9][0-9])-[^/]+$ ]]; then
  # 항목 폴더(11-x): 자식은 11.01-이름
  cat_no="${BASH_REMATCH[1]}"
  last=$(ls -1 "$parent" | sed -n "s/^${cat_no}\.\([0-9][0-9]\)-.*/\1/p" | sort -n | tail -1)
  if [ -z "$last" ]; then n=1; else n=$((10#$last+1)); fi
  prefix="${cat_no}.$(printf '%02d' "$n")"
else
  echo "번호 규칙이 없는 폴더다: $parent (10-projects 같은 영역 폴더나 11-이름 같은 항목 폴더 아래에만 만든다)"; exit 1
fi
dup=$(ls -1 "$parent" | grep -E "^[0-9.]+-${name}$" | head -1)
[ -n "$dup" ] && { echo "같은 이름이 이미 있다: $parent/$dup (번호만 다른 폴더를 또 만들지 않는다)"; exit 1; }
dir="$parent/$prefix-$name"
[ -e "$dir" ] && { echo "이미 있다: $dir"; exit 1; }
mkdir -p "$dir" || exit 1
if [ "$want_progress" = "progress" ]; then
  today=$(date +%Y-%m-%d)
  tpl="00-system/01-templates/progress-template.md"
  if [ -f "$tpl" ]; then
    # 킷 템플릿을 그대로 쓴다 — 형식의 원본은 템플릿 하나(ripple도 같은 파일을 쓴다)
    sed -e "s/\[프로젝트명\]/$name/" -e "s/YYYY-MM-DD/$today/g" "$tpl" > "$dir/progress.md"
  else
    echo "(템플릿 $tpl 이 없어 progress.md를 만들지 않았다 — 폴더만 만들었다)"
  fi
fi
echo "$dir"
