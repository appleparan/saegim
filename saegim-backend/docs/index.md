# saegim

Human-in-the-loop labeling platform for Korean document benchmarks

saegim은 한국어 문서 VLM(Vision-Language Model) 벤치마크를 위한 레이블링 플랫폼 백엔드입니다.
[OmniDocBench](https://github.com/opendatalab/OmniDocBench) 포맷을 기반으로
문서의 레이아웃, 텍스트, 수식, 표 등을 어노테이션하고 관리합니다.

## 주요 기능

- **PDF 업로드 및 변환** - PDF를 업로드하면 페이지별 이미지로 자동 변환
- **텍스트/이미지 자동 추출** - PyMuPDF로 텍스트 블록·이미지 위치를 추출, 수락 시 어노테이션에 반영
- **OmniDocBench 어노테이션** - 15가지 블록 레벨 + 4가지 스팬 레벨 카테고리 지원
- **페이지별 레이블링** - 페이지 단위로 어노테이션 데이터 편집 및 저장
- **벤치마크 데이터 내보내기** - OmniDocBench JSON 포맷으로 프로젝트 전체 내보내기
- **사용자 관리** - admin, annotator, reviewer 역할 기반 사용자 관리

## 기술 스택

| 구분 | 기술 |
| ------ | ------ |
| Framework | FastAPI |
| Database | PostgreSQL + asyncpg (raw SQL) |
| PDF 변환 | PyMuPDF (fitz) |
| 스키마 검증 | Pydantic v2 |
| 설정 관리 | pydantic-settings |
| 패키지 관리 | uv |

## 프로젝트 구조

```text
src/saegim/
├── app.py                  # FastAPI 앱 팩토리
├── api/
│   ├── settings.py         # 환경 설정 (Pydantic Settings)
│   └── routes/             # API 라우터
│       ├── health.py       # 헬스체크
│       ├── projects.py     # 프로젝트 CRUD
│       ├── documents.py    # 문서 업로드/조회
│       ├── pages.py        # 페이지 레이블링
│       ├── users.py        # 사용자 관리
│       └── export.py       # 데이터 내보내기
├── core/
│   └── database.py         # asyncpg 커넥션 풀 관리
├── repositories/           # Raw SQL 데이터 접근 레이어
│   ├── project_repo.py
│   ├── document_repo.py
│   ├── page_repo.py
│   └── user_repo.py
├── schemas/                # Pydantic 스키마
│   ├── annotation.py       # OmniDocBench 어노테이션 구조
│   ├── project.py
│   ├── document.py
│   ├── page.py
│   ├── user.py
│   └── export.py
├── services/               # 비즈니스 로직
│   ├── document_service.py    # PDF 업로드/변환/추출
│   ├── extraction_service.py  # PyMuPDF 텍스트/이미지 블록 추출
│   ├── labeling_service.py    # 어노테이션 관리, 자동 추출 수락
│   └── export_service.py      # OmniDocBench JSON 내보내기
└── migrations/
    └── 001_init.sql        # 초기 DDL
```

## 빠른 시작

```bash
# 의존성 설치
uv sync --group dev --group docs

# 서버 실행
uv run uvicorn saegim.app:app --reload

# 테스트 실행
uv run pytest --cov
```

자세한 내용은 [시작하기](guide/getting-started.md) 문서를 참조하세요.
