#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
샘플 저장소용 — 한 달치 일일 뉴스레터(영업일)를 생성한다.
템플릿 셸(_TEMPLATE_edition.html)은 그대로 두고 NEWSLETTER 데이터 객체만 주입한다.
또한 index.html의 ARCHIVE.editions 목록을 갱신한다.
※ 데모/쇼케이스용 샘플 콘텐츠. 실제 발행 시 AGENT.md 사양대로 교체된다.
"""
import json, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = (ROOT / "_TEMPLATE_edition.html").read_text(encoding="utf-8")

# 출처 풀(실제 신뢰 매체의 대표 페이지 — 데모용)
SRC = {
    "anthropic": ("Anthropic 뉴스", "https://www.anthropic.com/news"),
    "google": ("Google AI 블로그", "https://blog.google/technology/ai/"),
    "openai": ("OpenAI 블로그", "https://openai.com/news/"),
    "mit": ("MIT Technology Review", "https://www.technologyreview.com/topic/artificial-intelligence/"),
    "verge": ("The Verge — AI", "https://www.theverge.com/ai-artificial-intelligence"),
    "repo": ("이 템플릿 저장소 (GitHub)", "https://github.com/imakerjun/ai-newsletter"),
    "docs": ("Claude 활용 가이드", "https://platform.claude.com/docs/ko/"),
}

# --- 콘텐츠 풀 (회전) -------------------------------------------------------
NEWS_HL = [
    ("AI가 ‘답해주는 도구’에서 ‘대신 일해주는 동료’로", "한 번의 질문에 답하던 AI가 이제 여러 단계를 스스로 밟아 결과물까지 만들어 옵니다. 자료를 찾고, 문서를 만들고, 정해진 시간에 알아서 보내주는 ‘에이전트’가 일상 도구로 들어오고 있어요.", "mit", "반복되는 내 업무 한 가지를 떠올려 보세요. 그게 가장 먼저 맡겨볼 수 있는 일입니다."),
    ("‘에이전트’가 올해 AI의 키워드가 된 이유", "단순 챗봇을 넘어, 목표를 주면 스스로 계획하고 도구를 써서 끝까지 수행하는 흐름이 주류가 됐습니다. ‘무엇을 시킬까’가 새로운 능력이 되는 중입니다.", "verge", "거창하게 보지 마세요 — ‘대신 해줬으면 하는 일’의 목록이 곧 활용 아이디어입니다."),
    ("멀티모달이 ‘기본’이 되다 — 글·이미지·음성 한 번에", "이제 캡처 이미지를 보여주며 말로 묻고 표로 답을 받는 사용이 자연스러워졌습니다. 입력 방식의 벽이 빠르게 사라지는 중이에요.", "anthropic", "스크린샷 한 장 붙여넣고 ‘이거 표로 정리해줘’ 한마디면 됩니다."),
    ("더 긴 작업을 한 번에 — 장기 실행 모델의 부상", "몇 분, 때로 몇 시간이 걸리는 복잡한 작업을 끊김 없이 수행하는 모델이 나오면서, ‘맡기고 기다리는’ 업무 방식이 현실이 됐습니다.", "anthropic", "급한 일 말고 ‘오래 걸려도 되는 정리·조사’부터 맡겨보세요."),
    ("AI 비용은 내려가고, 성능은 올라간다", "같은 작업을 더 싸고 빠르게 처리하는 효율 개선이 이어지면서, 개인·팀이 부담 없이 일상에 쓰기 좋아지고 있습니다.", "openai", "‘비싸서 못 쓴다’는 옛말 — 가벼운 일부터 매일 써보는 게 학습의 지름길."),
    ("검색·메신저·문서, 매일 쓰는 도구 속으로 들어온 AI", "따로 AI 사이트를 찾지 않아도 늘 쓰던 업무 도구 안에서 요약·초안·번역이 붙는 방향으로 제품들이 움직이고 있습니다.", "google", "새 도구를 배우는 부담 없이, 쓰던 자리에서 한 단계씩 익히면 충분합니다."),
    ("AI 에이전트끼리 협업하는 시대", "하나의 큰 AI 대신, 역할을 나눈 여러 에이전트가 협업해 더 정확한 결과를 내는 구조가 표준이 되어갑니다.", "mit", "팀으로 일하듯, AI도 ‘분업’이 핵심이라는 점이 흥미롭죠."),
    ("‘평가(eval)’가 AI 활용의 필수 인프라로", "결과물 품질을 숫자로 점검하고 반복 개선하는 평가 루프가 자리잡으며, ‘좋아 보인다’에서 ‘측정한다’로 옮겨가고 있습니다.", "anthropic", "AI 결과를 그냥 믿지 말고 ‘무엇이 좋은 답인가’ 기준을 먼저 세우는 습관."),
]
NEWS_ART = [
    ("새 기능", "google", "음성으로 묻고 화면으로 답받기 — 대화형 UI의 진화", "말로 묻고 표·차트로 답을 받는 사용이 자연스러워졌습니다."),
    ("흐름", "mit", "‘프롬프트’보다 ‘맥락 제공’이 결과를 가른다", "무엇을 원하는지뿐 아니라 왜 필요한지를 주면 품질이 오릅니다."),
    ("제품", "verge", "노트·메신저에 붙는 AI 요약 기능 확산", "긴 스레드를 한 줄로 요약해주는 기능이 기본 탑재되는 추세."),
    ("연구", "anthropic", "긴 컨텍스트, ‘넣을 수 있다’와 ‘써야 한다’는 다르다", "무작정 다 넣기보다 핵심만 추리는 게 더 좋은 결과로 이어집니다."),
    ("동향", "openai", "이미지 생성·편집 품질의 빠른 향상", "간단한 설명만으로 발표 자료용 이미지를 만드는 사례가 늘었습니다."),
    ("보안", "mit", "AI 시대의 정보보안 — 무엇을 입력하면 안 되나", "민감정보·기밀은 입력 금지. 사내 정책 확인이 첫걸음입니다."),
    ("생산성", "google", "회의록 자동 정리, 어디까지 왔나", "녹취에서 결정·액션아이템만 뽑아주는 기능이 실용 단계."),
    ("리서치", "anthropic", "AI의 ‘환각’을 줄이는 법 — 출처 대조", "답에 근거 링크를 함께 요구하면 신뢰도가 크게 오릅니다."),
]
EVERY_HL = [
    ("바로 ‘이 뉴스레터’처럼 — 비개발자도 AI에게 일을 맡길 수 있다", "지금 보는 이 페이지도 사람이 일일이 코딩한 게 아니라 ‘이런 뉴스레터를 만들어줘’라는 말 한마디에서 시작됐어요. 자료 조사부터 디자인, 매일 발행까지 맡기는 시대입니다.", "repo", "오늘 30분이면 나만의 버전을 따라 만들 수 있어요."),
    ("빈 문서가 무섭다면 — 초안은 AI에게, 판단은 나에게", "보고서·이메일의 첫 줄을 띄우는 시간을 AI가 줄여줍니다. 사람은 검토와 결정에 집중하는 분업이 가장 현실적인 활용법이에요.", "docs", "‘완성’ 말고 ‘초안’을 시키세요. 훨씬 빠르고 결과도 좋습니다."),
    ("AI를 믿되 확인하기 — 환각과 정보보안 기본기", "AI는 그럴듯하게 틀릴 수 있고, 회사 자료·개인정보를 함부로 넣어서도 안 됩니다. ‘출처 확인’과 ‘민감정보 입력 금지’ 두 가지만 지켜도 안전합니다.", "docs", "이름·연락처·계정 정보 같은 민감정보는 넣지 않기 — 가장 먼저 익힐 한 가지."),
    ("‘질문 잘하는 법’이 곧 AI 활용 실력", "좋은 답은 좋은 질문에서 나옵니다. 원하는 형식·분량·예시를 함께 주면 결과가 확 달라져요.", "docs", "‘표로’, ‘3줄로’, ‘초등학생도 알게’ 같은 한마디를 붙이는 연습부터."),
    ("매일 5분, AI로 업무 한 조각 자동화하기", "거창한 도입이 아니라 반복 업무 하나를 AI에 맡기는 작은 습관이 가장 큰 변화를 만듭니다.", "verge", "‘매주 똑같이 하는 일’을 적어보세요. 거기에 답이 있습니다."),
    ("회의·자료조사·번역 — 비개발 직군의 AI 활용 3대장", "코드를 몰라도 바로 효과를 보는 영역입니다. 작게 시작해 점점 넓혀가세요.", "google", "가장 자신 없는 업무 한 가지를 AI와 함께 해보는 것부터."),
]
EVERY_ART = [
    ("업무 활용", "docs", "회의록·보고서·이메일 — 초안 맡기기 실전", "거친 초안을 받고 사람이 다듬는 분업이 가장 빠릅니다."),
    ("꼭 알아두기", "docs", "AI를 믿되 확인하기 — 출처와 민감정보", "출처 확인 + 민감정보 입력 금지, 이 둘만 지켜도 안전."),
    ("입문", "verge", "처음 쓰는 사람을 위한 AI 사용 5단계", "작게 시작해 매일 한 가지씩 맡겨보는 게 핵심입니다."),
    ("팁", "google", "원하는 형식을 말하면 결과가 달라진다", "‘표로/3줄로/예시 포함’ 한마디가 품질을 바꿉니다."),
    ("사례", "mit", "비개발 직군의 AI 활용 사례 모음", "기획·마케팅·CS에서 바로 쓰는 패턴을 소개합니다."),
    ("리터러시", "anthropic", "AI가 만든 결과, 어디까지 믿을까", "중요한 숫자·사실은 반드시 원문으로 교차 확인하세요."),
]

DETAIL = [
    "핵심은 한 번의 똑똑한 답이 아니라, 여러 단계를 끝까지 마무리하는 ‘지속성’입니다. 거창한 도입보다 작은 업무 하나를 맡겨보는 데서 시작하세요. 잘 되면 범위를 넓히면 됩니다.",
    "처음엔 결과를 100% 신뢰하기보다 ‘초안’으로 받아 사람이 검토하는 흐름이 안전합니다. 익숙해질수록 맡기는 범위를 늘려가며 나만의 사용법을 만들어 보세요.",
    "중요한 건 도구가 아니라 ‘무엇을 어떻게 시킬지’예요. 원하는 형식·분량·예시를 함께 주면 같은 AI라도 결과가 확연히 달라집니다.",
    "한 번 써보고 판단하지 말고, 며칠 반복하며 감을 잡는 게 좋습니다. 매일 5분, 반복 업무 한 조각을 맡기는 습관이 가장 큰 변화를 만듭니다.",
]

def mk_topic(tid, label, icon, tint, desc, hl_pool, art_pool, i):
    hl = hl_pool[i % len(hl_pool)]
    a1 = art_pool[i % len(art_pool)]
    a2 = art_pool[(i + 3) % len(art_pool)]
    def art(a, t):
        return {"tag": a[0], "source": SRC[a[1]][0], "url": SRC[a[1]][1], "time": t,
                "title": a[2], "summary": a[3], "foryou": "내 업무 맥락에 대입해 한 가지만 적용해 보세요."}
    return {"id": tid, "label": label, "icon": icon, "tint": tint, "desc": desc,
            "highlight": {"kicker": "이 주제의 핵심", "title": hl[0], "summary": hl[1],
                          "detail": DETAIL[i % len(DETAIL)],
                          "source": SRC[hl[2]][0], "url": SRC[hl[2]][1], "foryou": hl[3]},
            "articles": [art(a1, "이번 주"), art(a2, "최근")]}

WD = ["월", "화", "수", "목", "금", "토", "일"]

# 영업일(월~금) 한 달치: 2026-05-19 ~ 2026-06-18
start = datetime.date(2026, 5, 19)
end = datetime.date(2026, 6, 18)
dates = []
d = start
while d <= end:
    if d.weekday() < 5:
        dates.append(d)
    d += datetime.timedelta(days=1)

total = len(dates)
editions_dir = ROOT / "editions"
archive = []

for idx, dt in enumerate(dates):
    vol = idx + 1  # 오래된 것이 Vol.01
    iso = dt.isoformat()
    wd = WD[dt.weekday()]
    date_ko = f"{dt.year}년 {dt.month}월 {dt.day}일 ({wd})"
    label = f"Vol.{vol:02d}"
    news = mk_topic("news", "AI 최신 소식", "📰", "blue",
                    "이번 주, 알아두면 대화에 끼는 AI 흐름.", NEWS_HL, NEWS_ART, idx)
    every = mk_topic("everyone", "비개발자가 꼭 아는 AI", "🧭", "green",
                     "코드를 몰라도, 업무에 바로 쓰는 AI.", EVERY_HL, EVERY_ART, idx)
    nl = {
        "meta": {
            "icon": "🗞️", "edition": label, "cadence": "일간",
            "date": date_ko, "curator": "러닝 에이전트 (Claude Cowork)", "reader": "메이커준",
            "title": ["메이커준의 ", "AI 위클리"],
            "lead": "관심사를 탭으로 나눠 읽는 개인화 뉴스레터. 주제마다 이번 호 ‘딱 하나의 핵심’만 크게, 나머지는 가볍게.",
            "greeting": "안녕하세요! 오늘 호는 누구나 알아두면 좋은 AI 흐름과, 코드를 몰라도 업무에 바로 쓰는 활용법 두 가지로 골랐어요. 각 탭 맨 위의 큰 카드가 <b>그 주제의 핵심 한 건</b>입니다.",
        },
        "topics": [news, every],
    }
    obj = "const NEWSLETTER = " + json.dumps(nl, ensure_ascii=False, indent=2) + ";"
    html = re.sub(r"const NEWSLETTER = \{.*?\n\};", lambda m: obj, TPL, count=1, flags=re.DOTALL)
    (editions_dir / f"{iso}.html").write_text(html, encoding="utf-8")
    archive.append({"date": iso, "weekday": wd, "label": label,
                    "title": f"{news['highlight']['title']} · {every['highlight']['title']}"[:60],
                    "topics": ["AI 최신 소식", "비개발자가 꼭 아는 AI"], "href": f"editions/{iso}.html"})

# 최신순으로 아카이브 정렬
archive.reverse()

ARCHIVE = {
    "meta": {
        "icon": "🗞️", "title": ["메이커준의 ", "AI 위클리"],
        "lead": "러닝 에이전트가 내 관심사에 맞춰 매일 발행하는 개인화 AI 뉴스레터. 지난 호를 여기에 모아둡니다.",
        "owner": "메이커준", "cadence": "매일(영업일)",
    },
    "editions": archive,
}
index_path = ROOT / "index.html"
idx_html = index_path.read_text(encoding="utf-8")
arch_obj = "const ARCHIVE = " + json.dumps(ARCHIVE, ensure_ascii=False, indent=2) + ";"
idx_html = re.sub(r"const ARCHIVE = \{.*?\n\};", lambda m: arch_obj, idx_html, count=1, flags=re.DOTALL)
index_path.write_text(idx_html, encoding="utf-8")

print(f"generated {total} editions: {dates[0].isoformat()} ~ {dates[-1].isoformat()}")
print(f"archive entries: {len(archive)} (latest first)")
