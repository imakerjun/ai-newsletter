# 🗞️ 나만의 AI 뉴스레터 (Claude Cowork 템플릿)

내 관심사에 맞춘 AI 소식을, 내 취향의 디자인으로, 매일 아침 자동 발행하는 개인 뉴스레터.
**코딩을 몰라도** Claude Cowork에게 시키면 됩니다.

- 📄 **아카이브(목록)**: `index.html` — 발행한 호가 쌓이는 곳
- 📰 **한 호**: `editions/{날짜}.html` — 관심사별 탭 + 주제마다 핵심 1건
- 🤖 **발행 사양**: [`AGENT.md`](./AGENT.md) — 에이전트가 매일 따라 하는 지시서
- 🎨 디자인: Folio(Notion 스타일) 디자인 시스템 기반, 단일 HTML, 라이트/다크 자동

> 데모/예시 콘텐츠가 들어 있습니다. 실제 발행 시 에이전트가 최신 소식으로 교체합니다.

---

## 비개발자용 따라하기 (4단계)

### 1. 이 템플릿을 내 저장소로 복사
GitHub에서 이 레포 상단의 **`Use this template` → `Create a new repository`** 를 누릅니다.
(내 계정에 똑같은 구조의 저장소가 생깁니다. 깃 명령어 필요 없음)

### 2. Claude Cowork에 내 저장소를 연결
Claude Cowork에서 방금 만든 저장소를 작업 공간으로 연결합니다.

### 3. 내 관심사로 바꾸기 — 아래 프롬프트를 복사해서 붙여넣기
```
이 저장소는 내 AI 뉴스레터 템플릿이야. AGENT.md의 "내 설정"에서 interests를
내 관심사로 바꿔줘. 내 관심사는 다음과 같아:
- (예) AI로 디자인 잘하는 법
- (예) 개발자가 꼭 알아야 하는 AI 소식
- (원하는 만큼 추가)
그리고 persona_context에 나를 한두 문장으로 소개해줘: (예: 마케터, 신상품 기획 담당)
바꾼 뒤, 오늘 날짜로 첫 호를 한 번 만들어서 editions/ 에 저장하고
index.html 아카이브에도 추가해줘.
```

### 4. 매일 아침 자동 발행 걸기 (스케줄)
```
매일 아침 8시에 AGENT.md 사양대로 새 호를 발행하고, 커밋·푸시하고,
슬랙으로 배포 링크를 보내도록 스케줄을 등록해줘.
```
- 처음 한 번 **GitHub Pages**를 켜두면(`Settings → Pages → Branch: main`),
  push할 때마다 `https://{내아이디}.github.io/{레포이름}/` 로 자동 배포됩니다.
- 슬랙 발송은 **Incoming Webhook URL** 하나가 필요합니다(채널 설정 → 앱 → Incoming Webhooks).
  발급한 URL을 환경변수 `SLACK_WEBHOOK_URL`로 알려주세요.

---

## 동작 원리 (한눈에)

```
스케줄(매일 아침)
   └─ 에이전트가 AGENT.md를 읽음
        ├─ 관심사별 최신 소식 검색 → 핵심 1건 + 더 읽을거리 2건
        ├─ '나를 위한 한 줄'(내 맥락 연결) 작성
        ├─ editions/{날짜}.html 생성  (구조 템플릿 = _TEMPLATE_edition.html)
        ├─ index.html 아카이브 목록 맨 앞에 추가  (과거 호 보존)
        ├─ git commit & push  →  GitHub Pages 자동 배포
        └─ 슬랙 웹훅으로 배포 링크 발송
```

핵심: **"읽을 콘텐츠를 만드는 일" 자체를 에이전트에게 위임**하고,
나는 매일 아침 슬랙으로 도착한 링크만 열어보면 됩니다.

---

## 직접 열어보기 (로컬)
```bash
# 단순 정적 파일이라 더블클릭으로도 열리지만, 상대경로 링크까지 보려면:
python3 -m http.server 8000
# → http://localhost:8000  (아카이브)
```

## 구조
```
.
├── index.html               # 아카이브 허브 (ARCHIVE.editions 배열로 호 목록 관리)
├── editions/
│   └── 2026-06-18.html       # 한 호 (NEWSLETTER 데이터 객체로 콘텐츠 관리)
├── _TEMPLATE_edition.html    # 한 호의 고정 구조 템플릿 (에이전트가 데이터만 교체)
├── AGENT.md                  # 발행 자동화 사양
└── README.md
```
