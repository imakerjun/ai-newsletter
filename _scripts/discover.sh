#!/usr/bin/env bash
# discover.sh DATE → _scripts/work/DATE/websearch.json
# claude -p + WebSearch 로 해당 날짜(±1일)의 주요 AI 뉴스와 직무 활용 기사(최근 2주)를 보강 수집한다.
# 로컬 백필용. 클라우드 루틴에서는 에이전트가 같은 검색을 직접 수행해 같은 파일을 쓴다.
set -euo pipefail
DATE="${1:?usage: discover.sh YYYY-MM-DD}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/work/$DATE"; mkdir -p "$OUT"
MODEL="${NL_MODEL:-sonnet}"
PREV=$(python3 -c "import datetime as d;print((d.date.fromisoformat('$DATE')-d.timedelta(days=1)).isoformat())")
TWOWK=$(python3 -c "import datetime as d;print((d.date.fromisoformat('$DATE')-d.timedelta(days=14)).isoformat())")
SCHEMA='{"type":"object","properties":{"items":{"type":"array","items":{"type":"object","properties":{"title":{"type":"string"},"url":{"type":"string"},"source":{"type":"string"},"published":{"type":"string","description":"YYYY-MM-DD"},"summary":{"type":"string"},"role":{"type":"string","enum":["","planner","data","pm","dev_edu"]}},"required":["title","url","source","published","summary","role"]}},"note":{"type":"string"}},"required":["items","note"]}'
PROMPT="You are a research assistant for a Korean daily AI newsletter. Use the WebSearch tool. Budget: at most 15 searches total (batch several per turn). After the searches, stop searching and answer with the JSON — do not keep verifying.

Part A — News for the edition dated $DATE (news published between $PREV and $DATE, i.e. the 24 hours before $DATE 08:00 KST; ±1 day tolerance):
- Searches (8): \"AI news $DATE\", \"OpenAI $DATE\", \"Anthropic Claude $DATE\", \"Google Gemini DeepMind $DATE\", \"AI 뉴스 $DATE\" (Korean), \"AI 발표 $DATE\" (Korean), \"new AI model API OR SDK release OR open source OR eval benchmark $DATE\" (developer angle), \"AI education OR AI curriculum OR coding agent tutorial $DATE\" (AI-educator angle).
- Return 8-14 significant AI industry items: new models/features/policy/major launches/partnerships, PLUS developer-facing items (new model APIs/SDKs, coding agents, evals, prompt engineering, open-source releases) and AI-educator items (courses, curricula, teaching case studies). Tag developer/educator items with role=\"dev_edu\"; general items keep role=\"\". Prefer official blogs and major media (1st-party reporting). Date evidence may come from the URL path (e.g. /2026/07/15/), the snippet, or the result's date label; ±1 day tolerance is fine — do not drop items just because the exact hour is unknown.

Part B — Role use-cases (evergreen; published within the ~60 days before $DATE, the newer the better):
- Searches (5), one per line, each biased to the last 2 months: (1) \"Excel Copilot OR Google Sheets Gemini new feature\" (data), (2) \"natural language BI OR text-to-SQL for analysts announcement\" (data), (3) \"Notion AI OR Figma AI OR Miro AI update for product planning\" (planner), (4) \"ChatGPT deep research OR Gemini deep research for market research use case\" (planner), (5) \"AI for product managers PRD OR meeting notes OR feedback triage OR Jira Linear AI\" (pm).
- Return 5-8 items with role set to planner / data / pm (at least one per role if found). Only concrete articles, blog posts or official release notes with a visible date — never a product homepage. Prefer official release notes and reputable media.

Rules: include only URLs you actually saw in search results; published must be the real publication date (YYYY-MM-DD) as shown in results — if you truly cannot infer a date, omit the item. summary = 1-2 English or Korean sentences of what the article says. In note, list how many searches you ran."
cd "$OUT"
claude -p --model "$MODEL" --strict-mcp-config --setting-sources "" \
  --permission-mode bypassPermissions --allowedTools "WebSearch" --max-turns 30 \
  --output-format json --json-schema "$SCHEMA" "$PROMPT" < /dev/null > websearch.raw.json
python3 - <<'PY'
import json,sys
d=json.load(open("websearch.raw.json"))
so=d.get("structured_output")
if d.get("is_error") or not so:
    print("[discover] FAIL", d.get("is_error"), (d.get("result") or "")[:300], file=sys.stderr); sys.exit(1)
json.dump(so, open("websearch.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"[discover] items={len(so['items'])} cost=${d.get('total_cost_usd',0):.2f} turns={d.get('num_turns')} | {so.get('note','')[:160]}", file=sys.stderr)
PY
