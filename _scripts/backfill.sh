#!/usr/bin/env bash
# backfill.sh FROM TO [PARALLEL=3] [--commit-every N]
# 2단계 백필:
#   A) discover(WebSearch) + collect  — 출력 토큰이 적어 PARALLEL개 병렬로 돌려도 안전
#   B) write(LLM 작성, 출력 2~3만 토큰) + build — 계정 rate limit 때문에 **직렬**. N호마다 커밋·푸시(pull --rebase 후).
# 이미 editions/DATE.html 이 있으면 건너뛴다. 중단 후 재실행하면 남은 것만 이어서 한다.
set -uo pipefail
FROM="${1:?usage: backfill.sh FROM TO [PARALLEL] [--commit-every N]}"; TO="${2:?}"; PAR="${3:-3}"
EVERY=5; for ((i=1;i<=$#;i++)); do [ "${!i}" = "--commit-every" ] && { j=$((i+1)); EVERY="${!j}"; }; done
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$HERE")"
DATES=$(python3 -c "
import datetime as d
a=d.date.fromisoformat('$FROM'); b=d.date.fromisoformat('$TO')
while a<=b: print(a.isoformat()); a+=d.timedelta(days=1)")
prepA() {
  local D="$1"; local WD="$HERE/work/$D"; mkdir -p "$WD"
  [ -f "$ROOT/editions/$D.html" ] && return 0
  [ -f "$WD/newsletter.json" ] && return 0
  [ -f "$WD/websearch.json" ] || "$HERE/discover.sh" "$D" 2>>"$WD/log.txt" || echo "[backfill] $D discover 실패(계속)"
  [ -f "$WD/candidates.json" ] && [ "$WD/candidates.json" -nt "$WD/websearch.json" ] || python3 "$HERE/collect.py" "$D" 2>>"$WD/log.txt" >/dev/null
  echo "[backfill] $D A(수집) 완료"
}
export -f prepA; export HERE ROOT
echo "$DATES" | xargs -P "$PAR" -I{} bash -c 'prepA {}'
commit_push() {
  cd "$ROOT" || return 1
  git add editions index.html _scripts/*.py _scripts/*.sh _scripts/*.md _scripts/*.json _scripts/.gitignore _TEMPLATE_edition.html AGENT.md 2>/dev/null
  git diff --cached --quiet && return 0
  local N; N=$(ls editions | grep -c html)
  git commit -q -m "publish \"데일리 뉴스레터 백필 $1 (누적 ${N}호)\"

collect.py(HN·RSS) + discover.sh(WebSearch) → write.py(claude -p) → build.py 파이프라인으로
발행일 기준 직전 24시간 뉴스를 날짜별로 요약해 아카이브에 추가.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" --no-verify || return 1
  git pull -q --rebase origin main && git push -q origin main && echo "[backfill] pushed ($1, 누적 ${N}호)"
}
n=0; first=""
for D in $DATES; do
  [ -f "$ROOT/editions/$D.html" ] && continue
  WD="$HERE/work/$D"
  if [ ! -f "$WD/newsletter.json" ]; then
    [ -f "$WD/candidates.json" ] || { echo "[backfill] $D candidates 없음 — 건너뜀"; continue; }
    python3 "$HERE/write.py" "$D" 2>>"$WD/log.txt" || { echo "[backfill] $D write 실패 — 재시도"; python3 "$HERE/write.py" "$D" 2>>"$WD/log.txt" || { echo "[backfill] $D write 실패(2회) — 건너뜀"; continue; }; }
  fi
  python3 "$HERE/build.py" "$D" 2>&1 | grep -v "^\[build\] WARN" || echo "[backfill] $D build 실패"
  [ -f "$ROOT/editions/$D.html" ] || continue
  [ -z "$first" ] && first="$D"; n=$((n+1))
  if [ $((n % EVERY)) -eq 0 ]; then commit_push "$first~$D"; first=""; fi
done
[ -n "$first" ] && commit_push "$first~$D"
echo "[backfill] 끝. 발행된 호: $(ls "$ROOT/editions" | grep -c html)"
