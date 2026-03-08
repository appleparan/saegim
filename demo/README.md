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

```bash
bunx playwright test --project=demo
```

영상은 `test-results/` 디렉토리에 `.webm` 파일로 저장됩니다 (1920x1080).

## GIF 변환

```bash
bash convert-to-gif.sh                          # 기본값 (800px, 12fps)
bash convert-to-gif.sh "" demo.gif 640 8        # 작은 파일 (GitHub용)
bash convert-to-gif.sh "" demo-hq.gif 1280 15   # 고화질
```

## 데모 시나리오

| 장면 | 내용 |
|------|------|
| 1 | 로그인 (admin/admin) |
| 2 | 프로젝트 생성 |
| 3 | PDF 업로드 (Attention Is All You Need) |
| 4 | 레이블 에디터 (바운딩 박스 그리기, 줌, 읽기 순서) |
| 5 | 페이지 네비게이션 |
| 6 | 프로젝트 현황 대시보드 |
| 7 | JSON Export |
| 8 | 작업 대시보드 |

## 커스터마이징

- **속도 조절**: `record-demo.ts`의 `PAUSE_*` 상수와 `playwright.config.ts`의 `slowMo` 조절
- **시나리오 추가**: `record-demo.ts`에 `test.step()` 블록 추가

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `BASE_URL` | `http://localhost:13000` | 프론트엔드 URL |
| `API_URL` | `http://localhost:15000` | 백엔드 API URL |
