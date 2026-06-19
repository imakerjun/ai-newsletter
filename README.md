# 🧠 나만의 AI 학습 허브 (Claude Cowork 템플릿)

AI를 따라잡는 두 가지 길을 한 곳에. **코딩을 몰라도** Claude Cowork에게 시키면 됩니다.

- 📰 **받아보기 (자동)** — 내 관심사 맞춤 AI 뉴스레터가 매일 아침 자동 발행됩니다.
  - 아카이브(목록): `index.html` · 한 호: `editions/{날짜}.html` (관심사별 탭 + 주제마다 핵심 1건)
- 📚 **깊이 읽기 (수동)** — 공부하고 싶은 어려운 문서를 **5가지 렌즈**(🔤어원·⚡한입요약·🧒비유·🧪퀴즈·📄원문)로 재구성해 다시 읽습니다.
  - 라이브러리: `learn/index.html` · 한 문서: `learn/{슬러그}.html`
- 🤖 **사양**: [`AGENT.md`](./AGENT.md) — 자동 발행 + 수동 렌즈 생성 지시서
- 🎨 디자인: Folio(Notion 스타일) 기반, 단일 HTML, 라이트/다크 자동 · **Vercel**(또는 GitHub Pages)로 배포·누적

> 받아보기(자동) + 깊이 읽기(수동)가 **한 허브에 계속 쌓입니다.** 현재는 데모/예시 콘텐츠가 들어 있고, 실제 사용 시 최신 내용으로 교체됩니다.
> 깊이 읽기는 [doc-lenses](https://github.com/imakerjun/learning-templates/tree/main/doc-lenses) 학습 템플릿을 기술 문서용으로 각색했습니다.
> 이 저장소는 **가득 찬 예시(쇼케이스)**입니다. 직접 시작하려면 👉 [ai-newsletter-template](https://github.com/imakerjun/ai-newsletter-template)을 포크하세요.

---

## 비개발자용 따라하기 — Cowork + Vercel로 3단계

> 코딩 지식 없이, **클로드 코워크(Cowork)에게 말로** 시키면 됩니다. (전체 가이드: 템플릿 저장소 [README](https://github.com/imakerjun/ai-newsletter-template#readme))

### 1단계. 먼저 페이지로 만들어 보기 (미리보기)
Cowork에 템플릿 링크를 주며 요청합니다.
```
https://github.com/imakerjun/ai-newsletter-template 이 템플릿 활용해서,
지난 1주일간 있었던 AI 소식을 페이지로 만들어 주세요.
```
> 💡 인터넷에 올리기 전, 내 관심사로 잘 만들어지는지 먼저 ‘미리보기’로 확인하는 단계입니다.

### 2단계. Vercel로 인터넷에 올리기 (배포)
> 💡 **‘배포’** = 만든 페이지를 링크 하나로 누구나(휴대폰에서도) 볼 수 있게 인터넷에 올리는 것. 깃허브 푸시가 번거로워, **클로드가 직접 올려주는 Vercel**을 씁니다.
1. **Vercel 계정 만들기** — [vercel.com](https://vercel.com) 가입(깃허브로 로그인 가능). → 페이지 올려둘 ‘내 인터넷 공간’.
2. **클로드 커넥터에 Vercel 추가** — 클로드가 내 Vercel 공간에 올릴 수 있게 ‘연결’.
3. **토큰 발급 후 공유** — [vercel.com/account/settings/tokens](https://vercel.com/account/settings/tokens) 에서 토큰(비밀 출입증)을 만들어 클로드에게 전달. **노출 금지.**
4. **배포 요청** — `방금 만든 페이지를 Vercel로 배포해줘. 끝나면 공개 주소를 알려줘.` → `https://…vercel.app` 링크가 나옵니다.

### 3단계. 매일 아침 자동으로 받기 (스케줄)
> 💡 정해진 시간에 알아서 만들고·배포하고·보내게 하는 것. 한 번 걸어두면 매일 자동.
Cowork **스케줄 기능**으로 등록합니다.
```
매일 아침 8시에, AGENT.md 사양대로 지난 24시간 AI 소식으로 새 뉴스레터를 만들고,
Vercel로 배포한 다음, 슬랙(또는 메일)으로 배포된 링크를 보내줘.
```
- 슬랙 발송은 **Incoming Webhook URL** 하나가 필요합니다(채널 설정 → 앱 → Incoming Webhooks). 발급한 URL을 `SLACK_WEBHOOK_URL`로 알려주세요.

---

## 동작 원리 (한눈에)

```
스케줄(매일 아침)
   └─ 에이전트가 AGENT.md를 읽음
        ├─ 관심사별 최신 소식 검색 → 핵심 1건 + 더 읽을거리 2건
        ├─ '나를 위한 한 줄'(내 맥락 연결) 작성
        ├─ editions/{날짜}.html 생성  (구조 템플릿 = _TEMPLATE_edition.html)
        ├─ index.html 아카이브 목록 맨 앞에 추가  (과거 호 보존)
        ├─ Vercel로 배포  (또는 git push → GitHub Pages)
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
├── index.html               # 📰 뉴스레터 아카이브 허브 (ARCHIVE.editions 배열)
├── editions/
│   └── 2026-06-18.html       # 뉴스레터 한 호 (NEWSLETTER 데이터 객체)
├── _TEMPLATE_edition.html    # 뉴스레터 한 호의 고정 구조 템플릿
├── learn/                    # 📚 깊이 읽기(렌즈 학습) 트랙
│   ├── index.html            #   렌즈 라이브러리 (LIBRARY.docs 배열)
│   ├── prompting-fable-5.html#   한 문서 — 5가지 렌즈 (LENS_DOC 데이터 객체)
│   └── _TEMPLATE_lens.html   #   렌즈 문서의 고정 구조 템플릿
├── AGENT.md                  # 자동 발행 + 수동 렌즈 생성 사양
└── README.md
```
