# saegim Demo Recording

Playwright로 주요 기능을 자동 시연하고 GIF로 변환합니다.

## 사전 준비

```bash
# 1. Docker Compose로 서비스 실행
cd .. && make up

# 2. 서비스 헬스체크 확인
curl -f http://localhost:15000/api/v1/health

# 3. Playwright 설치
cd demo
bun install
bunx playwright install chromium
```

## 녹화

### 기능별 개별 녹화 (권장)

각 기능별로 별도 영상이 생성됩니다. 로그인/설정은 영상에 포함되지 않습니다.

```bash
# 전체 기능 데모 (setup → project-setup → labeling → overview)
bunx playwright test --project=setup --project=demo-project-setup --project=demo-labeling --project=demo-overview

# 개별 기능만 녹화
bunx playwright test --project=setup --project=demo-project-setup   # 프로젝트 생성 + OCR + 업로드
bunx playwright test --project=setup --project=demo-labeling        # 레이블 에디터
bunx playwright test --project=setup --project=demo-overview        # 프로젝트 개요 + 내보내기
```

### 올인원 녹화 (레거시)

전체 흐름을 하나의 영상으로 녹화합니다 (로그인 포함).

```bash
bunx playwright test --project=demo
```

영상은 `test-results/` 디렉토리에 `.webm` 파일로 저장됩니다 (1920x1080).

## 데모 프로젝트 구조

| 파일 | 내용 | 영상 |
|------|------|------|
| `auth-setup.ts` | 로그인 + 다크모드 + storageState 저장 | 없음 |
| `demo-project-setup.spec.ts` | 프로젝트 생성 → OCR 설정 → PDF 업로드 | O |
| `demo-labeling.spec.ts` | OCR 추출 수락 → 요소 검사 → element index → bbox → reading order → 저장 | O |
| `demo-overview.spec.ts` | 작업 현황 대시보드 → 내보내기 | O |
| `record-demo.ts` | 올인원 레거시 (전체 흐름) | O |
| `helpers.ts` | 공통 유틸리티 + API 헬퍼 | - |

## GIF 변환

```bash
bash convert-to-gif.sh                          # 기본값 (800px, 12fps)
bash convert-to-gif.sh "" demo.gif 640 8        # 작은 파일 (GitHub용)
bash convert-to-gif.sh "" demo-hq.gif 1280 15   # 고화질
```

## 커스터마이징

- **속도 조절**: `helpers.ts`의 `PAUSE_*` 상수와 `playwright.config.ts`의 `slowMo` 조절
- **시나리오 추가**: 각 spec 파일에 `test.step()` 블록 추가

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `BASE_URL` | `http://localhost:13000` | 프론트엔드 URL |
| `API_URL` | `http://localhost:15000` | 백엔드 API URL |
| `ADMIN_PASSWORD` | (auto-detect) | 관리자 비밀번호 |
| `GEMINI_API_KEY` | (from .env) | Gemini API 키 |
