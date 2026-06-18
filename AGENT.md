# AGENT.md — 러닝 에이전트 발행 지시서

이 문서는 **Claude Cowork(또는 Claude Code) 스케줄 에이전트**가 매번 실행할 때 읽는 사양이다.
목표: 내 관심사에 맞춘 AI 뉴스레터 한 호를 생성하고, 아카이브에 추가하고, 배포하고, 슬랙으로 알린다.

---

## 0. 내 설정 (이 부분만 사람이 편집)

```yaml
owner: 메이커준
cadence: 매일 아침 08:00 (Asia/Seoul)
interests:                      # 관심사 = 탭. 추가/삭제 자유. 3~5개 권장.
  - id: dev
    label: 개발자가 꼭 아는 AI
    icon: 🤖
    tint: blue
    focus: 에이전트형 코딩, 모델 릴리스, 개발 생산성, 컨텍스트 엔지니어링
  - id: design
    label: AI로 디자인 잘하기
    icon: 🎨
    tint: purple
    focus: design-to-code, 디자인 시스템을 컨텍스트로 주기, AI 디자인 도구
  - id: teach
    label: AI로 가르치기
    icon: 🎓
    tint: green
    focus: 개인화 학습, AI 튜터, 바이브코딩 교육 사례
  - id: build
    label: 에이전트 만들기
    icon: 🛠️
    tint: orange
    focus: 서브에이전트/하네스 패턴, MCP, 에이전트 평가(eval)
persona_context: |             # '나를 위한 한 줄'을 쓸 때 참고할 내 맥락
  우아한형제들 FE팀, 우아한테크코스 코치, 하네스/에이전트 엔지니어링과
  바이브코딩 워크숍을 운영. 교육·코칭에 바로 쓸 수 있는 각도로 연결할 것.
slack_webhook_env: SLACK_WEBHOOK_URL   # 발송용 Incoming Webhook (환경변수)
tint_options: [blue, purple, green, orange, pink]
```

---

## 1. 실행 순서

1. **오늘 날짜**를 `YYYY-MM-DD`(Asia/Seoul)로 구한다. → `{DATE}`
2. `interests`의 각 관심사마다 **최신 소식을 웹 검색**한다(최근 7일 우선).
   - 신뢰 가능한 출처(공식 블로그, 릴리스 노트, 1차 자료)를 우선한다.
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
- 데모가 아닌 **실제 발행**에서는 각 기사에 가능하면 출처 링크를 포함한다(요약 신뢰도↑).
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
