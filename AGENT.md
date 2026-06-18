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
    focus: 새 모델·기능, AI 제품 동향, 일상·업무에 들어온 AI (전문 용어는 풀어서)
  - id: everyone
    label: 비개발자가 꼭 아는 AI
    icon: 🧭
    tint: green
    focus: 코드 없이 쓰는 업무 활용(문서·요약·번역), AI 리터러시, 환각·정보보안 주의점
persona_context: |             # '나를 위한 한 줄'을 쓸 때 참고할 독자 맥락
  회사의 비개발 직군을 포함한 전사 임직원 누구나. 전문 용어는 풀어 쓰고,
  "이게 내 업무에 어떻게 쓰이는가"를 한 문장으로 연결할 것. 과장·홍보톤 금지.
slack_webhook_env: SLACK_WEBHOOK_URL   # 발송용 Incoming Webhook (환경변수)
tint_options: [blue, purple, green, orange, pink]
```

---

## 1. 실행 순서

1. **오늘 날짜**를 `YYYY-MM-DD`(Asia/Seoul)로 구한다. → `{DATE}`
2. `interests`의 각 관심사마다 **최신 소식을 웹 검색**한다(최근 7일 우선).
   - 신뢰 가능한 출처(공식 블로그, 릴리스 노트, 1차 자료)를 우선한다.
   - 각 항목의 **원문 URL과 매체명**을 반드시 함께 기록한다(데이터의 `source`·`url` 필드).
   - 관심사별로 **핵심 1건(highlight) + 더 읽을거리 2건(articles)** 을 고른다.
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
     -d '{"text":"🗞️ 오늘의 AI 위클리 {Vol.NN} 발행 → https://imakerjun.github.io/ai-newsletter/editions/{DATE}.html\n아카이브: https://imakerjun.github.io/ai-newsletter/"}'
   ```

---

## 2. 콘텐츠 규칙

- 사실 검증: 출처가 모호하면 단정하지 말고 "~로 보인다/논의되는 중" 톤으로.
- **출처 링크 필수**: highlight와 각 article 모두 `source`(매체명) + `url`(원문 링크)을 채운다.
  - 데이터 형태: `highlight: { kicker, title, summary, detail?, source, url, foryou }`,
    `articles: [{ tag, source, url, time, title, summary, detail?, foryou }]`
  - `url`은 **실제 원문 주소**여야 한다. 확인하지 못한 링크는 지어내지 말고 그 항목을 빼라(허위 링크 금지).
- **한국어로 정리**: 영어 출처라도 `title`·`summary`·`detail`·`foryou`는 한국어로 번역·요약한다.
  원제가 중요하면 제목 끝에 괄호로 병기한다(예: "… (원제: …)"). 핵심 용어는 풀어 쓰되 필요 시 영어 병기.
- **길이 관리(긴 글 대응)**: `summary`는 2~3문장으로 짧게(스캔용). 더 설명할 게 있으면 선택적 `detail`(접히는
  ‘자세히 보기’)에 2~4문장으로 담는다. 기사 전문을 그대로 옮기지 말고, 전체 내용은 `url` 원문으로 연결한다.
- `tint`는 `tint_options` 중에서만 쓴다(디자인 일관성).
- 분량: highlight 요약 3~4문장, article 요약 2~3문장. 길어지지 않게.
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
