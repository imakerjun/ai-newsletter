# AGENT.md — 러닝 에이전트 발행 지시서

이 문서는 **Claude Cowork(또는 Claude Code) 스케줄 에이전트**가 매번 실행할 때 읽는 사양이다.
목표: 내 관심사에 맞춘 AI 뉴스레터 한 호를 생성하고, 아카이브에 추가하고, 배포하고, 슬랙으로 알린다.

---

## 0. 내 설정 (이 부분만 사람이 편집)

```yaml
owner: 메이커준
cadence: 매일 아침 08:00 (Asia/Seoul)
interests:                      # 관심사 = 탭. 추가/삭제 자유. 2~5개 권장.
  - id: news
    label: AI 최신 소식
    icon: 📰
    tint: blue
    window_hours: 24            # 발행 시각 기준 직전 24시간 내 소식 우선
    focus: 직전 24시간의 업계 전반 주요 AI 뉴스(새 모델·기능·정책·발표). 영향 범위와 중요도 우선.
  - id: everyone
    label: 비개발자를 위한 AI 소식
    icon: 🧭
    tint: green
    window_hours: 24
    focus: 직전 24시간 소식 중 비개발자가 ‘먼저 적용·시도해볼 만한 것’ — 주요 기능 업데이트, 바로 쓰는 활용법, 새 도구. 기술 깊이보다 ‘오늘 해볼 수 있는가’.
  # ↓ 직무별 탭: 속보가 아니라 '현업 활용 사례'를 큐레이션(상시 유효). window_hours 없음.
  - id: planner
    label: 기획자를 위한 AI 소식
    icon: 💡
    tint: purple
    kind: role            # 역할 활용 사례 — 날짜 필터 대신 큐레이션
    focus: 시장·사용자 조사, 기획서 초안, 아이디어 구체화 등 기획자가 오늘 업무에 바로 쓰는 AI 활용
  - id: data
    label: 데이터 분석을 위한 AI 소식
    icon: 📊
    tint: orange
    kind: role
    focus: 자연어로 표에 묻기·수식/SQL 초안·데이터 정리·결과를 쉬운 말로 설명. 'AI 결과는 사람이 검증' 원칙 강조
  - id: pm
    label: PM을 위한 AI 소식
    icon: 📋
    tint: pink
    kind: role
    focus: PRD 초안·회의록 정리·피드백 분류·릴리스 노트 등 PM 업무 활용. '판단은 사람이, 정리는 AI가'
persona_context: |             # '나를 위한 한 줄'을 쓸 때 참고할 독자 맥락
  회사의 비개발 직군을 포함한 전사 임직원 누구나. 전문 용어는 풀어 쓰고,
  "이게 내 업무에 어떻게 쓰이는가"를 한 문장으로 연결할 것. 과장·홍보톤 금지.
slack_webhook_env: SLACK_WEBHOOK_URL   # 발송용 Incoming Webhook (환경변수)
tint_options: [blue, purple, green, orange, pink]
```

---

## 1. 실행 순서

1. **오늘 날짜**를 `YYYY-MM-DD`(Asia/Seoul)로 구한다. → `{DATE}`
2. `interests`의 각 관심사마다 **직전 24시간(`window_hours`)의 소식을 웹 검색**한다(아래 ‘뉴스 선정 기준’ 적용).
   - 검색은 발행 시각 기준 직전 24시간을 우선한다(예: `past 24 hours`, `오늘`, 날짜 한정 쿼리).
   - 신뢰 가능한 1차 출처(공식 블로그·릴리스 노트·주요 매체 1차 보도)를 우선하고, **원문 URL과 매체명**을 반드시 기록한다.
   - 관심사별로 **핵심 1건(highlight) + 더 읽을거리 2건(articles)** 을 선정 기준 점수가 높은 순으로 고른다.
   - 각 항목의 `time`에는 상대 시각을 적는다(예: `오늘`, `어제`, `3시간 전`).
3. 각 항목에 **`나를 위한 한 줄`(foryou)** 을 쓴다 — `persona_context`에 맞춰
   "이 소식이 내 교육/코칭/업무에 왜 중요한지"를 한 문장으로.
4. **에디션 파일 생성**: `_TEMPLATE_edition.html`을 복제해 `editions/{DATE}.html`로 저장하고,
   안의 `NEWSLETTER` 데이터 객체를 오늘 내용으로 교체한다. (구조·CSS·스크립트는 그대로 둔다)
   - `meta.date`는 `YYYY년 M월 D일 (요일)`, `meta.edition`은 직전 호 +1 (예: Vol.08).
5. **아카이브 갱신**: 루트 `index.html`의 `ARCHIVE.editions` 배열 **맨 앞**에 새 항목을 추가한다.
   ```js
   { date: "{DATE}", weekday: "{요일}", label: "{Vol.NN}",
     title: "{한 줄 요약}", topics: [관심사 label들], href: "editions/{DATE}.html" }
   ```
   - 기존 항목은 절대 삭제·수정하지 않는다(아카이브 보존).
   - 단, **최초 발행 시**에는 템플릿에 들어 있던 **예시 항목(`demo: true`)을 모두 제거**한다(이후 실제 호만 쌓는다).
6. **커밋 & 푸시**:
   ```bash
   git add -A
   git commit -m "publish \"{DATE} {Vol.NN} 뉴스레터 발행\"" --no-verify
   git push
   ```
   → GitHub Pages가 push를 감지해 **자동 재배포**한다(별도 배포 단계 없음).
7. **슬랙 발송**: 배포 URL을 Incoming Webhook으로 보낸다.
   ```bash
   curl -s -X POST "$SLACK_WEBHOOK_URL" \
     -H 'Content-Type: application/json' \
     -d '{"text":"🗞️ 오늘의 데일리 AI 뉴스레터 {Vol.NN} 발행 → https://imakerjun.github.io/ai-newsletter/editions/{DATE}.html\n아카이브: https://imakerjun.github.io/ai-newsletter/"}'
   ```

---

## 뉴스 선정 기준 (24시간 윈도우)

매 발행은 **발행 시각 기준 직전 24시간**에 나온 소식을 다룬다. 24시간 내 충분한 소식이 없으면
최대 48~72시간까지 넓히되, 오래된 항목은 `time`에 사실대로 표기한다(예: `2일 전`). 루머는 다루지 않는다.

**선정 점수(높은 순으로 highlight→articles 배치):**
1. **영향 범위** — 많은 사람·업무에 영향을 주는가.
2. **새로움·중요도** — 새 모델/기능/정책의 1차 발표인가(재탕·반복 보도 아님).
3. **출처 신뢰도** — 공식 블로그·릴리스 노트·주요 매체의 1차 보도인가.
4. **실용성** — 독자가 바로 보거나 써볼 수 있는가.
5. **관심사 적합도** — 해당 탭의 `focus`에 맞는가.

**탭별 관점**
- **AI 최신 소식**: 업계 전반에서 24시간 내 가장 중요한 소식. 영향·중요도 우선, 한 탭이 한 주제로 쏠리지 않게 다양화.
- **비개발자를 위한 AI 소식**: 같은 24시간 소식 중 **비개발자가 먼저 적용·시도해볼 만한 것**을 고른다 —
  주요 기능 업데이트, 코드 없이 쓰는 활용법, 새로 나온 도구. `foryou`는 “오늘 당장 해볼 수 있는 한 가지”로 쓴다.

**제외:** 미확인 루머, 광고·홍보성 글, 출처 불명, 동일 사안 중복, 24h 윈도우 밖의 옛 소식(불가피할 때만 시각 표기 후 포함).

---

## 2. 콘텐츠 규칙

- 사실 검증: 출처가 모호하면 단정하지 말고 "~로 보인다/논의되는 중" 톤으로.
- **출처 링크 + 발행일 필수**: highlight와 각 article 모두 `source`(매체명) + `url`(원문 링크) + `published`(출처 발행일)을 채운다.
  - 데이터 형태: `highlight: { kicker, title, summary, detail?, source, url, published, foryou }`,
    `articles: [{ tag, source, url, time, published, title, summary, detail?, foryou }]`
  - `published`는 **원문이 실제로 발행된 날짜**(`YYYY-MM-DD`). 카드에 ‘🗓 발행 …’으로 표기되어 신선도를 보여준다.
    `time`(오늘/어제/N시간 전)은 발행 시점 기준 상대 시각, `published`는 절대 날짜 — 둘 다 채운다.
  - `url`·`published`는 **실제 값**이어야 한다. 확인하지 못하면 지어내지 말고 그 항목을 빼라(허위 링크·허위 날짜 금지).
- **선정 기준 노출**: 각 탭(topic)에 `criteria` 한 단락을 넣어 ‘무슨 기준으로 골랐는지’를 독자에게 보여준다
  (페이지에 ‘ⓘ 이 소식들은 이렇게 골랐어요’ 토글로 표시됨). 위 ‘뉴스 선정 기준’을 탭 관점에 맞게 한 단락으로 요약한다.
  데이터 형태: `topic: { id, label, icon, tint, desc, criteria, highlight, articles }`.
- **한국어로 정리**: 영어 출처라도 `title`·`summary`·`detail`·`foryou`는 한국어로 번역·요약한다.
  원제가 중요하면 제목 끝에 괄호로 병기한다(예: "… (원제: …)"). 핵심 용어는 풀어 쓰되 필요 시 영어 병기.
- **요약은 ‘무슨 소식인지’ 파악되게**: 한 줄 요약 금지. 출처 페이지의 내용을 적절한 분량으로 요약한다 —
  `summary`는 highlight 3~5문장 / article 2~3문장으로, ‘무엇이 일어났는지 + 핵심 + 왜 중요한지’가 카드만 봐도
  전달되게 쓴다. 더 깊은 맥락(배경·주의점·예시)은 `detail`(접히는 ‘자세히 보기’, 2~3문장)에 담는다.
  단, 기사 전문을 그대로 복사하지는 말고, 전체 내용은 `url` 원문으로 연결한다.
- **‘자세히 보기’(detail)는 충분히 길게 + 예시로**: `detail`은 한 줄로 끝내지 않는다.
  - **AI 최신 소식(news)**: 2단락 이상 — `<p>무슨 일/배경</p><p>그래서 무슨 의미인지·주의점</p>`.
  - **직무별·비개발자 탭(everyone/planner/data/pm)**: 3단락으로 충분히 길게 —
    `<p>① 왜 유용한지 쉬운 설명</p><p><b>예를 들어</b> 구체 시나리오 + 따라 칠 샘플 한마디 ‘…’</p><p>② 한 걸음 더: 응용·주의·검증</p>`.
  - 전문 용어는 풀어 쓰고, 코드 없이 바로 해볼 수 있는 행동/샘플로 끝맺는다. HTML 태그는 `<p>`, `<b>`만 쓴다.
- **직무별 탭(kind: role)**: 24시간 속보가 아니라 **현업 활용 사례**를 큐레이션하되, **반드시 실제 리서치 기반**으로 쓴다.
  - 각 항목은 WebSearch로 찾은 **실제 기사/공식 발표 URL**과 **그 기사의 발행일(`published`)**을 출처로 단다.
    **제품 홈페이지(예: chatgpt.com, openai.com 메인)를 출처로 쓰지 말 것** — 구체적 기사/블로그/뉴스 URL만. 못 찾으면 그 항목을 뺀다.
  - `time`은 비우고(상시 활용), `published`에 출처 기사 발행일을 넣는다. `criteria`는 ‘OO 업무에 바로 쓰는 활용을 정리했다’는 취지로.
- `tint`는 `tint_options` 중에서만 쓴다(디자인 일관성).
- 문체: 정중한 평서체("~합니다"), 과장·홍보톤 금지.

## 3. 하면 안 되는 것

- 과거 `editions/*.html` 파일을 덮어쓰거나 삭제하지 않는다.
- 개인정보(실명·이메일·연락처·키/토큰)를 본문에 넣지 않는다.
- `_TEMPLATE_edition.html`의 구조·CSS·스크립트를 바꾸지 않는다(데이터만 교체).

## 4. 한 줄 요약 (에이전트용 프롬프트)

> "AGENT.md의 설정대로 오늘({DATE}) 관심사별 최신 AI 소식을 검색해 `editions/{DATE}.html`을
> 생성하고, 루트 `index.html`의 아카이브 목록 맨 앞에 추가한 뒤, 커밋·푸시하고 슬랙 웹훅으로
> 배포 링크를 보내줘. 과거 호는 건드리지 마."

---

## 5. 수동 트랙 — 깊이 읽기(렌즈) 문서 만들기

자동 뉴스레터(받아보기)와 별개로, **공부하고 싶은 어려운 문서/공식문서를 5가지 렌즈로 재구성**하는
사용자 요청형 작업이다. 트리거 예: "이 링크를 깊이 읽기 렌즈 문서로 만들어줘 — {URL}".

**렌즈 5종(순서 고정):** 🔤 어원 → ⚡ 한입요약 → 🧒 비유로 쉽게 → 🧪 퀴즈 → 📄 전문(번역)

**순서:**
1. 원문 URL의 내용을 읽는다(영어면 한국어로 정리). 슬러그 `{slug}`를 정한다(예: `prompting-fable-5`).
2. `learn/_TEMPLATE_lens.html`을 복제해 `learn/{slug}.html`로 저장하고, `LENS_DOC` 데이터만 교체한다.
   - prose 렌즈는 `body`(HTML 문자열), 퀴즈는 `quiz: [{ q, options, answer(인덱스), explain }]`.
   - 🔤 어원: 핵심 용어/이름의 유래(학습용 가설임을 명시). ⚡ 한입요약: 핵심 5~7줄.
     🧒 비유: 일상 비유로 감 잡기. 🧪 퀴즈: 4~5문항 자가점검.
     📄 전문(번역): 원문 **전체를 한국어로** 옮긴다. 영어 프롬프트·예시는 한국어 번역을 본문으로,
     복사용 영어 원문은 `<details>` 접이식 `<pre>`로 병기한다(맨 위에 출처 링크).
3. `learn/index.html`의 `LIBRARY.docs` 배열 **맨 앞**에 항목을 추가한다(icon, title, desc, lenses, source, sourceUrl, date, href).
   - 초기 `demo: true` 예시 항목은 첫 실제 문서 추가 시 제거한다.
4. 커밋·푸시 → GitHub Pages 자동 배포. (원하면 슬랙으로 새 학습 문서 링크 발송)

**규칙:** 원문을 그대로 복제하지 말 것(요약·각색 + 원문 링크). 사실은 출처에 근거하고, 어원·비유는
이해를 돕는 학습용 해석임을 밝힌다. `_TEMPLATE_lens.html`의 구조·CSS·스크립트는 바꾸지 않는다(데이터만).
