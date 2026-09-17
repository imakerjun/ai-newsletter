#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect.py DATE  →  _scripts/work/DATE/candidates.json

발행일(DATE, Asia/Seoul 08:00 발행 기준) 직전 24시간의 AI 뉴스 후보를 모은다.
표준 라이브러리만 사용한다 — 로컬(백필)과 클라우드 루틴 샌드박스 어디서든 그대로 실행되도록.

소스
  - Hacker News (Algolia API, created_at 범위 필터)            → 원문 URL·점수
  - RSS/Atom 피드(OpenAI·DeepMind·HF·Google AI·TechCrunch·Verge·Ars·MIT TR·AI타임스·ZDNet Korea·바이라인)
  - (선택) work/DATE/websearch.json — discover.sh 가 만든 WebSearch 보강 결과

후보가 MIN_CANDIDATES 미만이면 윈도우를 48h → 72h로 넓힌다(widened_hours에 기록).
직무 탭(planner/data/pm)용 role_pool 은 최근 14일 후보 중 역할 키워드 매칭으로 따로 담는다.
"""
import sys, os, re, json, html, time, subprocess, datetime as dt, urllib.request, urllib.parse
from urllib.error import URLError
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "_scripts", "work")
KST = dt.timezone(dt.timedelta(hours=9))
UTC = dt.timezone.utc
PUBLISH_HOUR_KST = 8
MIN_CANDIDATES = 12
MAX_TEXT = 2500
ROLE_DAYS = 14
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 ai-newsletter-bot"}

FEEDS = [
    # (source label, url, lang)
    ("OpenAI", "https://openai.com/news/rss.xml", "en"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml", "en"),
    ("Hugging Face 블로그", "https://huggingface.co/blog/feed.xml", "en"),
    ("Google AI 블로그", "https://blog.google/technology/ai/rss/", "en"),
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/", "en"),
    ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "en"),
    ("Ars Technica", "https://arstechnica.com/ai/feed/", "en"),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/", "en"),
    ("AI타임스", "https://www.aitimes.com/rss/allArticle.xml", "ko"),
    ("ZDNet Korea", "https://feeds.feedburner.com/zdkorea", "ko"),
    ("바이라인네트워크", "https://byline.network/feed/", "ko"),
    # 개발자·AI 교육자 관점 소스 (Anthropic 은 공식 RSS 미제공 — HN·WebSearch 로 보완)
    ("GitHub 블로그", "https://github.blog/feed/", "en"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/", "en"),
    ("InfoQ AI/ML", "https://feed.infoq.com/ai-ml-data-eng/", "en"),
]

AI_KW = re.compile(r"\b(AI|A\.I\.|LLM|LLMs|OpenAI|Anthropic|Claude|Gemini|GPT[-\d]*|ChatGPT|DeepMind|Copilot|agent|agents|agentic|model|models|Mistral|Llama|xAI|Grok|Nvidia|NVIDIA|Hugging ?Face|Cursor|Codex|Sora|Midjourney|diffusion|transformer|inference|GPU|TPU|machine learning|deep learning|neural|chatbot|Perplexity|Meta AI|Apple Intelligence|Siri|Alexa|robot|robotics|autonomous|Waymo|Tesla FSD|Scale AI|Databricks|Snowflake|Notion|Figma)\b|인공지능|생성형|챗GPT|오픈AI|앤트로픽|클로드|제미나이|엔비디아|에이전트|딥마인드|거대언어|LLM", re.I)
# 개발자·AI 교육자 관점(사용자 지정, 2026-09-18): 모델 API/SDK, 코딩 에이전트, 평가·프롬프트 엔지니어링, 오픈소스, AI 교육
DEV_EDU_KW = re.compile(r"\b(API|SDK|open[- ]?source|open[- ]?weight|fine-?tun\w*|benchmark|eval(uation)?s?|prompt engineering|context window|token|inference cost|coding agent|code review|pull request|GitHub Copilot|Claude Code|Codex|Cursor|Windsurf|MCP|Model Context Protocol|RAG|retrieval|vector (db|database)|embedding|quantiz\w*|LoRA|RLHF|RLAIF|system prompt|jailbreak|red[- ]?team|hallucinat\w*|curriculum|syllabus|bootcamp|workshop|teaching|tutorial|course|classroom|edtech)\b|파인튜닝|오픈소스|오픈\s?웨이트|프롬프트\s?엔지니어링|코딩\s?에이전트|평가셋|벤치마크|커리큘럼|강의|교육과정|워크숍|튜토리얼", re.I)
# 한국어 피드(AI타임스 등)는 이미 AI 매체라 별도 필터 없이 포함, 종합지(ZDNet·바이라인)는 키워드 필터 적용.
ROLE_KW = {
    "planner": re.compile(r"product|roadmap|user research|survey|brainstorm|Notion|Figma|Miro|Canva|prototype|PRD|planning|기획|리서치|프로토타입|노션|피그마|Deep Research|deep research|Gamma|Slides|presentation", re.I),
    "data":    re.compile(r"Excel|spreadsheet|Sheets|SQL|analytics|analysis|dashboard|Tableau|Power BI|Looker|Databricks|Snowflake|BigQuery|pandas|data analyst|Genie|Copilot in Excel|엑셀|스프레드시트|데이터 분석|대시보드|분석", re.I),
    "pm":      re.compile(r"product manager|PM\b|PRD|Jira|Linear|Asana|Productboard|Slack|Teams|meeting notes|transcript|release notes|feedback|prioriti|roadmap|회의록|피드백|우선순위|릴리스 노트|Confluence|Zoom|Granola|Otter|Fireflies", re.I),
}
ROLE_ANY = re.compile("|".join(p.pattern for p in ROLE_KW.values()), re.I)


def log(*a):
    print("[collect]", *a, file=sys.stderr, flush=True)


def http_get(url, timeout=25):
    """urllib 로 받되, 로컬 macOS 에서 종종 나는 'Missing Authority Key Identifier' SSL 검증
    실패(파이썬 3.13+가 시스템 키체인보다 엄격 — curl/브라우저는 통과)는 curl 로 폴백한다."""
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
    except URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        cp = subprocess.run(["curl", "-sSL", "--max-time", str(timeout), "-A", UA["User-Agent"], url],
                            capture_output=True, timeout=timeout + 5)
        if cp.returncode != 0 or not cp.stdout:
            raise
        raw, ctype = cp.stdout, ""
    m = re.search(r"charset=([\w-]+)", ctype)
    enc = m.group(1) if m else "utf-8"
    try:
        return raw.decode(enc, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=UTC)
        return d
    except Exception:
        pass
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=UTC)
        return d
    except Exception:
        pass
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})", s)
    if m:  # AI타임스 등: 로컬(KST) 시각으로 간주
        return dt.datetime(*map(int, m.groups()), tzinfo=KST)
    return None


class _Text(HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "aside", "noscript", "svg", "form", "button"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.in_article, self.article_parts = [], 0, False, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in ("article", "main"):
            self.in_article = True
        if tag in ("p", "br", "li", "h1", "h2", "h3", "div"):
            (self.article_parts if self.in_article else self.parts).append(" ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in ("article", "main"):
            self.in_article = False

    def handle_data(self, data):
        if self.skip:
            return
        (self.article_parts if self.in_article else self.parts).append(data)

    def text(self):
        t = "".join(self.article_parts) if len("".join(self.article_parts)) > 400 else "".join(self.parts)
        return re.sub(r"\s+", " ", t).strip()


def page_text(url):
    """원문 페이지 본문 앞부분(MAX_TEXT자). 실패하면 빈 문자열."""
    try:
        h = http_get(url, timeout=20)
    except Exception as e:
        return "", f"{type(e).__name__}"
    p = _Text()
    try:
        p.feed(h)
    except Exception:
        return "", "parse"
    return p.text()[:MAX_TEXT], ""


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _tag(block, name):
    """<name ...>내용</name> 첫 매치의 내용(CDATA 해제). 네임스페이스 접두어 허용."""
    m = re.search(r"<(?:\w+:)?%s(?:\s[^>]*)?>(.*?)</(?:\w+:)?%s>" % (name, name), block, re.S | re.I)
    if not m:
        return ""
    v = m.group(1).strip()
    m2 = re.match(r"^<!\[CDATA\[(.*)\]\]>$", v, re.S)
    return (m2.group(1) if m2 else v).strip()


def fetch_feed(label, url, lang):
    """RSS 2.0 / Atom 피드를 정규식으로 파싱한다(expat 없는 파이썬에서도 동작)."""
    try:
        raw = http_get(url, timeout=40)
    except Exception as e:
        log(f"feed FAIL {label}: {e}")
        return []
    out = []
    for it in re.findall(r"<item(?:\s[^>]*)?>(.*?)</item>", raw, re.S | re.I):
        title = strip_html(html.unescape(_tag(it, "title")))
        link = html.unescape(_tag(it, "link")) or (re.search(r"<link[^>]*href=\"([^\"]+)\"", it) or [None, ""])[1]
        pub = parse_date(html.unescape(_tag(it, "pubDate") or _tag(it, "date")))
        desc = strip_html(html.unescape(_tag(it, "description") or _tag(it, "encoded")))
        if title and link:
            out.append(dict(title=title, url=link.strip(), published=pub, summary=desc[:800], source=label, lang=lang, origin="rss"))
    if not out:
        for it in re.findall(r"<entry(?:\s[^>]*)?>(.*?)</entry>", raw, re.S | re.I):
            title = strip_html(html.unescape(_tag(it, "title")))
            link = ""
            for m in re.finditer(r"<link\b([^>]*)/?>", it):
                attrs = m.group(1)
                if re.search(r"rel=\"(?!alternate)", attrs):
                    continue
                h = re.search(r"href=\"([^\"]+)\"", attrs)
                if h:
                    link = html.unescape(h.group(1)); break
            pub = parse_date(_tag(it, "published") or _tag(it, "updated"))
            desc = strip_html(html.unescape(_tag(it, "summary") or _tag(it, "content")))
            if title and link:
                out.append(dict(title=title, url=link.strip(), published=pub, summary=desc[:800], source=label, lang=lang, origin="rss"))
    log(f"feed {label}: {len(out)} items")
    return out


def fetch_hn(start, end, min_points=15, max_pages=6):
    out = []
    for page in range(max_pages):
        q = urllib.parse.urlencode({
            "tags": "story",
            "numericFilters": f"created_at_i>={int(start.timestamp())},created_at_i<{int(end.timestamp())},points>={min_points}",
            "hitsPerPage": 100, "page": page})
        try:
            j = json.loads(http_get("https://hn.algolia.com/api/v1/search_by_date?" + q, timeout=40))
        except Exception as e:
            log(f"hn FAIL page {page}: {e}")
            break
        for h in j.get("hits", []):
            t = h.get("title") or ""
            u = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            if not AI_KW.search(t):
                continue
            out.append(dict(title=t, url=u, published=parse_date(h.get("created_at")), summary="", source=hn_source(u), lang="en",
                            origin="hn", score=h.get("points", 0), hn=f"https://news.ycombinator.com/item?id={h.get('objectID')}"))
        if page >= j.get("nbPages", 1) - 1:
            break
        time.sleep(0.3)
    log(f"hn: {len(out)} AI stories")
    return out


def hn_source(url):
    host = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    return host or "Hacker News"


def load_websearch(dirpath):
    """websearch.json + feeds.json (클라우드 루틴이 WebFetch 로 읽은 피드 항목) 을 같은 형식으로 읽는다."""
    out = []
    for name, origin in (("websearch.json", "websearch"), ("feeds.json", "feedfetch")):
        out += _load_extra(os.path.join(dirpath, name), origin)
    return out


def _load_extra(p, origin):
    if not os.path.exists(p):
        return []
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        log(f"websearch.json 읽기 실패: {e}")
        return []
    out = []
    for it in j.get("items", []):
        raw = (it.get("published") or "").strip()
        date_only = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw))
        pub = dt.datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=KST) if date_only else parse_date(raw)
        if it.get("url") and it.get("title"):
            role = it.get("role") or None
            out.append(dict(title=it["title"], url=it["url"], published=pub, date_only=date_only, summary=(it.get("summary") or "")[:800],
                            source=it.get("source") or hn_source(it["url"]), lang=it.get("lang", "en"), origin=origin,
                            role_hint=(role if role != "dev_edu" else None), dev_edu_hint=(role == "dev_edu")))
    log(f"{os.path.basename(p)}: {len(out)} items")
    return out


def norm_url(u):
    u = re.sub(r"[?#].*$", "", u.strip())
    return u.rstrip("/").lower().replace("http://", "https://").replace("://www.", "://")


def dedupe(items):
    seen, out = set(), []
    for it in items:
        k = norm_url(it["url"])
        tk = re.sub(r"\W+", "", it["title"].lower())[:60]
        if k in seen or tk in seen:
            continue
        seen.add(k); seen.add(tk)
        out.append(it)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    date = sys.argv[1]
    no_fetch = "--no-fetch" in sys.argv
    D = dt.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=KST, hour=PUBLISH_HOUR_KST)
    publish_at = D
    outdir = os.path.join(WORK, date)
    os.makedirs(outdir, exist_ok=True)

    # 1) 소스 수집 (피드는 한 번만 받고 윈도우별로 필터)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_feed, *f) for f in FEEDS]
        feed_items = [it for f in as_completed(futs) for it in f.result()]
    hn_items = fetch_hn(publish_at - dt.timedelta(hours=72), publish_at)
    ws_items = load_websearch(outdir)

    def in_window(it, hours):
        p = it.get("published")
        if p is None:
            return False
        if it.get("date_only"):  # 날짜만 아는 항목(WebSearch·WebFetch): 날짜 단위로 판정
            return (publish_at - dt.timedelta(hours=hours)).date() <= p.date() <= publish_at.date()
        return (publish_at - dt.timedelta(hours=hours)) <= p < publish_at

    def ai_filter(it):
        if it["origin"] != "rss":
            return True
        if it["lang"] == "ko" and it["source"] == "AI타임스":
            return True
        return bool(AI_KW.search(it["title"] + " " + it.get("summary", "")))

    widened = 24
    for hours in (24, 48, 72):
        cands = [it for it in feed_items + hn_items if in_window(it, hours) and ai_filter(it)]
        cands += [it for it in ws_items if it.get("published") is None or in_window(it, hours) or it.get("role_hint")]
        cands = dedupe(cands)
        widened = hours
        if len(cands) >= MIN_CANDIDATES:
            break
    log(f"window={widened}h candidates={len(cands)}")

    # 2) 직무 탭 풀: 최근 14일 중 역할 키워드 매칭
    role_pool = [it for it in dedupe(feed_items + hn_items + ws_items)
                 if (it.get("role_hint") or (in_window(it, 24 * ROLE_DAYS) and ROLE_ANY.search(it["title"] + " " + it.get("summary", ""))))]
    for it in role_pool:
        it["roles"] = [r for r, p in ROLE_KW.items() if p.search(it["title"] + " " + it.get("summary", ""))] or ([it["role_hint"]] if it.get("role_hint") else [])
    role_pool = [it for it in role_pool if it["roles"]]
    log(f"role_pool={len(role_pool)}")

    # 3) 원문 본문 앞부분 가져오기(요약 근거). 순위: HN 은 점수, 공식 블로그·매체 RSS·WebSearch·WebFetch 는 기본 점수(잘리지 않게).
    DEFAULT_SCORE = {"websearch": 80, "feedfetch": 70, "rss": 60}
    def rank(it):
        return it.get("score") if it.get("origin") == "hn" and it.get("score") is not None else DEFAULT_SCORE.get(it.get("origin"), 0)
    cands.sort(key=lambda it: -rank(it))
    MAX_CANDS = 50
    targets = cands[:MAX_CANDS] + [it for it in role_pool if it not in cands][:30]
    if not no_fetch:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(page_text, it["url"]): it for it in targets if "openai.com" not in it["url"]}
            for f in as_completed(futs):
                it = futs[f]
                txt, err = f.result()
                it["text"] = txt
                if err:
                    it["fetch_error"] = err
    fetched = sum(1 for it in targets if it.get("text"))
    log(f"page text fetched: {fetched}/{len(targets)}")

    def ser(it):
        p = it.get("published")
        hrs = round((publish_at - p).total_seconds() / 3600, 1) if p else None
        blob = it["title"] + " " + it.get("summary", "") + " " + it.get("text", "")
        return {
            "title": it["title"], "url": it["url"], "source": it["source"], "lang": it["lang"], "origin": it["origin"],
            "published": p.astimezone(KST).isoformat() if p else None,
            "published_date": p.astimezone(KST).strftime("%Y-%m-%d") if p else None,
            "hours_before_publish": hrs,
            "score": it.get("score"), "hn": it.get("hn"),
            "summary": it.get("summary", ""), "text": it.get("text", ""),
            "roles": it.get("roles", []),
            "dev_edu": bool(it.get("dev_edu_hint")) or bool(DEV_EDU_KW.search(blob)),
        }

    out = {
        "date": date, "publish_at": publish_at.isoformat(), "window_hours": widened,
        "window_start": (publish_at - dt.timedelta(hours=widened)).isoformat(),
        "counts": {"candidates": len(cands), "role_pool": len(role_pool), "feeds": len(feed_items), "hn": len(hn_items), "websearch": len(ws_items)},
        "candidates": [ser(it) for it in cands[:MAX_CANDS]],
        "role_pool": [ser(it) for it in role_pool[:30]],
    }
    path = os.path.join(outdir, "candidates.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"→ {path}")
    print(json.dumps(out["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
