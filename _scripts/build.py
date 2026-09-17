#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py DATE [--force] [--preview]

_scripts/work/DATE/newsletter.json + candidates.json → editions/DATE.html, index.html(ARCHIVE.editions) 갱신.
  - 검증: 5탭·필수 필드·tint·url이 후보(candidates/role_pool)에 실제로 있는지·url 중복·published 형식.
  - 기존 editions/DATE.html 이 있으면 --force 없이는 건드리지 않는다(과거 호 보존).
  - Vol 번호 = 시간순 연번(해당 날짜보다 앞선 호 수 + 1). 아카이브 목록은 날짜 내림차순 유지.
  - --preview: editions/index 를 건드리지 않고 work/DATE/preview.html 만 만든다.
"""
import sys, os, re, json, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(HERE, "work")
TPL = os.path.join(ROOT, "_TEMPLATE_edition.html")
INDEX = os.path.join(ROOT, "index.html")
WEEKDAY = "월화수목금토일"
TABS = {
    "news":     dict(label="AI 최신 소식", icon="📰", tint="blue"),
    "everyone": dict(label="비개발자를 위한 AI 소식", icon="🧭", tint="green"),
    "planner":  dict(label="기획자를 위한 AI 소식", icon="💡", tint="purple"),
    "data":     dict(label="데이터 분석을 위한 AI 소식", icon="📊", tint="orange"),
    "pm":       dict(label="PM을 위한 AI 소식", icon="📋", tint="pink"),
}
TINTS = {"blue", "purple", "green", "orange", "pink"}


def fail(msg):
    print("[build] ERROR", msg, file=sys.stderr); sys.exit(1)


def norm(u):
    return re.sub(r"[?#].*$", "", u.strip()).rstrip("/").lower().replace("http://", "https://").replace("://www.", "://")


def validate(nl, cands):
    allowed = {norm(c["url"]): c for c in cands["candidates"] + cands["role_pool"]}
    ids = [t["id"] for t in nl["topics"]]
    if ids != list(TABS):
        fail(f"탭 순서/구성이 다릅니다: {ids}")
    seen = set()
    problems = []
    for t in nl["topics"]:
        items = [("highlight", t["highlight"])] + [("article", a) for a in t["articles"]]
        keep = []
        for kind, it in items:
            k = norm(it.get("url", ""))
            c = allowed.get(k)
            if not c:
                problems.append(f"{t['id']}/{kind}: 후보 밖 URL → 제거: {it.get('url')}")
                continue
            if k in seen:
                problems.append(f"{t['id']}/{kind}: URL 중복 → 제거: {it.get('url')}")
                continue
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", it.get("published", "")):
                it["published"] = c.get("published_date") or ""
                if not it["published"]:
                    problems.append(f"{t['id']}/{kind}: published 없음 → 제거"); continue
            for f in ("title", "summary", "detail", "foryou", "source"):
                if not it.get(f):
                    problems.append(f"{t['id']}/{kind}: {f} 비어있음 → 제거"); break
            else:
                seen.add(k); keep.append((kind, it))
        hl = [it for kind, it in keep if kind == "highlight"]
        arts = [it for kind, it in keep if kind == "article"]
        if not hl:
            if not arts:
                fail(f"{t['id']}: 유효 항목이 없습니다. newsletter.json 을 다시 생성하세요.")
            a = arts.pop(0)  # 첫 article 을 highlight 로 승격
            t["highlight"] = dict(kicker="오늘의 핵심" if t["id"] in ("news", "everyone") else "이 역할의 핵심 활용",
                                  title=a["title"], summary=a["summary"], detail=a["detail"], source=a["source"], url=a["url"],
                                  published=a["published"], foryou=a["foryou"])
            problems.append(f"{t['id']}: highlight 제거되어 article 승격")
        t["articles"] = arts
        if t["id"] in ("planner", "data", "pm"):
            for a in t["articles"]:
                a["time"] = ""
    return problems


def render_data(date, nl, vol):
    D = dt.date.fromisoformat(date)
    w = WEEKDAY[D.weekday()]
    topics = []
    for t in nl["topics"]:
        meta = TABS[t["id"]]
        topics.append({"id": t["id"], "label": meta["label"], "icon": meta["icon"], "tint": meta["tint"],
                       "desc": t["desc"], "criteria": t["criteria"], "highlight": t["highlight"], "articles": t["articles"]})
    return {
        "meta": {
            "icon": "🗞️", "edition": f"Vol.{vol:02d}", "cadence": "일간",
            "date": f"{D.year}년 {D.month}월 {D.day}일 ({w})",
            "curator": "러닝 에이전트 (Claude Code)", "reader": "메이커준",
            "title": ["데일리 ", "AI 뉴스레터"],
            "lead": "발행일 기준 지난 24시간의 AI 소식과 직무별 활용을 탭으로 나눠 전합니다. 탭마다 ‘딱 하나의 핵심’을 크게, ‘자세히 보기’엔 예시와 함께 길게 풀어 담았어요.",
            "greeting": nl["greeting"],
        },
        "topics": topics,
    }, w


def inject(tpl, data):
    start = tpl.index("const NEWSLETTER = {")
    end = tpl.index("\n};", start) + 3
    return tpl[:start] + "const NEWSLETTER = " + json.dumps(data, ensure_ascii=False, indent=2) + ";" + tpl[end:]


def load_archive(index_html):
    s = index_html.index("const ARCHIVE = {")
    e = index_html.index("\n};", s) + 3
    return json.loads(index_html[s + len("const ARCHIVE = "):e - 1]), s, e


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    date = sys.argv[1]
    force, preview = "--force" in sys.argv, "--preview" in sys.argv
    wd = os.path.join(WORK, date)
    nl = json.load(open(os.path.join(wd, "newsletter.json"), encoding="utf-8"))
    cands = json.load(open(os.path.join(wd, "candidates.json"), encoding="utf-8"))
    problems = validate(nl, cands)
    for p in problems:
        print("[build] WARN", p, file=sys.stderr)

    index_html = open(INDEX, encoding="utf-8").read()
    archive, s, e = load_archive(index_html)
    eds = [x for x in archive["editions"] if not x.get("demo")]
    out_path = os.path.join(ROOT, "editions", f"{date}.html")
    exists = os.path.exists(out_path) or any(x["date"] == date for x in eds)
    if exists and not force and not preview:
        fail(f"{date} 호가 이미 있습니다. 덮어쓰려면 --force")
    others = [x for x in eds if x["date"] != date]
    vol = sum(1 for x in others if x["date"] < date) + 1
    data, w = render_data(date, nl, vol)
    html = inject(open(TPL, encoding="utf-8").read(), data)
    # 주입 결과 재파싱 검증
    chk = html[html.index("const NEWSLETTER = ") + len("const NEWSLETTER = "):]
    json.loads(chk[:chk.index("\n};") + 2])

    if preview:
        p = os.path.join(wd, "preview.html"); open(p, "w", encoding="utf-8").write(html)
        print(f"[build] preview → {p} (Vol.{vol:02d})", file=sys.stderr); return

    open(out_path, "w", encoding="utf-8").write(html)
    entry = {"date": date, "weekday": w, "label": f"Vol.{vol:02d}", "title": nl["lead_title"],
             "topics": ["AI 최신 소식", "비개발자를 위한 AI 소식"], "href": f"editions/{date}.html"}
    others.append(entry)
    others.sort(key=lambda x: x["date"], reverse=True)
    # 새 호 뒤에 오는 호들의 Vol 재번호(백필로 중간 삽입 시). 라벨은 시간순 연번.
    for i, x in enumerate(sorted(others, key=lambda x: x["date"])):
        x["label"] = f"Vol.{i + 1:02d}"
    archive["editions"] = others
    archive["meta"]["cadence"] = "매일"
    archive["meta"]["lead"] = archive["meta"]["lead"].replace("매일(영업일)", "매일")
    new_index = index_html[:s] + "const ARCHIVE = " + json.dumps(archive, ensure_ascii=False, indent=2) + ";" + index_html[e:]
    open(INDEX, "w", encoding="utf-8").write(new_index)
    print(f"[build] {date} Vol.{vol:02d} → editions/{date}.html, index.html({len(others)}호)", file=sys.stderr)


if __name__ == "__main__":
    main()
