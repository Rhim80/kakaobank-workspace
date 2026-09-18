# source 해서 쓴다: PY 에 실제로 도는 파이썬 3 이름, PY_VER 에 버전 줄을 넣는다(없으면 둘 다 빈 값).
# check_lanes.sh · test-report/collect_env.sh 가 같이 쓴다 — 파이썬 판정은 여기 한 곳에만 적는다.
# command -v 로 있는지만 보지 않는다: 윈도우에는 python3 라는 이름의 가짜(Microsoft Store 바로가기)가
# 기본으로 깔려 있어 "있음"으로 잡히지만 실행하면 파이썬이 돌지 않는다. --version 이 "Python 3."을 내는 것만 고른다.
PY=""; PY_VER=""
for _c in python3 python py; do
  _v=$("$_c" --version 2>&1) || continue
  case "$_v" in Python\ 3.*) PY="$_c"; PY_VER="$_v"; break ;; esac
done
unset _c _v
