#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write.py DATE  →  _scripts/work/DATE/newsletter.json

candidates.json 을 WRITER_PROMPT.md 에 끼워 `claude -p --json-schema` 로 뉴스레터 데이터를 생성한다(로컬 백필용).
클라우드 루틴에서는 에이전트가 같은 프롬프트를 읽고 newsletter.json 을 직접 쓴다(`--prompt-only` 로 프롬프트만 출력).
환경변수 NL_MODEL(기본 sonnet), NL_EFFORT(기본 medium).
"""
import sys, os, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")


def build_prompt(date):
    c = json.load(open(os.path.join(WORK, date, "candidates.json"), encoding="utf-8"))
    slim = {"candidates": [], "role_pool": []}
    for k in slim:
        for it in c[k]:
            slim[k].append({kk: it[kk] for kk in ("title", "url", "source", "lang", "published_date", "hours_before_publish", "score", "summary", "text", "roles") if it.get(kk) not in (None, "", [], 0)})
    tpl = open(os.path.join(HERE, "WRITER_PROMPT.md"), encoding="utf-8").read()
    return (tpl.replace("{DATE}", date).replace("{WINDOW}", str(c["window_hours"]))
            .replace("{WINDOW_START}", c["window_start"][:16]).replace("{PUBLISH_AT}", c["publish_at"][:16])
            .replace("{N_CAND}", str(len(c["candidates"]))).replace("{N_ROLE}", str(len(c["role_pool"])))
            .replace("{CANDIDATES}", json.dumps(slim, ensure_ascii=False, indent=0)))


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    date = sys.argv[1]
    prompt = build_prompt(date)
    if "--prompt-only" in sys.argv:
        print(prompt); return
    outdir = os.path.join(WORK, date)
    schema_obj = json.load(open(os.path.join(HERE, "newsletter.schema.json"), encoding="utf-8"))
    schema_obj.pop("$schema", None)
    schema = json.dumps(schema_obj, ensure_ascii=False)
    model = os.environ.get("NL_MODEL", "sonnet")
    effort = os.environ.get("NL_EFFORT", "medium")
    pf = os.path.join(outdir, "writer.prompt.md")
    open(pf, "w", encoding="utf-8").write(prompt)
    cmd = ["claude", "-p", "--model", model, "--effort", effort, "--strict-mcp-config", "--setting-sources", "",
           "--tools", "", "--output-format", "json", "--json-schema", schema, prompt]
    print(f"[write] claude -p model={model} prompt_chars={len(prompt)}", file=sys.stderr, flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=outdir, timeout=1500, stdin=subprocess.DEVNULL)
    open(os.path.join(outdir, "writer.raw.json"), "w", encoding="utf-8").write(r.stdout)
    if r.returncode != 0:
        print("[write] claude exit", r.returncode, r.stderr[-800:], file=sys.stderr); sys.exit(1)
    d = json.loads(r.stdout)
    so = d.get("structured_output")
    if d.get("is_error") or not so:
        print("[write] FAIL", d.get("is_error"), (d.get("result") or "")[:400], file=sys.stderr); sys.exit(1)
    json.dump(so, open(os.path.join(outdir, "newsletter.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[write] ok cost=${d.get('total_cost_usd', 0):.2f} out_tokens={d.get('usage', {}).get('output_tokens')} → {outdir}/newsletter.json", file=sys.stderr)


if __name__ == "__main__":
    main()
