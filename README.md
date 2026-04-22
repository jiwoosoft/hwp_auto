<div align="center">

# 한글의 달인 · master-of-hwp

**AI가 한컴오피스 문서(.hwp / .hwpx)를 읽고, 이해하고, 편집하는 오픈소스 플랫폼**

**🏫 경기도교육청 소속 현직 초등학교 교사가 만든 실무 도구**
*— [배움의 달인](https://www.youtube.com/@%EB%B0%B0%EC%9B%80%EC%9D%98%EB%8B%AC%EC%9D%B8-p5v) · 교육 현장의 한글 업무를 AI로 —*

[![PyPI](https://img.shields.io/pypi/v/master-of-hwp.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/master-of-hwp/)
[![Studio](https://img.shields.io/pypi/v/master-of-hwp-studio.svg?label=studio&style=for-the-badge&logo=pypi&logoColor=white&color=7c3aed)](https://pypi.org/project/master-of-hwp-studio/)
[![Python](https://img.shields.io/pypi/pyversions/master-of-hwp.svg?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/master-of-hwp/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br />

<a href="https://www.youtube.com/@%EB%B0%B0%EC%9B%80%EC%9D%98%EB%8B%AC%EC%9D%B8-p5v" target="_blank">
  <img src="https://img.shields.io/badge/YouTube-배움의_달인-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube 배움의 달인" />
</a>
&nbsp;
<a href="https://x.com/reallygood83" target="_blank">
  <img src="https://img.shields.io/badge/X-@reallygood83-000000?style=for-the-badge&logo=x&logoColor=white" alt="X @reallygood83" />
</a>
&nbsp;
<a href="https://github.com/reallygood83/master-of-hwp" target="_blank">
  <img src="https://img.shields.io/badge/GitHub-star-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub star" />
</a>

<br /><br />

**OS 지원**
&nbsp;
<img src="https://img.shields.io/badge/macOS-✅-000000?style=flat-square&logo=apple&logoColor=white" alt="macOS" />
<a href="#-windows-사용자-가이드"><img src="https://img.shields.io/badge/Windows-✅_가이드_보기-0078D4?style=flat-square&logo=windows&logoColor=white" alt="Windows" /></a>
<img src="https://img.shields.io/badge/Linux-✅-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux" />

**[English](README.en.md)** · **[CHANGELOG](CHANGELOG.md)** · **[로드맵](docs/ROADMAP.md)** · **[아키텍처](docs/ARCHITECTURE.md)** · **[기여하기](CONTRIBUTING.md)** · **[🪟 Windows 가이드](#-windows-사용자-가이드)**

</div>

---

## 🎯 왜 이 프로젝트인가

한국의 공공·교육·업무 현장은 아직도 한글 문서(`.hwp` / `.hwpx`)를 표준으로 씁니다. 하지만 대부분의 AI 도구는 HWP를 직접 다루지 못하고, DOCX로 변환해 편집한 뒤 돌려놓는 과정에서 **서식·표·문단 속성이 망가집니다**.

**한글의 달인(master-of-hwp)** 은 이 문제를 해결합니다:

- ✅ **진짜 포맷 유지** — 변환 없이 원본 HWP/HWPX를 그대로 열고 저장
- ✅ **구조 이해** — 섹션·문단·표의 구조를 AI에 그대로 노출
- ✅ **AI-네이티브 편집** — "3번째 문단을 공식 문체로 바꿔줘" 같은 자연어 지시로 수정
- ✅ **라운드트립 보장** — 편집 → 저장 → 재로딩 후에도 구조 훼손 없음

---

## 🚀 30초 시작

### 📘 개발자용 — Python 라이브러리

```bash
pip install master-of-hwp
```

```python
from master_of_hwp import HwpDocument

doc = HwpDocument.open("보도자료.hwpx")
print(doc.summary())                         # 구조 요약 (AI 컨텍스트용)

for s, p, text in doc.find_paragraphs("보도"):
    print(f"§{s}.{p}: {text}")

edited = doc.replace_paragraph(0, 0, "새 문단 내용")
edited.path.with_suffix(".edited.hwpx").write_bytes(edited.raw_bytes)
```

### 🎨 일반 사용자용 — Studio (WYSIWYG GUI)

```bash
pip install master-of-hwp-studio
mohwp studio
```

→ 브라우저 자동 실행 → **rhwp WYSIWYG 에디터 + AI 작업 패널** 한 화면에서 사용.

```bash
mohwp mcp-config   # OS별 Claude Desktop 설정 경로 자동 감지해 스니펫 출력
```

> 💡 **Windows 사용자**: 더 자세한 설치 방법과 3가지 AI provider 경로는 [🪟 Windows 사용자 가이드](#-windows-사용자-가이드) 섹션을 참고하세요.

---

## ✨ 주요 기능

| 기능 | 상세 |
|---|---|
| **문서 열기** | `.hwp` / `.hwpx` 파일을 네이티브 포맷 그대로 로드 |
| **구조 분석** | 섹션·문단·표·셀을 JSON으로 반환 (`summary()`, `section_tables` 등) |
| **문단/셀 편집** | `replace_paragraph`, `replace_table_cell_paragraph` 불변 API |
| **AI 자연어 편집** | `doc.ai_edit("내용을 공식체로")` — Claude/Codex/API 모두 지원 |
| **멀티모달** | 이미지·PDF 첨부 → Claude Code CLI/Codex CLI가 Read/인식 |
| **템플릿 라이브러리** | 자주 쓰는 양식 저장/불러오기 (`~/.mohwp/templates/`) |
| **왕복 재현율** | `fidelity.harness` 로 바이트 레벨 검증 |
| **MCP 서버** | Claude Desktop 에서 `open_document`, `find_paragraphs`, `replace_paragraph` 등 도구 호출 |

---

## 🧠 AI 제공자

| 제공자 | 사용 방식 | 우선순위 |
|---|---|---|
| **Claude Code CLI** | `claude -p "prompt"` (구독 사용, API 키 불필요) | 🥇 1순위 |
| **Claude API** | `ANTHROPIC_API_KEY` 환경변수 | 🥈 2순위 |
| **Codex CLI** | `codex exec` (ChatGPT Plus/Pro 구독) | 🥇 1순위 |
| **OpenAI API** | `OPENAI_API_KEY` 환경변수 | 🥈 2순위 |
| **Rule-based** | 위 어떤 것도 없을 때 폴백 | 🥉 항상 가능 |

---

## 🪟 Windows 사용자 가이드

**한국 공공·교육·업무 현장의 대다수가 Windows 환경이라 매우 중요합니다. v0.2.4+부터 Windows 3가지 경로 모두 지원합니다.**

### 📦 기본 설치 (공통)

Python 3.11+ 이 필요합니다. [python.org](https://www.python.org/downloads/windows/) 에서 설치 시 **"Add Python to PATH" 체크** 필수.

```powershell
# PowerShell (일반 권한)
py -m pip install master-of-hwp-studio
mohwp studio
```

→ 브라우저 자동 실행 → **방화벽 팝업이 뜨면 "액세스 허용"** 클릭

---

### AI Provider 3가지 선택지

| 경로 | 난이도 | 구독 활용 | 소요 시간 |
|---|---|---|---|
| **A. API 키** | ⭐ 쉬움 | ❌ API 크레딧 별도 | 10초 |
| **B. WSL 전체 통합** | ⭐⭐⭐ 중간 | ✅ 구독 그대로 | 15분 |
| **C. 하이브리드 (자동 브릿지)** | ⭐⭐ 쉬움 | ✅ 구독 그대로 | 5분 |

---

#### 🔑 경로 A — API 키 (가장 쉬움 · 추천)

Anthropic Claude API 또는 OpenAI API 키만 있으면 즉시 동작:

```powershell
# Claude 쓰는 경우
setx ANTHROPIC_API_KEY "sk-ant-..."

# 또는 OpenAI 쓰는 경우
setx OPENAI_API_KEY "sk-..."

# 새 PowerShell 창 열고
mohwp studio
```

- API 키 발급: [Anthropic Console](https://console.anthropic.com/settings/keys) · [OpenAI Platform](https://platform.openai.com/api-keys)
- ⚠️ Claude Pro/Max 구독과 **API 크레딧은 별도 과금**
- ✅ WSL 설치 불필요, 가장 안정적

---

#### 🐧 경로 B — WSL 전체 통합 (구독 그대로)

이미 Claude Pro/Max 나 ChatGPT Plus 구독 중이면, WSL 안에서 **구독을 그대로** 사용:

```powershell
# 1) WSL 설치 (관리자 PowerShell, 1회만)
wsl --install
# → 재부팅 후 Ubuntu 터미널 자동으로 열림
```

```bash
# 2) WSL Ubuntu 안에서 필수 패키지 설치
sudo apt update
sudo apt install -y python3-pip python3.11-venv nodejs npm

# 3) Claude Code CLI 설치 + 구독 로그인
npm install -g @anthropic-ai/claude-code
claude login   # 브라우저 열리면 Claude 구독 계정으로 로그인

# 4) Studio 설치 + 실행
pip install master-of-hwp-studio
mohwp studio
```

- Windows 브라우저에서 `http://localhost:<port>` 바로 접속 (WSL2 자동 포워딩)
- ✅ **구독 그대로 사용** — API 크레딧 불필요
- ❌ WSL 사용이 익숙하지 않으면 러닝 커브

---

#### 🔗 경로 C — 하이브리드 (v0.2.4+ 자동 브릿지 · 권장)

Studio 는 **Windows native** 에서 돌고, `claude`/`codex` CLI 만 WSL 안에 설치. 자동으로 브릿지 됩니다.

**Step 1 — WSL 에 CLI만 설치**

```powershell
wsl --install   # 이미 WSL 있으면 스킵
```
```bash
# WSL Ubuntu 안에서 (한 번만)
sudo apt install -y nodejs npm
npm install -g @anthropic-ai/claude-code
claude login
```

**Step 2 — Windows 에 Studio 설치 + 실행**

```powershell
py -m pip install master-of-hwp-studio
mohwp studio
```

그러면 Studio 가 자동으로:
```
claude CLI 찾음? → Windows PATH 에 없음
              ↓
wsl.exe 있음? → 있음
              ↓
wsl -e which claude → 찾음!
              ↓
이후 모든 AI 호출: wsl -e claude -p "..."
```

**파일 경로도 자동 변환:**
```
C:\Users\moon\Desktop\photo.png
         ↓ (자동)
/mnt/c/Users/moon/Desktop/photo.png
         ↓
wsl -e codex exec -i /mnt/c/Users/moon/Desktop/photo.png ...
```

- ✅ **구독 그대로 사용**
- ✅ Windows native 에서 편안하게 Studio 사용
- ✅ 파일 첨부는 그냥 Windows 파일 고르면 알아서 처리

---

### 🔧 Windows 트러블슈팅

| 문제 | 해결 |
|---|---|
| `mohwp` 명령어 못 찾음 | 새 PowerShell 창 열기 (환경변수 갱신) 또는 `py -m master_of_hwp_studio studio` |
| 방화벽 팝업 | "액세스 허용" 클릭 (localhost 통신에만 필요) |
| `setx` 로 설정한 환경변수 반영 안 됨 | 새 터미널 창에서 확인 — `setx` 는 새 프로세스부터 적용 |
| WSL 설치 후 Ubuntu 안 보임 | `wsl -l` 로 배포판 확인, 없으면 `wsl --install -d Ubuntu` |
| `claude login` 브라우저 안 열림 | WSL 안에서 `powershell.exe start <URL>` 로 Windows 브라우저 호출 |
| HWP 파일 열기 느림 | 대용량 파일은 Studio 가 WASM 로드 후 5-10초 소요 |

### 🧑‍🏫 교사·공무원용 설치 팁

- **IT 부서 정책으로 `pip` 가 막힌 경우**: [Anaconda](https://www.anaconda.com/download) 나 [Python for Windows Store 앱](https://apps.microsoft.com/detail/9NCVDN91XZQP) 으로 우회
- **오피스 환경에서 Python 설치 불가**: [Studio Portable 배포 요청 이슈](https://github.com/reallygood83/master-of-hwp/issues) 로 알려주세요 (roadmap 반영 예정)
- **프록시 환경**: `pip install --proxy http://proxy.company.com:8080 master-of-hwp-studio`

---

## 🏗 아키텍처

```
┌──────────────────────────────────────────┐
│  사용자 (교사 · 공무원 · 개발자)         │
└────────────┬─────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────┐    ┌──────────────────┐
│ Claude   │    │ 한글의 달인 Studio│
│ Desktop  │    │ (mohwp studio)   │
└────┬─────┘    └────────┬─────────┘
     │ MCP              │ HTTP
     ▼                   ▼
┌────────────────────────────────┐
│  master-of-hwp Core API        │
│  (HwpDocument, ai_edit, ...)   │
└────────────┬───────────────────┘
             │
   ┌─────────┴─────────┐
   ▼                   ▼
┌────────────┐   ┌──────────────────┐
│ olefile +  │   │ rhwp (Rust+WASM) │
│ zipfile    │   │ WYSIWYG 에디터   │
└────────────┘   └──────────────────┘
```

- **Python Core** — HWP 5.0 (CFBF) + HWPX (OOXML) 파싱, 편집 프리미티브
- **rhwp** — [edwardkim/rhwp](https://github.com/edwardkim/rhwp) 의 Rust + WebAssembly WYSIWYG 편집 엔진 (번들 포함)
- **Studio** — 웹 GUI + MCP 서버 통합 (`mohwp` CLI)

---

## 📦 패키지

| 이름 | 용도 | 설치 |
|---|---|---|
| [`master-of-hwp`](https://pypi.org/project/master-of-hwp/) | Python Core API | `pip install master-of-hwp` |
| [`master-of-hwp`](https://pypi.org/project/master-of-hwp/)`[ai]` | + AI provider SDK | `pip install "master-of-hwp[ai]"` |
| [`master-of-hwp-studio`](https://pypi.org/project/master-of-hwp-studio/) | GUI + MCP + rhwp 번들 | `pip install master-of-hwp-studio` |

---

## 🛣 로드맵

- **v0.1** ✅ — 읽기 API + HWPX 문단 편집 + fidelity
- **v0.2** ✅ — 표 셀 편집 · 자연어 편집 루프 · CLI provider · Studio GUI · rhwp 번들 · 템플릿 라이브러리 · 멀티모달 첨부
- **v0.3** — HWP 5.0 완전 쓰기 (CFBF resize writer) · 문단 삽입/삭제 · 표 추가/삭제
- **v0.4** — Agentic edit loop (intent → locate → apply → verify → rollback)
- **v1.0** — API 호환성 계약 고정

세부: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## 🤝 기여하기

**이 프로젝트는 커뮤니티 기여를 환영합니다.**

- 🐛 **버그 리포트 / 기능 요청**: [Issues](https://github.com/reallygood83/master-of-hwp/issues)
- 💻 **코드 기여**: fork → branch → PR ([CONTRIBUTING.md](CONTRIBUTING.md))
- 💬 **질문 / 토론**: [Discussions](https://github.com/reallygood83/master-of-hwp/discussions)

도움 주시면 좋은 영역:
- HWP 5.0 CFBF 쓰기 엔진 (v0.3)
- 문단/표 삽입·삭제 연산
- 추가 LLM provider (Gemini, 로컬 Ollama)
- Windows/Linux 인스톨러
- 접근성(a11y) 개선

작은 기여도 환영합니다 — 문서 오탈자, 번역, 샘플 파일 모두 가치 있습니다.

---

## 👨‍🏫 만든 사람

**[배움의 달인](https://www.youtube.com/@%EB%B0%B0%EC%9B%80%EC%9D%98%EB%8B%AC%EC%9D%B8-p5v)** — 경기도교육청 소속 **현직 초등학교 교사**

교실에서 매일 가정통신문 · 공문서 · 기안문을 HWP 로 작성하면서 느낀 **"이거 AI 가 해줄 수 있을 텐데"** 라는 갈증이 이 프로젝트의 출발점입니다. 그래서 이 도구는 단순한 라이브러리가 아니라 **실제 교사·공무원의 하루를 바꾸기 위한 실무 도구**로 설계됐습니다.

- 📺 **YouTube**: [@배움의달인](https://www.youtube.com/@%EB%B0%B0%EC%9B%80%EC%9D%98%EB%8B%AC%EC%9D%B8-p5v) — AI · 교육공학 · 업무 자동화 콘텐츠
- 𝕏 **X (Twitter)**: [@reallygood83](https://x.com/reallygood83)
- 💬 **문의/제안**: [GitHub Discussions](https://github.com/reallygood83/master-of-hwp/discussions)

> 교사·공무원·행정직 분들께: 현장에서 안 되는 부분이나 "이 기능 있었으면" 하는 것 있으면 [이슈](https://github.com/reallygood83/master-of-hwp/issues) 로 남겨주세요. 같은 현장 경험으로 최대한 반영합니다.

---

## 🙏 감사의 말

이 프로젝트는 [**edwardkim/rhwp**](https://github.com/edwardkim/rhwp) (by [@edwardkim](https://github.com/edwardkim)) 의 Rust + WebAssembly HWP 파싱/렌더링 엔진을 기반으로 합니다. `master-of-hwp-studio` 의 WYSIWYG 에디터는 rhwp 가 있기에 가능합니다. rhwp 도 같이 ⭐ 눌러주세요.

---

## 📄 라이선스

MIT — [LICENSE](LICENSE) 참고.

---

<div align="center">

**만든 사람** — 배움의 달인

<a href="https://www.youtube.com/@%EB%B0%B0%EC%9B%80%EC%9D%98%EB%8B%AC%EC%9D%B8-p5v" target="_blank">📺 YouTube</a>
&nbsp;·&nbsp;
<a href="https://x.com/reallygood83" target="_blank">𝕏 @reallygood83</a>
&nbsp;·&nbsp;
<a href="https://github.com/reallygood83" target="_blank">GitHub</a>

*도움이 되셨다면 ⭐ 한 번 눌러주시면 큰 힘이 됩니다.*

</div>
