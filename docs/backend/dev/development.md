# 개발 가이드

## 개발 환경 설정

```bash
# 의존성 설치
uv sync --group dev --group docs

# pre-commit 훅 설치
uvx pre-commit install
```

## 코드 스타일

| 항목 | 규칙 |
| ------ | ------ |
| Python 버전 | 3.13+ |
| 줄 길이 | 100자 |
| 따옴표 | 작은따옴표 (`'`) |
| 포매터 | ruff format |
| 린터 | ruff check |
| 타입 체커 | ty check |
| 독스트링 | Google 컨벤션 |

### 명령어

```bash
# 포맷팅
uv run ruff format

# 린트 검사
uv run ruff check

# 린트 자동 수정
uv run ruff check --fix

# 타입 검사
uv run ty check
```

## 테스트

### 실행

```bash
# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov

# 상세 출력
uv run pytest -v

# 특정 파일
uv run pytest tests/services/test_labeling_service.py -v

# 특정 테스트
uv run pytest tests/services/test_labeling_service.py::TestAddElement -v
```

### 테스트 구조

```text
tests/
├── conftest.py                     # 공통 픽스처
├── api/                            # API 라우터 테스트
│   ├── test_app.py                 # 앱 설정
│   ├── test_health.py              # 헬스체크
│   ├── test_projects.py            # 프로젝트 CRUD
│   ├── test_documents.py           # 문서 업로드/조회
│   ├── test_pages.py               # 페이지 레이블링
│   ├── test_users.py               # 사용자 관리
│   ├── test_export.py              # 데이터 내보내기
│   └── test_settings.py            # 설정 검증
└── services/                       # 서비스 레이어 테스트
    ├── test_document_service.py    # PDF 업로드/변환
    ├── test_labeling_service.py    # 어노테이션 관리
    └── test_export_service.py      # 내보내기 서비스
```

### 테스트 패턴

API 테스트는 `FastAPI TestClient`를 사용하며, 서비스/리포지토리 호출을 mock합니다:

```python
class TestPageEndpoints:
    def test_get_page(self, client: TestClient, sample_page_record):
        with patch(
            'saegim.services.labeling_service.get_page_data',
            new_callable=AsyncMock,
            return_value=sample_page_record,
        ):
            response = client.get(f'/api/v1/pages/{page_id}')

        assert response.status_code == 200
```

서비스 테스트는 리포지토리를 mock합니다:

```python
class TestSaveAnnotation:
    @pytest.mark.asyncio
    async def test_saves_annotation(self, mock_pool, page_id, document_id):
        record = _make_page_record(page_id, document_id, annotation_data={...})

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_annotation = AsyncMock(return_value=record)
            result = await labeling_service.save_annotation(mock_pool, page_id, {})

        assert result['annotation_data'] == {...}
```

### 주요 픽스처

`tests/conftest.py`에 정의된 공통 픽스처:

| 픽스처 | 설명 |
| -------- | ------ |
| `test_settings` | 테스트용 Settings (debug=True) |
| `mock_pool` | asyncpg Pool 모의 객체 |
| `app` | FastAPI 앱 (DB mock 적용) |
| `client` | TestClient |
| `sample_project_record` | 프로젝트 레코드 예시 |
| `sample_document_record` | 문서 레코드 예시 |
| `sample_page_record` | 페이지 레코드 예시 (어노테이션 포함) |
| `sample_user_record` | 사용자 레코드 예시 |

## 새 기능 추가 가이드

### 새 API 엔드포인트 추가

1. **스키마 정의** - `src/saegim/schemas/`에 Pydantic 모델 추가
2. **리포지토리 작성** - `src/saegim/repositories/`에 raw SQL 함수 추가
3. **서비스 작성** - `src/saegim/services/`에 비즈니스 로직 추가
4. **라우터 작성** - `src/saegim/api/routes/`에 엔드포인트 추가
5. **라우터 등록** - `src/saegim/app.py`에 `include_router` 추가
6. **테스트 작성** - `tests/api/`와 `tests/services/`에 테스트 추가

### 새 마이그레이션 추가

1. `migrations/` 디렉토리에 순번 파일 생성 (예: `002_add_labels.sql`)
2. DDL 작성 (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE` 등)
3. `psql -f migrations/002_add_labels.sql`로 실행

## 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `API_HOST` | `0.0.0.0` | API 바인드 호스트 |
| `API_PORT` | `5000` | API 포트 |
| `DEBUG` | `false` | 디버그 모드 (docs/redoc 활성화) |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `DATABASE_URL` | `postgresql://labeling:labeling@localhost:5432/labeling` | DB 연결 URL |
| `DB_POOL_MIN_SIZE` | `2` | 최소 커넥션 수 |
| `DB_POOL_MAX_SIZE` | `10` | 최대 커넥션 수 |
| `STORAGE_PATH` | `./storage` | 파일 저장 경로 |
| `MAX_WORKERS` | `1` | 워커 수 |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173"]` | 허용 CORS 오리진 |

환경 변수는 `.env` 파일이나 시스템 환경 변수로 설정할 수 있습니다.
`pydantic-settings`가 자동으로 로드합니다.

## 문서 빌드

```bash
# 로컬 서버 (라이브 리로드)
uv run mkdocs serve

# 정적 빌드
uv run mkdocs build
```

빌드된 문서는 `site/` 디렉토리에 생성됩니다.
