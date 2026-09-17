#!/usr/bin/env bash
# publish.sh DATE [--no-discover] [--force]
# 한 호 발행(로컬): collect → discover(WebSearch 보강) → collect(병합) → write → build.
# 커밋·푸시는 하지 않는다(backfill.sh 또는 사람이 묶어서).
set -euo pipefail
DATE="${1:?usage: publish.sh YYYY-MM-DD [--no-discover] [--force]}"; shift || true
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
DISCOVER=1; FORCE=""
for a in "$@"; do case "$a" in --no-discover) DISCOVER=0;; --force) FORCE="--force";; esac; done
if [ -f "$ROOT/editions/$DATE.html" ] && [ -z "$FORCE" ]; then echo "[publish] $DATE 이미 발행됨 — skip"; exit 0; fi
WD="$HERE/work/$DATE"; mkdir -p "$WD"
if [ "$DISCOVER" = 1 ] && [ ! -f "$WD/websearch.json" ]; then
  "$HERE/discover.sh" "$DATE" || echo "[publish] discover 실패 — 피드/HN만으로 진행"
fi
python3 "$HERE/collect.py" "$DATE" 2>>"$WD/log.txt"
[ -f "$WD/newsletter.json" ] && [ -z "$FORCE" ] || python3 "$HERE/write.py" "$DATE" 2>>"$WD/log.txt"
python3 "$HERE/build.py" "$DATE" $FORCE 2>&1 | tee -a "$WD/log.txt"
