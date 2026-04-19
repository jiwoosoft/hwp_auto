# GUI 실행 가이드

## 현재 GUI 성격
현재 GUI는 완성형 에디터라기보다,
**실제 rhwp 에디터를 메인에 띄우고 오른쪽에서 MCP 기반 작업을 제어하는 로컬 워크벤치**다.

## 실행 순서
두 프로세스를 함께 띄운다.

### 1. rhwp-studio 에디터 실행
```bash
./scripts/run_rhwp_studio.sh
```
기본 주소:
```text
http://127.0.0.1:7700
```

### 2. GUI 워크벤치 실행
```bash
./scripts/run_gui.sh
```
기본 주소:
```text
http://127.0.0.1:8876
```

## 환경변수
### GUI 포트 변경
```bash
MASTER_OF_HWP_GUI_PORT=8899 ./scripts/run_gui.sh
```

### 로컬 파일 허용 범위
기본적으로 사용자 홈 디렉터리(`$HOME`)를 열 수 있다.
필요하면 범위를 좁힐 수 있다.

```bash
MASTER_OF_HWP_ALLOWED_WORKSPACE=/Users/moon/Documents ./scripts/run_gui.sh
```

## 현재 가능한 것
- 로컬 파일 브라우저로 HWP/HWPX/TXT/MD 탐색
- 선택한 파일을 GUI 세션에 열기
- 실제 rhwp-studio 에디터를 메인 pane에 띄우기
- 텍스트 추출
- 구조 추출
- 문단 치환
- 문단 삽입
- 저장
- 저장본 검증

## 사용 흐름
1. `run_rhwp_studio.sh` 실행
2. `run_gui.sh` 실행
3. GUI에서 로컬 파일을 탐색해 선택
4. `문서 열기`를 누르면 세션이 열리고, 에디터 iframe에 문서가 로드된다
5. 오른쪽 패널에서 텍스트 추출/구조 추출/문단 편집/저장/검증 수행

## 현재 한계
- 에디터 pane은 실제 rhwp-studio이지만, GUI는 아직 얇은 조작 패널이다.
- 브라우저 자동화 환경에서는 iframe 내부 편집까지 완전히 검증하지 못했다.
- table creation roundtrip persistence는 아직 실패 상태다.
- 완전한 시각적 diff/preview UX는 아직 미완성이다.
