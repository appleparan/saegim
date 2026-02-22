# E2E Tests

Playwright 기반 end-to-end 테스트. Docker Compose로 전체 스택(postgres, backend, frontend)을 띄우고 API + UI를 검증한다.

## 사전 준비

```bash
cd e2e
bun install
bun run setup   # Chromium 설치 + 테스트 PDF 다운로드
```

## 기본 테스트 (GPU 불필요)

기본 프로파일은 postgres + backend + frontend만 실행한다. pdfminer.six 폴백으로 OCR 추출하므로 GPU가 필요 없다.

```bash
# 1. 서비스 시작
bun run docker:up

# 2. 테스트 실행
bun run test

# 3. 개별 테스트 실행
bun run test:health      # health check만
bun run test:workflow     # 전체 워크플로우
bun run test:benchmark    # API 벤치마크

# 4. UI 모드 (디버깅)
bun run test:ui

# 5. 결과 리포트
bun run report

# 6. 정리
bun run docker:down
```

## GPU 테스트 (vLLM + Chandra)

`gpu` 프로파일은 기본 서비스에 vLLM 서버를 추가한다. vLLM은 `datalab-to/chandra` (9B) 모델을 로드하며, **24GB+ VRAM GPU**가 필요하다.

### 요구사항

- NVIDIA GPU (24GB+ VRAM, e.g. RTX 4090, A5000, A6000)
- NVIDIA Container Toolkit (`nvidia-docker2`)
- 첫 실행 시 모델 다운로드 (~18GB)

### 실행

```bash
# 1. GPU 프로파일로 서비스 시작
bun run docker:gpu:up

# 2. vLLM 모델 로딩 대기 (첫 실행 시 다운로드 포함 10-30분)
#    로그로 진행 상황 확인:
docker compose -f docker-compose.e2e.yml --profile gpu logs -f vllm

# 3. GPU 테스트 실행
bun run test:gpu

# 4. 정리
bun run docker:gpu:down
```

### HuggingFace 캐시

모델 다운로드를 영속화하려면 `HF_CACHE_DIR` 환경변수를 설정한다:

```bash
# 기본값: ~/.cache/huggingface
export HF_CACHE_DIR=/data/models/huggingface
bun run docker:gpu:up
```

## 테스트 구조

```text
e2e/
├── docker-compose.e2e.yml    # Docker Compose (기본 + gpu 프로파일)
├── playwright.config.ts      # Playwright 설정 (chromium, gpu 프로젝트)
├── package.json
├── helpers/
│   ├── api.ts                # API 헬퍼 (CRUD, OCR config, vLLM health)
│   ├── pdf.ts                # 테스트 PDF 다운로드 (attention.pdf)
│   └── timer.ts              # 벤치마크 타이머
├── tests/
│   ├── health.spec.ts        # 서비스 health check
│   ├── workflow.spec.ts      # 프로젝트 생성 → PDF 업로드 → 레이블링 → 내보내기
│   ├── extraction.spec.ts    # pdfminer 추출 → 수락 워크플로우
│   ├── ocr-config.spec.ts    # OCR 엔진 설정 API (engine_type CRUD + validation)
│   ├── hybrid-labeling.spec.ts
│   ├── benchmark.spec.ts     # API 응답시간 벤치마크
│   └── gpu/
│       └── vllm-extraction.spec.ts  # vLLM chandra 추출 (GPU 전용)
└── fixtures/
    └── attention.pdf         # 테스트 PDF (자동 다운로드)
```

## Docker Compose 서비스

| 서비스 | 프로파일 | 포트 | 설명 |
| ------------- | -------- | ----- | ------------------------------------------ |
| postgres | 기본 | 25432 | PostgreSQL 18 |
| backend | 기본 | 25000 | FastAPI 서버 |
| frontend | 기본 | 23000 | SvelteKit (Nginx) |
| vllm | gpu | 28000 | vLLM OpenAI API (datalab-to/chandra) |

## 환경변수

| 변수 | 기본값 | 설명 |
| ------------------- | ------------------------- | ------------------------------- |
| `E2E_BACKEND_URL` | `http://localhost:25000` | 백엔드 API URL |
| `E2E_FRONTEND_URL` | `http://localhost:23000` | 프론트엔드 URL |
| `E2E_VLLM_URL` | `http://localhost:28000` | vLLM API URL |
| `HF_CACHE_DIR` | `~/.cache/huggingface` | HuggingFace 모델 캐시 경로 |

## Playwright 프로젝트

| 프로젝트 | 매칭 패턴 | Timeout | 설명 |
| ---------- | ----------------------------------- | ------- | ---------------------- |
| `chromium` | `tests/*.spec.ts` (gpu/ 제외) | 2분 | 기본 테스트 |
| `gpu` | `tests/gpu/*.spec.ts` | 10분 | GPU 전용 (vLLM 추출) |

`bun run test`는 `chromium` 프로젝트만 실행하고, `bun run test:gpu`는 `gpu` 프로젝트만 실행한다.
