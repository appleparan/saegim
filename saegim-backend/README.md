# saegim-backend

saegim 레이블링 플랫폼의 백엔드. FastAPI + asyncpg 기반 REST API 서버.

## 기술 스택

| 분류 | 기술 |
| ---- | ---- |
| **프레임워크** | FastAPI |
| **DB 드라이버** | asyncpg (raw SQL) |
| **데이터베이스** | PostgreSQL 15+ (JSONB) |
| **스키마** | Pydantic |
| **PDF 처리** | pypdfium2 + pdfminer.six |
| **OCR** | 4종 Strategy 패턴 (Gemini, vLLM/Chandra, PP-StructureV3, pdfminer) |
| **포맷터** | ruff format |
| **린터** | ruff check |
| **타입 체커** | ty |
| **테스트** | pytest |
| **패키지 관리** | uv |

## 프로젝트 구조

```text
saegim-backend/
├── src/saegim/
│   ├── app.py                    # FastAPI 앱 팩토리
│   ├── cli.py                    # CLI 진입점
│   ├── api/
│   │   └── routes/               # REST 엔드포인트
│   ├── schemas/                  # Pydantic 모델 (EngineType, OcrConfig 등)
│   ├── services/
│   │   ├── engines/              # OCR 엔진 Strategy 패턴
│   │   │   ├── base.py           # BaseOCREngine ABC
│   │   │   ├── factory.py        # build_engine() 팩토리
│   │   │   ├── pdfminer_engine.py
│   │   │   ├── commercial_api_engine.py
│   │   │   ├── integrated_server_engine.py
│   │   │   └── split_pipeline_engine.py
│   │   ├── ppstructure_service.py   # PP-StructureV3 HTTP 클라이언트
│   │   ├── gemini_ocr_service.py    # Gemini VLM 프로바이더
│   │   ├── vllm_ocr_service.py      # vLLM 프로바이더 (Chandra 등)
│   │   └── ocr_pipeline.py          # 2단계 파이프라인 오케스트레이터
│   ├── repositories/             # 데이터 접근 (raw SQL)
│   └── core/                     # DB 커넥션 풀, 설정
├── migrations/                   # SQL 마이그레이션
├── tests/                        # pytest 유닛/통합 테스트
│   ├── api/                      # API 라우트 테스트
│   ├── schemas/                  # Pydantic 스키마 테스트
│   └── services/                 # 서비스 로직 테스트
├── docs/                         # MkDocs 문서
└── pyproject.toml                # 프로젝트 설정 (uv, ruff, ty 등)
```

## 개발

```bash
cd saegim-backend

# 환경 설정
uv python install 3.14
uv python pin 3.14
uv sync --group dev --group docs

# 서버 실행
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000

# 코드 퀄리티
uv run ruff format                  # 포맷팅
uv run ruff check --fix             # 린트
uv run ty check                     # 타입 체크
uv run pytest --cov                 # 테스트 + 커버리지

# 문서
uv run mkdocs serve                 # 로컬 문서 서버
uv run mkdocs build                 # 문서 빌드
```

## 릴리스

```bash
sh scripts/release.sh
```

`release.sh`는 다음을 수행한다:

1. `git-cliff`로 다음 버전을 결정
2. `CHANGELOG.md`와 `RELEASE.md` 생성
3. 커밋, 태그, 푸시

---

*이 프로젝트 템플릿은 [copier-modern-ml](https://github.com/appleparan/copier-modern-ml) 기반으로 생성되었습니다.*
