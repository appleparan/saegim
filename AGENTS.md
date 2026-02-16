# 한국어 문서 VLM 벤치마크 레이블링 웹앱 — 플래닝 가이드

---

## 1. 프로젝트 개요 및 평가

### 1.1 목표 정의

PDF 등 한국어 문서 데이터셋을 업로드하면 OmniDocBench 포맷의 3가지 메타데이터(Dataset Format, Evaluation Categories, Attribute Labels)를 자동 추출하고, 사람이 이를 검수·레이블링하여 최종 벤치마크 데이터셋을 생산하는 웹앱을 구축한다.

### 1.1.1 상위 비전: 논문 리뷰 에이전트에서 VLM 벤치마크 플랫폼으로

본 프로젝트의 출발점은 **논문 리뷰 에이전트**다. 논문의 Key Figure를 추출하고, OCR 품질을 검증하며, 핵심 아이디어를 구조화하는 것이 원래 목표였다. 이 과정에서 Key Figure 추출과 OCR이 핵심 병목임을 확인했고, 이를 체계적으로 해결하기 위해 에이전트 기반 레이블링 프레임워크를 구상했다.

이후 VLM 벤치마크 데이터셋의 부족(특히 한국어)을 인식하고, KO-VLM-Benchmark를 참조하여 레이블링 프레임워크를 범용 VLM 벤치마크 구축 플랫폼으로 확장하기로 결정했다.

**궁극적 목표는 3가지 평가 태스크를 모두 커버하는 프레임워크**:

| 태스크 | 평가 대상 | saegim에서의 역할 |
| ------ | --------- | ----------------- |
| **KO-VQA** | 다양한 도메인의 한국어 문서 이해 능력 + 문서 기반 답변 추론 능력 | Q&A 쌍 + 근거 영역 레이블링 |
| **KO-VDC** | 한국어 시각화 도식 자료 이해 능력 + 도식 기반 설명문 생성/이해 능력 | Element-level 구조 레이블링 (현재 MVP) |
| **KO-OCRAG** | 복잡한 구조의 한국어 문서 OCR 능력 + Visual Context parsing 능력 | Context-Query-Answer 트리플렛 레이블링 |

이를 위해 **두 가지 어노테이션 패러다임**이 공존해야 한다:

```text
패러다임 1: Element-centric (Phase 1~3, KO-VDC 중심)
  Page → [Element(bbox, category, text, attribute)]

패러다임 2: Task-centric (Phase 4b~4c, KO-VQA/OCRAG 중심)
  Page → [Task(question, answer, evidence_regions)]
```

### 1.1.2 논문 리뷰 에이전트를 위한 문서 분석 메타데이터

논문 리뷰 에이전트의 핵심 기능인 **의미 수준 분석**(핵심 아이디어, 주요 그림 해석 등)은 구조적 레이블링과는 다른 계층에 속한다. 이를 **document-level 메타데이터**로 분리하여 `documents.analysis_data` JSONB 컬럼에 저장한다.

외부 AI(VLM/LLM)가 자동 추출하고, 사람이 검수하는 패턴은 Phase 2의 auto-extraction과 동일하다.

**분석 섹션 네비게이션 (sticky)**:

| 섹션 | 설명 | 데이터 소스 |
| ---- | ---- | ----------- |
| **Overview** | 논문 개요 (제목, 저자, 초록, 핵심 기여) | AI 자동 추출 + 사람 검수 |
| **Core Idea** | 문제 정의, 접근 방법, 핵심 기여 | AI 자동 추출 + 사람 검수 |
| **Key Figures** | 주요 그림/도표와 그 중요성 설명 | AI 자동 선정 + page/anno_id로 element 참조 |
| **Limitations** | 명시적/암시적 한계점, 향후 연구 방향 | AI 자동 추출 + 사람 검수 |

`documents.analysis_data` JSONB 구조:

| 키 | 내용 |
| -- | ---- |
| `overview` | title, authors, venue, summary, tags |
| `core_idea` | problem, approach, novelty, key_equations (page+anno_id 참조) |
| `key_figures` | page, anno_id, label, why_important, rank |
| `limitations` | stated, implicit, future_work |
| `_meta` | model, extracted_at, reviewed, reviewed_by |

**Key Figures가 element-level과 document-level을 연결하는 브릿지 역할**:
`analysis_data.key_figures[].{page, anno_id}` → `annotation_data.layout_dets[].{anno_id}` 참조.

### 1.2 두 레포지토리 분석

#### KO-VLM-Benchmark (Marker-Inc-Korea)

- 한국어 실제 문서 기반 VLM 벤치마크로, 3가지 평가 태스크를 정의한다.
  - **KO-VDC** (Visual Document Conversion): 문서 이미지 → 텍스트 변환 정확도. Edit Distance, BLEU, METEOR 등으로 평가.
  - **KO-VQA** (Visual Question Answering): 문서 이미지에 대한 질의응답 정확도.
  - **KO-OCRAG** (OCR + RAG): OCR 결과 기반 검색-생성 파이프라인 평가.
- 핵심 시사점: 한국어 문서에 특화된 평가 카테고리(문서 유형, 언어, 레이아웃)와 태스크별 ground truth가 필요하다는 것을 보여줌.

#### OmniDocBench (CVPR 2025)

- 1,355 PDF 페이지, 9종 문서 유형, 4종 레이아웃, 3종 언어를 포괄하는 문서 파싱 벤치마크.
- 3가지 핵심 출력 포맷이 본 프로젝트의 표준이 된다:
  1. **Dataset Format**: JSON 구조 (layout_dets, page_info, extra)
  2. **Evaluation Categories**: 15종 Block-level + 4종 Span-level 카테고리
  3. **Attribute Labels**: 페이지/테이블/텍스트/수식 속성 라벨

### 1.3 접근 방식 평가

이 프로젝트의 핵심 가치는 "자동 추출 + 사람 검증"의 하이브리드 파이프라인에 있다. 순수 수동 레이블링은 비용이 너무 크고, 순수 자동 추출은 품질이 보장되지 않기 때문에, PDF에서 가능한 메타데이터를 자동으로 뽑고 사람이 검수/보정하는 구조가 현실적이다.

다만 주의할 점이 있다:

- PDF에서 레이아웃 요소를 자동 검출하는 단계의 품질이 전체 파이프라인의 병목이 된다. 초기 버전에서는 기존 도구(MinerU, PP-Structure 등)를 활용하되, 자체 모델을 학습할 로드맵도 고려해야 한다.
- OmniDocBench의 Attribute Labels는 상당히 세분화되어 있어, 한국어 문서에 맞게 일부 커스터마이징(예: 한글 서체 분류, 한국 문서 유형 세분화)이 필요할 수 있다.
- KO-VLM-Benchmark의 평가 태스크(VDC, VQA, OCRAG)를 모두 커버하려면 레이블링 범위가 넓어지므로, Phase를 나누어 점진적으로 확장하는 것을 권장한다.

---

## 2. 출력 데이터 스키마 (OmniDocBench 기반)

레이블링 결과물은 아래 3가지 계층으로 구성된 JSON을 최종 출력한다.

### 2.1 Dataset Format (JSON 구조)

```text
페이지 단위 JSON 배열. 각 페이지는:
├── layout_dets[]          # 페이지 내 요소 리스트
│   ├── category_type      # Evaluation Category (아래 2.2 참조)
│   ├── poly[8]            # 4꼭짓점 좌표 (x1,y1,...,x4,y4)
│   ├── ignore             # 평가 시 무시 여부
│   ├── order              # 읽기 순서
│   ├── anno_id            # 고유 ID
│   ├── text               # OCR 텍스트 (선택)
│   ├── latex              # LaTeX (수식/테이블, 선택)
│   ├── html               # HTML (테이블, 선택)
│   ├── attribute{}        # Attribute Labels (아래 2.3 참조)
│   ├── line_with_spans[]  # Span-level 하위 요소
│   └── merge_list[]       # 병합 관계 요소
├── page_info{}
│   ├── page_no, height, width, image_path
│   └── page_attribute{}   # 페이지 속성 라벨
└── extra{}
    └── relation[]         # 요소 간 관계 (캡션-본체 등)
```

### 2.2 Evaluation Categories

#### Block-level (15종)

| 카테고리 | 설명 | 한국어 문서 참고 |
| --------- | ------ | ---------------- |
| title | 제목 | 논문 제목, 장/절 제목 |
| text_block | 본문 텍스트 단락 | 일반 텍스트 |
| figure | 그림/이미지 | 도표, 사진 |
| figure_caption | 그림 설명 | "그림 1. …" |
| figure_footnote | 그림 주석 | 그림 아래 부가 설명 |
| table | 테이블 본체 | 표 |
| table_caption | 테이블 설명 | "표 1. …" |
| table_footnote | 테이블 주석 | 표 아래 부가 설명 |
| equation_isolated | 별행 수식 | 독립 수식 |
| equation_caption | 수식 번호 | "(1)", "(2.3)" 등 |
| header | 머리글 | 페이지 상단 |
| footer | 바닥글 | 페이지 하단 |
| page_number | 페이지 번호 | |
| page_footnote | 페이지 각주 | 본문 하단 주석 |
| abandon | 무시 대상 | 광고, 워터마크 텍스트 등 |
| code_txt | 코드 블록 | 프로그래밍 코드 |
| code_txt_caption | 코드 설명 | |
| reference | 참고문헌 | 논문 말미 참조 리스트 |

#### Span-level (4종)

| 카테고리 | 설명 |
| --------- | ------ |
| text_span | 텍스트 라인 단위 |
| equation_ignore | 무시할 수식 |
| equation_inline | 인라인 수식 |
| footnote_mark | 위/아래첨자 마크 |

### 2.3 Attribute Labels

#### 페이지 속성 (Page-level)

| 속성 | 값 | 한국어 확장 제안 |
| ------ | ----- | ----------------- |
| data_source | academic_literature, PPT2PDF, book, colorful_textbook, exam_paper, note, magazine, research_report, newspaper | + `government_doc` (공문서), `financial_report_kr` (한국 재무보고서) |
| language | en, simplified_chinese, en_ch_mixed | → `ko`, `en`, `ko_en_mixed`, `ko_ch_mixed` 로 변경 |
| layout | single_column, double_column, three_column, 1andmore_column, other_layout | 동일 사용 |
| watermark | true / false | 동일 |
| fuzzy_scan | true / false | 동일 |
| colorful_background | true / false | 동일 |

#### 테이블 속성 (Block-level: Table)

| 속성 | 값 |
| ------ | ----- |
| table_layout | vertical / horizontal |
| with_span | True / False (병합 셀 유무) |
| line | full_line / less_line / fewer_line / wireless_line |
| language | table_ko / table_en / table_ko_en_mixed |
| include_equation | True / False |
| include_background | True / False |
| table_vertical | True / False (90°/270° 회전) |

#### 텍스트 속성 (Block-level: Text)

| 속성 | 값 |
| ------ | ----- |
| text_language | text_ko / text_en / text_ko_en_mixed |
| text_background | white / single_colored / multi_colored |
| text_rotate | normal / rotate90 / rotate180 / rotate270 / horizontal |

#### 수식 속성 (Block-level: Formula)

| 속성 | 값 |
| ------ | ----- |
| formula_type | print / handwriting |
| equation_language | equation_ko / equation_en |

---

## 3. 시스템 아키텍처

### 3.1 전체 파이프라인

```text
[PDF 업로드]
     │
     ▼
[Phase A: 자동 추출 파이프라인]
     │  ├── PDF → 이미지 변환 (페이지별 렌더링)
     │  ├── 레이아웃 검출 (Block/Span 카테고리 자동 분류)
     │  ├── OCR 텍스트 추출
     │  ├── 테이블/수식 인식
     │  ├── 읽기 순서 추정
     │  └── 페이지 속성 자동 분류 (문서 유형, 언어, 레이아웃 등)
     │
     ▼
[Phase B: 사람 레이블링 웹앱]
     │  ├── (1) Bounding Box 검수/수정
     │  ├── (2) Category 검수/수정
     │  ├── (3) Attribute Label 부여/수정
     │  ├── (4) OCR/LaTeX/HTML 텍스트 검수
     │  ├── (5) 읽기 순서 검수
     │  └── (6) 요소 간 관계(relation) 라벨링
     │
     ▼
[Phase C: QA & 내보내기]
     │  ├── 교차 검증 (Inter-Annotator Agreement)
     │  ├── 자동 검증 규칙 (필수 필드, 좌표 유효성 등)
     │  └── OmniDocBench JSON 내보내기
     │
     ▼
[최종 벤치마크 데이터셋]
```

### 3.2 기술 스택

| 계층 | 기술 | 이유 |
| ------ | ------ | ------ |
| **프론트엔드** | Svelte 5 + SvelteKit + TypeScript | Svelte 5의 runes($state, $derived)로 bbox/annotation 상태 관리가 간결. Canvas 위 bbox 인터랙션은 Konva.js 또는 Fabric.js 활용 |
| **백엔드** | FastAPI (Python) | 자동 추출 파이프라인(PyTorch 모델)과 자연스러운 통합. 프론트엔드와는 HTTP/JSON API로만 통신 |
| **DB 드라이버** | asyncpg (raw SQL) | 비동기 PostgreSQL 드라이버. ORM 없이 raw SQL + Repository 패턴으로 JSONB 직접 제어 |
| **DB** | PostgreSQL 15+ | 2~5명 동시 접속 + JSONB 지원 (아래 3.3 상세 설명) |
| **파일 저장** | 로컬 파일시스템 (→ 추후 MinIO/S3) | PDF 원본, 페이지 이미지 등 바이너리 파일 |
| **자동 추출** | MinerU (pipeline backend) | 15+ 카테고리 레이아웃 검출 + OCR + 수식 LaTeX + 테이블 HTML (구현 완료) |
| **PDF 추출 (폴백)** | PyMuPDF | CI/테스트용 동기 추출 폴백 (text_block + figure만 지원) |
| **태스크 큐** | Celery + Redis (구현 완료) | MinerU 비동기 추출, GPU 워커 지원 |
| **배포** | Docker Compose | 로컬/서버 동일 환경. 배포 환경 미정이어도 유연하게 대응 |

#### 프론트엔드 ↔ 백엔드 연결 구조

Svelte 5와 FastAPI는 완전히 독립된 프로세스로, HTTP/JSON으로만 통신한다.
Svelte가 Python을 import하지 않으며, 서로 존재를 알 필요가 없다.

```text
Svelte 5 (:5173)             FastAPI (:5000)             PostgreSQL (:5432)
┌────────────────────┐       ┌────────────────────┐      ┌──────────────┐
│ UI + Canvas        │       │ Routes / Services  │      │              │
│ $state annotation  │◄JSON─►│ PDF extraction     │◄SQL─►│ JSONB tables │
│ Konva.js + DOM     │       │ Repository pattern │      │              │
└────────────────────┘       └────────────────────┘      └──────────────┘
```

개발 시 터미널 두 개를 별도로 실행한다:

- 백엔드: `cd saegim-backend && uv run saegim --port 5000`
- 프론트엔드: `cd saegim-frontend && bun run dev` (포트 5173)

API 클라이언트 구현: [saegim-frontend/src/lib/api/](saegim-frontend/src/lib/api/)
CORS 설정은 환경변수 `CORS_ORIGINS`로 관리한다.

### 3.3 데이터베이스 전략

#### 왜 PostgreSQL인가

이 프로젝트는 "웹앱 + 2~5명 동시 접속"이므로 SQLite는 적합하지 않다.

| 요구사항 | SQLite | PostgreSQL |
| --------- | -------- | ------------ |
| 다수 사용자 동시 쓰기 | 단일 Writer lock → 충돌 | 동시 쓰기 안전 |
| JSON 내부 필드 검색/인덱싱 | TEXT 저장, 느린 검색 | JSONB 인덱스, 빠른 쿼리 |
| JSON 부분 업데이트 | 통째로 교체 | jsonb_set()으로 부분 수정 |
| 설치 복잡도 | 파일 하나 | Docker Compose로 1줄 실행 |

레이블링 작업은 자동 저장이 수시로 발생하므로 동시 쓰기 안전성이 필수적이다.

#### 개발 환경 전략: PostgreSQL + asyncpg (raw SQL)

ORM 없이 asyncpg + raw SQL + Repository 패턴을 채택했다.
JSONB 부분 업데이트(`jsonb_set`), 배열 조작, 조건부 UPDATE 등
PostgreSQL 고유 기능을 적극 활용하기 위해 ORM 추상화를 배제했다.

환경변수 템플릿: [.env.example](.env.example)

개발/배포 모두 PostgreSQL을 사용하며, Docker Compose로 로컬에서도 동일 환경을 구성한다.

#### Page 단위 JSONB 저장 전략

레이블링 데이터를 저장하는 방식에 두 가지 선택지가 있다:

- **전략 A (정규화)**: layout_elements, span_elements, relations 테이블을 별도로 둠
  → JOIN이 복잡하고, OmniDocBench JSON 변환 로직이 필요
- **전략 B (Page 단위 JSONB)**: 페이지 테이블에 annotation_data JSONB 컬럼 하나로 통째 저장
  → OmniDocBench JSON 구조를 그대로 넣고 꺼냄. Export = SELECT → 배열 조합 → 파일 쓰기

**전략 B를 채택한다.** 이유:

1. OmniDocBench JSON ↔ DB 간 변환 로직이 거의 없다 (넣고 꺼내면 그대로 Export 포맷)
2. 스키마 확장 시 마이그레이션이 단순하다 (JSON 필드 추가는 DB 마이그레이션 불필요)
3. PostgreSQL JSONB는 내부 필드 인덱싱이 가능하여 "table 카테고리만 찾기" 같은 쿼리도 지원
4. 수천 페이지, 페이지당 10~50KB 수준이면 전체 합쳐도 수십~수백 MB — PostgreSQL에 부담 없음

#### 데이터 저장 위치 분리

| 저장 대상 | 위치 | 이유 |
| ----------- | ------ | ------ |
| PDF 원본 | 파일시스템 `./storage/pdfs/` | 바이너리, 수정 안 함 |
| 페이지 이미지 | 파일시스템 `./storage/images/` | 용량 큼 (페이지당 1~5MB), 읽기만 함 |
| 레이블링 JSON | PostgreSQL JSONB (`pages.annotation_data`) | 동시 편집 안전, 쿼리/인덱싱 가능 |
| 자동 추출 원본 | PostgreSQL JSONB (`pages.auto_extracted_data`) | 비교/복원용 보관 |
| 문서 분석 메타데이터 | PostgreSQL JSONB (`documents.analysis_data`) | AI 추출 결과 + 사람 검수. Overview, Core Idea, Key Figures, Limitations |
| 프로젝트/문서/유저 메타 | PostgreSQL 일반 컬럼 | 관계형 데이터 |
| 작업 할당/진행 상태 | PostgreSQL 일반 컬럼 | 상태 관리, 쿼리 필요 |
| 최종 내보내기 파일 | 파일시스템 (생성 후 다운로드) | OmniDocBench JSON + 이미지 패키지 |

#### 코드 구조: Repository 패턴

DB 접근을 Repository 계층으로 감싸, SQL 변경 시 영향 범위를 최소화한다.
ORM 없이 asyncpg raw SQL을 사용하며, Repository가 SQL 쿼리를 캡슐화한다.
전체 디렉토리 구조는 Section 3.5 참조.

파일 저장소를 로컬 → S3로 바꿀 때도 repository/service 내부만 수정하면 된다.

### 3.4 Docker Compose 구성

설정 파일: [docker-compose.yml](docker-compose.yml)

| 서비스 | 이미지/빌드 | 포트 |
| ------ | ----------- | ---- |
| postgres | postgres:18.2-trixie | 5432 |
| backend | ./saegim-backend | 5000 |
| frontend | ./saegim-frontend | 80 (→ 5173) |
| redis | redis:7-alpine | 6379 |
| celery-worker | ./saegim-backend | - (Celery 워커) |

`docker compose up` 한 줄이면 로컬/서버 동일 환경.
E2E 테스트용 격리 환경: [e2e/docker-compose.e2e.yml](e2e/docker-compose.e2e.yml) (Section 3.8).

### 3.5 프로젝트 디렉토리 구조

```text
saegim/
├── .env.example                  # 환경변수 템플릿
├── .github/
│   ├── ISSUE_TEMPLATE/           # 버그 리포트, 기능 요청 템플릿
│   └── workflows/
│       ├── ci.yml                # 린트/테스트/빌드 CI
│       ├── claude.yml            # Claude Code 자동화
│       └── publish-release.yml   # 릴리즈 발행
├── .markdownlint-cli2.jsonc      # 마크다운 린트 설정 (line_length: 120)
├── .markdownlint.json
├── AGENTS.md                     # 플래닝 가이드 (이 문서)
├── CHANGELOG.md                  # git-cliff 자동 생성
├── README.md
├── cliff.toml                    # git-cliff 설정
├── docker-compose.yml            # 개발/배포용 Docker Compose
│
├── docs/                         # 루트 문서 (quickstart, 배포 가이드)
│   ├── guide/quickstart.md
│   └── dev/
│       ├── docker.md
│       └── kubernetes.md
│
├── e2e/                          # E2E 테스트 (Playwright + Docker Compose)
│   ├── docker-compose.e2e.yml    # E2E 전용 환경 (포트 2xxxx)
│   ├── package.json              # bun + @playwright/test
│   ├── playwright.config.ts
│   ├── fixtures/                 # 테스트용 PDF 등 고정 데이터
│   │   └── attention.pdf
│   ├── helpers/                  # 테스트 유틸리티
│   │   ├── api.ts                # 백엔드 API 호출 헬퍼
│   │   ├── pdf.ts                # 테스트 PDF 생성
│   │   └── timer.ts              # 대기/폴링 유틸
│   └── tests/
│       ├── health.spec.ts        # 헬스체크 (백엔드 + 프론트엔드)
│       ├── workflow.spec.ts      # 프로젝트→문서→레이블링 전체 플로우
│       ├── benchmark.spec.ts     # OmniDocBench Export 검증
│       ├── hybrid-labeling.spec.ts # 3-layer 하이브리드 뷰어 테스트
│       └── extraction.spec.ts    # PDF 텍스트/이미지 추출 + 수락 플로우
│
├── k8s/                          # Kubernetes 매니페스트
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-statefulset.yaml
│   ├── storage-pvc.yaml
│   ├── migration-job.yaml
│   ├── backend-deployment.yaml
│   └── frontend-deployment.yaml
│
├── scripts/
│   └── release.sh                # 릴리즈 스크립트
│
├── saegim-backend/               # FastAPI + asyncpg 백엔드
│   ├── Dockerfile
│   ├── Makefile
│   ├── pyproject.toml            # uv 패키지 관리
│   ├── mkdocs.yml                # MkDocs 문서 설정
│   ├── migrations/
│   │   ├── 001_init.sql          # 초기 DB 스키마
│   │   └── 002_extraction_status.sql  # extracting/extraction_failed 상태 추가
│   ├── docs/                     # 백엔드 문서 (MkDocs)
│   │   ├── index.md
│   │   ├── guide/                # API 문서, 시작하기, 개요
│   │   ├── design/               # 아키텍처, DB 설계
│   │   └── dev/                  # 개발 가이드
│   ├── src/saegim/
│   │   ├── app.py                # FastAPI 앱 팩토리 + lifespan
│   │   ├── cli.py                # CLI 엔트리포인트
│   │   ├── core/
│   │   │   └── database.py       # asyncpg 커넥션 풀
│   │   ├── api/
│   │   │   ├── settings.py       # Pydantic Settings (환경변수)
│   │   │   └── routes/
│   │   │       ├── health.py     # GET /api/v1/health
│   │   │       ├── projects.py   # 프로젝트 CRUD
│   │   │       ├── documents.py  # 문서 업로드/삭제
│   │   │       ├── pages.py      # 페이지 레이블링 + accept-extraction
│   │   │       ├── users.py      # 사용자 관리
│   │   │       └── export.py     # OmniDocBench JSON 내보내기
│   │   ├── repositories/         # DB 접근 (asyncpg raw SQL)
│   │   │   ├── page_repo.py      # JSONB CRUD, accept_auto_extracted()
│   │   │   ├── document_repo.py
│   │   │   ├── project_repo.py
│   │   │   └── user_repo.py
│   │   ├── services/
│   │   │   ├── document_service.py     # PDF 업로드/변환/추출 (pymupdf/mineru 분기)
│   │   │   ├── extraction_service.py   # PyMuPDF 텍스트/이미지 추출 (CI 폴백)
│   │   │   ├── mineru_extraction_service.py  # MinerU 추출 + OmniDocBench 변환
│   │   │   ├── labeling_service.py     # 어노테이션 CRUD, accept_auto_extraction()
│   │   │   └── export_service.py       # OmniDocBench JSON 내보내기
│   │   ├── tasks/                # Celery 비동기 태스크
│   │   │   ├── celery_app.py     # Celery 앱 설정 (Redis broker)
│   │   │   └── extraction_task.py # MinerU 추출 Celery 태스크
│   │   └── schemas/              # Pydantic 요청/응답 스키마
│   │       ├── annotation.py     # AnnotationData, LayoutElement
│   │       ├── page.py           # PageResponse, ElementCreate
│   │       ├── document.py
│   │       ├── project.py
│   │       ├── export.py
│   │       └── user.py
│   └── tests/
│       ├── conftest.py           # pytest 공통 fixture (asyncpg pool mock 등)
│       ├── api/                  # API 라우트 테스트
│       │   ├── test_health.py
│       │   ├── test_projects.py
│       │   ├── test_documents.py
│       │   ├── test_pages.py
│       │   ├── test_export.py
│       │   ├── test_users.py
│       │   ├── test_settings.py
│       │   └── test_app.py
│       ├── services/             # 서비스 유닛 테스트
│       │   ├── test_document_service.py
│       │   ├── test_extraction_service.py
│       │   ├── test_mineru_extraction_service.py  # MinerU 변환 테스트 (38개)
│       │   ├── test_export_service.py
│       │   └── test_labeling_service.py
│       └── tasks/                # Celery 태스크 테스트
│           └── test_extraction_task.py
│
├── saegim-frontend/              # Svelte 5 (Runes) SPA
│   ├── Dockerfile
│   ├── package.json              # bun 패키지 관리
│   ├── vite.config.ts
│   ├── svelte.config.js
│   ├── nginx.conf                # 프로덕션 nginx 설정
│   ├── docs/                     # 프론트엔드 문서
│   │   ├── guide/                # 컴포넌트 레퍼런스, 단축키
│   │   ├── design/               # 아키텍처, 스토어 설계
│   │   └── dev/                  # API 클라이언트 문서
│   ├── src/
│   │   ├── App.svelte            # 라우터 (hash-based SPA)
│   │   ├── main.ts
│   │   ├── app.css               # Tailwind CSS
│   │   ├── lib/
│   │   │   ├── api/              # FastAPI 호출 함수
│   │   │   │   ├── client.ts     # fetch 래퍼 (BASE_URL 등)
│   │   │   │   ├── pages.ts      # acceptExtraction() 포함
│   │   │   │   ├── documents.ts
│   │   │   │   ├── projects.ts
│   │   │   │   ├── elements.ts
│   │   │   │   ├── relations.ts
│   │   │   │   └── types.ts      # API 응답 타입
│   │   │   ├── components/
│   │   │   │   ├── canvas/
│   │   │   │   │   ├── HybridViewer.svelte   # 3-layer 통합 뷰어
│   │   │   │   │   ├── ImageViewer.svelte    # Konva.js Stage + 줌/패닝
│   │   │   │   │   ├── BboxLayer.svelte      # Konva bbox 렌더링/편집
│   │   │   │   │   ├── BboxDrawTool.svelte   # 새 bbox 그리기
│   │   │   │   │   └── TextOverlay.svelte    # DOM 텍스트 투명 오버레이
│   │   │   │   ├── common/
│   │   │   │   │   ├── Button.svelte
│   │   │   │   │   ├── Select.svelte
│   │   │   │   │   ├── Toggle.svelte
│   │   │   │   │   └── LoadingSpinner.svelte
│   │   │   │   ├── layout/
│   │   │   │   │   ├── Header.svelte
│   │   │   │   │   └── Sidebar.svelte
│   │   │   │   └── panels/
│   │   │   │       ├── ElementList.svelte
│   │   │   │       ├── CategorySelect.svelte
│   │   │   │       ├── AttributePanel.svelte
│   │   │   │       ├── PageAttributePanel.svelte
│   │   │   │       ├── TextEditor.svelte
│   │   │   │       └── ExtractionPreview.svelte  # 자동 추출 수락 UI
│   │   │   ├── stores/
│   │   │   │   ├── annotation.svelte.ts  # $state 기반 어노테이션 상태
│   │   │   │   ├── canvas.svelte.ts      # 캔버스 상태 (줌, 모드)
│   │   │   │   └── ui.svelte.ts          # UI 상태 (사이드바, 알림)
│   │   │   ├── types/
│   │   │   │   ├── omnidocbench.ts       # OmniDocBench JSON 타입
│   │   │   │   ├── categories.ts         # 블록 카테고리 상수
│   │   │   │   ├── element-groups.ts     # isTextBlock(), isImageBlock()
│   │   │   │   └── canvas.ts
│   │   │   └── utils/
│   │   │       ├── bbox.ts               # bbox 좌표 변환
│   │   │       ├── color.ts              # 카테고리별 색상
│   │   │       ├── interaction.ts        # 마우스/키보드 유틸
│   │   │       ├── text-layout.ts        # 텍스트 레이아웃 계산
│   │   │       └── validation.ts
│   │   └── pages/
│   │       ├── ProjectList.svelte        # 프로젝트 목록
│   │       ├── DocumentList.svelte       # 문서 목록 + PDF 업로드
│   │       └── LabelingPage.svelte       # 3-panel 레이블링 메인 화면
│   └── tests/
│       ├── setup.ts                      # Vitest 설정
│       └── lib/
│           ├── components/canvas/
│           │   └── TextOverlay.test.ts
│           ├── types/
│           │   └── element-groups.test.ts
│           └── utils/
│               ├── bbox.test.ts
│               ├── interaction.test.ts
│               └── text-layout.test.ts
│
└── storage/                      # 파일시스템 저장소 (Docker volume 마운트)
    ├── pdfs/                     # 원본 PDF
    └── images/                   # 페이지별 렌더링 이미지
```

### 3.6 문서 구조

프로젝트 문서는 3곳에 분산되어 있으며, 기능 추가/변경 시 모두 업데이트해야 한다:

| 위치 | 내용 | 대상 |
| ------ | ------ | ------ |
| `docs/` (루트) | 프로젝트 전체 quickstart, Docker/K8s 배포 가이드 | 사용자/운영 |
| `saegim-backend/docs/` | 백엔드 API 문서, 아키텍처, DB 설계 (MkDocs) | 백엔드 개발자 |
| `saegim-frontend/docs/` | 프론트엔드 아키텍처, 컴포넌트, API 클라이언트 | 프론트엔드 개발자 |
| `AGENTS.md` (루트) | 전체 플래닝 가이드, Phase 로드맵, 스키마 설계 | 기획/설계 |
| `README.md` (루트) | 프로젝트 소개, 기술 스택, 빠른 시작 | 신규 참여자 |

### 3.7 핵심 컴포넌트 설계

#### A. PDF Ingestion Service

- PDF를 페이지 단위로 고해상도 이미지(200 DPI 이상)로 변환
- 원본 PDF와 변환 이미지를 저장
- page_info (page_no, height, width, image_path) 자동 생성

#### B. Auto-Extraction Pipeline

- Layout Detection: 각 페이지에서 블록/스팬 요소의 bounding box + category_type 추출
- OCR Engine: 텍스트 블록의 text 필드 채우기
- Table Recognizer: table 요소의 html/latex 필드 생성
- Formula Recognizer: 수식 요소의 latex 필드 생성
- Attribute Classifier: 페이지/블록 속성 자동 분류
- Reading Order Estimator: order 필드 자동 부여
- 모든 추출 결과를 "초안 JSON"으로 저장 → 사람 검수 단계로 전달

#### C. Labeling Web Interface (핵심)

- 이미지 뷰어 + 오버레이 bbox 편집기
- 사이드 패널: 선택한 요소의 category, attribute, text/latex/html 편집
- 읽기 순서 드래그 & 드롭 편집
- Relation 연결 도구 (캡션 ↔ 본체 등)

#### D. Quality Assurance Module

- 자동 검증 규칙 (bbox가 이미지 범위 내인지, 필수 속성 누락 등)
- 교차 검증: 같은 페이지를 2명 이상이 독립 레이블링 → 불일치 리뷰
- 진행률 대시보드

#### E. Export Service

- OmniDocBench JSON 포맷으로 직렬화
- 이미지 파일과 함께 패키징
- 선택적으로 KO-VLM-Benchmark 평가 스크립트와 호환되는 형식으로도 내보내기

### 3.8 E2E 테스트

E2E 테스트는 Playwright + Docker Compose로 실행한다.
전용 Docker Compose(`e2e/docker-compose.e2e.yml`)가 격리된 환경을 구성한다.

#### 환경 구성

| 서비스 | 포트 | 설명 |
| ------ | ---- | ---- |
| PostgreSQL | 25432 | E2E 전용 DB (labeling_e2e 비밀번호) |
| Backend | 25000 | FastAPI (포트 5000 → 호스트 25000) |
| Frontend | 23000 | Nginx 정적 빌드 (포트 80 → 호스트 23000) |

#### 실행 방법

```bash
cd e2e

# 1. Docker 환경 시작
bun run docker:up
# = docker compose -f docker-compose.e2e.yml up -d

# 2. Playwright 브라우저 + 테스트 PDF 설치
bun run setup
# = bunx playwright install chromium && bunx tsx helpers/pdf.ts

# 3. 테스트 실행
bun run test              # 전체 테스트
bun run test:health       # 헬스체크만
bun run test:workflow     # 전체 워크플로우만

# 4. 실패 시 디버깅
bun run test:ui           # Playwright UI 모드
bun run report            # HTML 리포트 열기
bun run docker:logs       # Docker 로그 확인

# 5. 정리
bun run docker:down
# = docker compose -f docker-compose.e2e.yml down -v
```

#### 테스트 구조

| 파일 | 내용 |
| ---- | ---- |
| `health.spec.ts` | 백엔드 `/api/v1/health` + 프론트엔드 로드 확인 |
| `workflow.spec.ts` | 프로젝트 생성 → PDF 업로드 → 레이블링 → Export 전체 플로우 |
| `benchmark.spec.ts` | OmniDocBench Export JSON 스키마 검증 |
| `hybrid-labeling.spec.ts` | 3-layer 하이브리드 뷰어 (배경+Konva+TextOverlay) |
| `extraction.spec.ts` | PDF 텍스트/이미지 추출 → 수락 → 어노테이션 반영 |

#### 헬퍼 모듈

- `helpers/api.ts`: 백엔드 REST API 호출 (`createProject`, `uploadPdf`, `acceptExtraction` 등)
- `helpers/pdf.ts`: `fixtures/attention.pdf` 존재 확인/생성
- `helpers/timer.ts`: 폴링/대기 유틸리티

#### Playwright 설정

- 브라우저: Chromium (1920×1080)
- 타임아웃: 테스트 120초, expect 15초, action 15초
- 실패 시 스크린샷, 재시도 시 trace/video 수집
- 직렬 실행 (`fullyParallel: false`, `workers: 1`)

---

## 4. 레이블링 UI 워크플로우 상세

### 4.1 어노테이터 작업 흐름

```text
Step 1: 페이지 로드
  → 자동 추출 결과가 bbox로 오버레이된 이미지를 본다

Step 2: 페이지 속성 확인/수정
  → data_source, language, layout, watermark, fuzzy_scan, colorful_background
  → 드롭다운 선택 방식

Step 3: Block-level 요소 검수
  → 각 bbox를 클릭하면:
     (a) category_type 확인/변경 (드롭다운)
     (b) bounding box 위치/크기 조정 (드래그)
     (c) 해당 카테고리의 attribute labels 부여 (조건부 UI)
         - text_block이면 → text_language, text_background, text_rotate
         - table이면 → table_layout, with_span, line, language 등
         - equation이면 → formula_type, equation_language
     (d) text / latex / html 내용 검수/수정
     (e) ignore 여부 토글

Step 4: Span-level 요소 검수
  → Block 내부의 line_with_spans 편집
  → 필요 시 인라인 수식, 각주 마크 등 추가/삭제

Step 5: 읽기 순서(order) 설정
  → 번호 자동 부여 결과를 확인
  → 드래그로 순서 변경 또는 직접 숫자 입력

Step 6: 관계(Relation) 설정
  → figure ↔ figure_caption 연결
  → table ↔ table_caption / table_footnote 연결
  → 잘린 단락(truncated) 관계 설정

Step 7: 완료 & 제출
  → 자동 검증 통과 확인 후 제출
```

### 4.2 UI 핵심 기능 요구사항

| 기능 | 설명 | 우선순위 |
| ------ | ------ | --------- |
| 이미지 줌/패닝 | 고해상도 문서를 자유롭게 확대/축소 | P0 |
| Bbox 생성/편집/삭제 | 사각형 드로잉, 꼭짓점 드래그, 삭제 | P0 |
| Category 선택 | 드롭다운 또는 단축키 지정 | P0 |
| Attribute 패널 | 카테고리에 따라 동적으로 표시되는 속성 입력 | P0 |
| 텍스트 편집 패널 | text / latex / html 인라인 편집 | P0 |
| 읽기 순서 에디터 | 번호 표시 오버레이 + 순서 변경 | P1 |
| Relation 연결 | 두 요소를 선택하여 관계 라벨 부여 | P1 |
| 키보드 단축키 | 카테고리 빠른 전환, 다음/이전 요소 이동 | P1 |
| Undo/Redo | 모든 편집 작업의 되돌리기 | P1 |
| 자동 저장 | 주기적 자동 저장 (작업 유실 방지) | P1 |
| 미니맵 | 전체 페이지 축소 보기에서 현재 위치 표시 | P2 |
| 비교 뷰 | 원본 이미지 vs 레이블링 결과 나란히 보기 | P2 |

---

## 5. 자동 추출 파이프라인 상세

### 5.0 현재 구현: 이중 백엔드 추출 (구현 완료)

`EXTRACTION_BACKEND` 환경변수로 추출 백엔드를 선택한다:

#### 5.0.1 MinerU 백엔드 (기본값, `EXTRACTION_BACKEND=mineru`)

```text
PDF 업로드
  → PyMuPDF 페이지 렌더링 (2x scale PNG)
  → Celery 태스크 디스패치 (비동기)
     → MinerU pipeline 백엔드 실행
     → content_list.json 생성
     → content_list → OmniDocBench 변환
        ├── 15+ 카테고리 매핑 (title, text_block, figure, table, equation_isolated, ...)
        ├── bbox 0-1000 정규화 → 픽셀 좌표 변환
        ├── 수식 → latex 필드, 테이블 → html 필드
        └── 캡션/각주 → 별도 element 생성
     → psycopg (동기)로 각 페이지 auto_extracted_data 업데이트
     → document status: extracting → ready (또는 extraction_failed)
  → 프론트엔드에서 "수락" → annotation_data로 복사
```

#### 5.0.2 PyMuPDF 백엔드 (CI 폴백, `EXTRACTION_BACKEND=pymupdf`)

```text
PDF 업로드
  → PyMuPDF 페이지 렌더링 (2x scale PNG)
  → page.get_text("dict") → blocks 배열 (동기)
     ├── type=0 (텍스트) → category_type: "text_block", spans의 text 합침
     └── type=1 (이미지) → category_type: "figure"
  → page.get_images() + get_image_bbox() → 임베디드 이미지 추출
  → 좌표 스케일링: PyMuPDF 72 DPI × 2.0 = 이미지 픽셀 좌표
  → auto_extracted_data JSONB에 OmniDocBench 형식으로 저장
  → document status: processing → ready (즉시)
  → 프론트엔드에서 "수락" → annotation_data로 복사
```

구현 파일:

- `mineru_extraction_service.py`: MinerU 래핑 + OmniDocBench 변환
- `extraction_service.py`: PyMuPDF 폴백 (`extract_page_elements()`, `bbox_to_poly()`)
- `document_service.py`: 업로드 시 백엔드 분기 + Celery 디스패치
- `tasks/celery_app.py`: Celery 앱 설정 (Redis broker)
- `tasks/extraction_task.py`: MinerU 추출 Celery 태스크
- `page_repo.py`: `create()`, `accept_auto_extracted()`, `update_auto_extracted_data()`
- `labeling_service.py`: `accept_auto_extraction()`
- `ExtractionPreview.svelte`: 추출 진행중 표시 + 수락/무시 UI

### 5.1 후보 도구 비교

| 도구 | 특징 | 장점 | 단점 | 상태 |
| ------ | ------ | ------ | ------ | ------ |
| **MinerU** (OpenDataLab) | OmniDocBench 제작팀 도구 | OmniDocBench 포맷과 직접 호환, 15+ 카테고리 | 한국어 최적화 필요 | **구현 완료** |
| **PP-StructureV3** (PaddlePaddle) | 레이아웃+OCR+테이블 통합 | 높은 정확도 (OmniDocBench Overall 86.73) | 패들 의존성 | 미구현 |
| **DocLayout-YOLO** | 경량 레이아웃 검출 | 빠른 추론 속도 | 텍스트 인식 별도 필요 | 미구현 |
| **Marker** (VikParuchuri) | PDF → Markdown 변환 | 간단한 파이프라인 | Attribute 정보 없음 | 미구현 |

**현재**: MinerU pipeline 백엔드를 1차 파이프라인으로 사용. 한국어 OCR 부분은 별도 보강 필요(예: PaddleOCR 한국어 모델). 자동 추출은 "초안" 역할이므로 완벽할 필요 없이 사람 검수 부하를 줄이는 것이 목표.

### 5.2 자동 Attribute 분류 전략

| 속성 | 자동 분류 방법 | 예상 정확도 |
| ------ | -------------- | ----------- |
| data_source | 메타데이터 + 이미지 분류 모델 (ResNet 등) | 중~높 |
| language | 텍스트 언어 감지 (langdetect 등) | 높 |
| layout | 열 분석 알고리즘 (X좌표 클러스터링) | 높 |
| watermark | 이미지 분석 (투명 텍스트 감지) | 중 |
| fuzzy_scan | 이미지 선명도 측정 (Laplacian variance) | 높 |
| colorful_background | 이미지 색상 히스토그램 분석 | 높 |
| table 속성들 | 테이블 구조 분석으로 자동 추출 가능 | 중~높 |
| text 속성들 | OCR + 텍스트 분석 조합 | 중 |
| formula 속성들 | 수식 인식 결과 기반 | 중 |

---

## 6. 데이터 모델 (DB 스키마)

### 6.1 테이블 설계

Page 단위 JSONB 전략에 따라, 핵심 테이블은 5개로 단순하게 유지한다.

```text
projects
├── id              UUID, PK
├── name            VARCHAR
├── description     TEXT
├── project_type    VARCHAR          # ★ Phase 4a: 'element_annotation' | 'vqa' | 'ocrag' (기본값: 'element_annotation')
└── created_at      TIMESTAMP

documents
├── id              UUID, PK
├── project_id      FK → projects
├── filename        VARCHAR          # 원본 PDF 파일명
├── pdf_path        VARCHAR          # 파일시스템 경로 (예: storage/pdfs/xxx.pdf)
├── total_pages     INT
├── status          ENUM             # uploading / processing / extracting / ready / error / extraction_failed
├── analysis_data   JSONB            # ★ Phase 4a: 문서 분석 메타데이터 (Overview, Core Idea, Key Figures, Limitations)
└── created_at      TIMESTAMP

pages
├── id              UUID, PK
├── document_id     FK → documents
├── page_no         INT
├── width           INT              # 페이지 이미지 너비 (px)
├── height          INT              # 페이지 이미지 높이 (px)
├── image_path      VARCHAR          # 파일시스템 경로 (예: storage/images/xxx_p1.jpg)
│
├── annotation_data     JSONB        # ★ 핵심: OmniDocBench 구조 통째로 저장
├── auto_extracted_data JSONB        # 자동 추출 원본 (비교/복원용, 수정 안 함)
│
├── status          ENUM             # pending / in_progress / submitted / reviewed
├── assigned_to     FK → users       # 현재 작업자
├── locked_at       TIMESTAMP        # 배타적 잠금 시각 (동시 편집 방지)
└── updated_at      TIMESTAMP

users
├── id              UUID, PK
├── name            VARCHAR
├── email           VARCHAR, UNIQUE
├── role            ENUM             # admin / annotator / reviewer
└── created_at      TIMESTAMP

task_history
├── id              UUID, PK
├── page_id         FK → pages
├── user_id         FK → users
├── action          ENUM             # assigned / started / saved / submitted / approved / rejected
├── snapshot        JSONB            # 해당 시점의 annotation_data 스냅샷 (선택, Undo/이력용)
└── created_at      TIMESTAMP
```

### 6.2 annotation_data JSONB 구조

`pages.annotation_data` 컬럼 안에 들어가는 JSON이 곧 OmniDocBench의 한 페이지 데이터다.
Export 시 이 컬럼을 모아서 배열로 만들면 바로 최종 JSON이 된다.

```jsonc
{
  "layout_dets": [
    {
      "category_type": "text_block",  // 15종 Block-level + 4종 Span-level
      "poly": [x1,y1, x2,y2, x3,y3, x4,y4],  // 4꼭짓점 좌표
      "ignore": false, "order": 0, "anno_id": 0,
      "text": "...", "latex": "...", "html": "...",
      "attribute": { /* 카테고리별 속성 (Section 2.3) */ },
      "line_with_spans": [ /* Span-level 하위 요소 */ ]
    }
  ],
  "page_attribute": {
    "data_source": "academic_literature", "language": "ko",
    "layout": "double_column",
    "watermark": false, "fuzzy_scan": false, "colorful_background": false
  },
  "extra": { "relation": [{ "source_anno_id": 3, "target_anno_id": 4, "relation_type": "parent_son" }] }
}
```

타입 정의: [saegim-frontend/src/lib/types/omnidocbench.ts](saegim-frontend/src/lib/types/omnidocbench.ts)

### 6.3 PostgreSQL JSONB 활용

JSONB를 쓰면 정규화 없이도 내부 필드를 검색할 수 있다.
주요 연산: `@>` (containment), `->>`(텍스트 추출), `jsonb_set()` (부분 업데이트), GIN 인덱스.
쿼리 예시: [saegim-backend/docs/design/database.md](saegim-backend/docs/design/database.md)

### 6.4 Export 로직 (OmniDocBench JSON 생성)

구현: [saegim-backend/src/saegim/services/export_service.py](saegim-backend/src/saegim/services/export_service.py)

annotation_data를 OmniDocBench 구조로 저장했기 때문에,
Export는 사실상 **DB에서 꺼내서 page_info를 붙이는 것**이 전부다.

---

## 7. 개발 단계별 로드맵

### Phase 1: MVP ✅ 완료

**목표**: 단일 PDF를 업로드하고, 수동으로 OmniDocBench JSON을 생산할 수 있는 최소 기능.

#### 개발 환경 셋업

- PostgreSQL + asyncpg (raw SQL) + Repository 패턴
- Docker Compose로 개발/배포 동일 환경
- 파일 저장은 로컬 `./storage/` 디렉토리

#### 구현 완료 기능

- PDF → 이미지 변환 파이프라인 (PyMuPDF 2x 렌더링)
- 3-layer 하이브리드 레이블링 UI (배경 이미지 → Konva bbox → DOM TextOverlay)
- Category 선택 UI (드롭다운)
- Page/Block Attribute 입력 UI
- Text/LaTeX/HTML 편집 패널
- OmniDocBench JSON 내보내기 (annotation_data 조합)
- 프로젝트/문서/페이지 CRUD
- E2E 테스트 (Playwright + Docker Compose)

### Phase 2: 자동 추출 통합 (진행 중)

**목표**: 자동 추출 → 사람 검수 파이프라인 완성.

#### 구현 완료 (Stage 1~3, PR #4)

- **PyMuPDF 텍스트/이미지 자동 추출**: PDF 업로드 시 `page.get_text("dict")`로 텍스트 블록과 이미지 위치를 추출하여 `auto_extracted_data` JSONB에 저장
- **좌표 스케일링**: PyMuPDF 72 DPI × 2.0 = 이미지 픽셀 좌표로 변환
- **accept-extraction API**: 프론트에서 "수락" 버튼 → `auto_extracted_data`를 `annotation_data`로 복사
- **ExtractionPreview UI**: 자동 추출 결과 프리뷰 배너 + 수락/무시 버튼
- **TextOverlay 연동**: 수락 후 텍스트 블록의 text가 투명 오버레이로 렌더링 → 드래그 선택 가능

#### 구현 완료 (Stage 4~6, PR #5)

- **MinerU 구조 추출 통합**: MinerU pipeline 백엔드를 통한 15+ 카테고리 레이아웃 검출, 수식 LaTeX 변환, 테이블 HTML 변환
- **content_list → OmniDocBench 변환**: MinerU의 `content_list.json` 출력을 OmniDocBench 형식으로 변환 (좌표 0-1000 정규화 → 픽셀 좌표)
- **Celery + Redis 비동기 처리**: MinerU 추출을 Celery 태스크로 비동기 실행, Redis를 broker/backend로 사용
- **추출 백엔드 분기**: `EXTRACTION_BACKEND` 환경변수로 `pymupdf`(동기 폴백) / `mineru`(비동기) 선택
- **문서 상태 확장**: `extracting`, `extraction_failed` 상태 추가
- **프론트엔드 UI**: 추출 진행중 배지 + 자동 폴링, ExtractionPreview 컴포넌트에 MinerU 추출 중 표시
- **Docker Compose**: Redis 서비스 + Celery 워커 + GPU 워커(주석) 추가

#### 미구현 (후속 PR)

- PaddleOCR 연동 — PyMuPDF로 텍스트 추출 안 되는 영역에 OCR 수행
- 자동 Attribute 분류기 추가
- 읽기 순서 에디터
- Relation 연결 도구

### Phase 3: 협업 & QA (2~3주)

**목표**: 다수 어노테이터가 동시에 작업하고 품질을 관리할 수 있는 시스템.

#### 동시성 처리

- 페이지 단위 배타적 잠금 (pages.locked_at + assigned_to로 구현)
- 자동 저장 시 optimistic locking (updated_at 비교)
- task_history에 작업 이력 기록 (스냅샷 포함, 필요 시 복원)

#### 작업 관리

- 작업 할당 시스템 (어노테이터별 페이지 배분)
- 교차 검증 (같은 페이지 2인 이상 독립 레이블링)
- 리뷰어 워크플로우 (검수 → 승인/반려)
- 진행률 대시보드 (SQL 집계 쿼리로 실시간 통계)
- Inter-Annotator Agreement 자동 산출
- 자동 검증 규칙 강화

### Phase 4a: AI 분석 메타데이터 + Project Type 추상화 (2~3주)

**목표**: 문서 분석 메타데이터 자동 추출 + 다양한 어노테이션 모드를 위한 아키텍처 전환.

이 단계가 전체 로드맵의 **아키텍처 전환점**이다. Phase 1~3의 element-centric 패러다임을 유지하면서, Phase 4b~4c의 task-centric 패러다임을 수용할 수 있는 구조를 만든다.

#### AI 분석 메타데이터 (analysis_data)

- `documents` 테이블에 `analysis_data JSONB` 컬럼 추가
- VLM/LLM API 호출로 문서 분석 자동 추출 (Overview, Core Idea, Key Figures, Limitations)
- 자동 추출 결과를 `analysis_data`에 저장 → 사람이 검수/수정
- Phase 2의 auto-extraction 파이프라인과 동일한 Celery 태스크로 구현
- Key Figures는 `page` + `anno_id`로 기존 element 참조

#### Project Type 추상화

- `projects` 테이블에 `project_type VARCHAR` 컬럼 추가
  - `element_annotation` (기본값, Phase 1~3의 기존 동작)
  - `vqa` (Phase 4b)
  - `ocrag` (Phase 4c)
- `annotation_data`의 JSONB 스키마를 `project_type`별로 분기
- Pydantic 스키마에 `model_config = ConfigDict(extra='allow')` 적용하여 확장에 열린 구조
- Frontend LabelingPage의 3-panel 구조는 유지하되, panel 내용을 `project_type`에 따라 교체 가능하게 모듈화
- Export 서비스를 Strategy 패턴으로 설계 (OmniDocBench, VQA, OCRAG 각각의 Exporter)

#### 자동 추출 파이프라인 확장

```text
PDF 업로드
  → 이미지 변환 (PyMuPDF)
  → 레이아웃 자동 추출 (MinerU)          ← Phase 2에서 구현
  → AI 의미 추출 (VLM API 호출)          ← Phase 4a에서 추가
      ├── Overview 추출
      ├── Core Idea 추출
      ├── Key Figures 선정 + 해석
      └── Limitations 추출
  → auto_extracted_data / analysis_data에 저장
  → 사람이 검수/수정
```

### Phase 4b: KO-VDC Export + KO-VQA 레이블링 모듈 (2~3주)

**목표**: KO-VDC ground truth 내보내기 + VQA 질의응답 레이블링 기능.

#### KO-VDC

- VDC용 ground truth 내보내기 형식 (text 필드 기반)
- OmniDocBench 평가 스크립트와의 호환성 검증
- Edit Distance, BLEU, METEOR 평가 지표 연동

#### KO-VQA

- QA pair 에디터 UI (질문 작성 + 답변 작성)
- Evidence region 링크 (기존 bbox 재활용 — `page` + `anno_id` 참조)
- 질문 유형 분류 (factual, reasoning, comparison 등)
- VQA Export 포맷 (이미지 + Q&A JSON)

### Phase 4c: KO-OCRAG 레이블링 모듈 (2~3주)

**목표**: OCR + RAG 파이프라인 평가를 위한 레이블링 기능.

- Context chunk 정의 도구 (문서 영역 → 검색 단위 분할)
- Query-Context-Answer 트리플렛 에디터
- Retrieval relevance 라벨링 (query에 대해 어떤 chunk가 관련 있는지)
- OCRAG Export 포맷

### Phase 5: 논문 리뷰 에이전트 연동 (별도 시스템)

**목표**: saegim의 ground truth를 활용하는 논문 리뷰 에이전트.

saegim은 이 에이전트의 **데이터 공장** 역할을 한다.

- saegim의 analysis_data + annotation_data를 학습/평가 데이터로 활용
- VLM 모델 + RAG 파이프라인 구축
- Key Figure 추출 정확도 평가 (saegim ground truth 대비)
- OCR 품질 평가 (saegim text 필드 대비)
- 벤치마크 리더보드 뷰어 (선택)

---

## 8. 한국어 문서 특화 고려사항

### 8.1 OmniDocBench 포맷 커스터마이징

OmniDocBench는 영어/중국어 중심이므로, 한국어 문서에 맞게 다음을 확장한다:

- **language 필드**: `ko`, `en`, `ko_en_mixed` 추가.
- **data_source 확장**: `government_doc` (공문서), `legal_doc` (법률 문서), `medical_report` (의료 보고서) 등 한국 특화 문서 유형 추가 가능.
- **Evaluation Category 확장**: 한국어 문서에 자주 등장하는 요소(인감/도장, 한자 혼용 텍스트 등)를 추가 카테고리 또는 속성으로 반영 검토.
- 기본 스키마를 변경하지 않고 **확장(additive)** 방식으로 구현하여 OmniDocBench 호환성을 유지한다.

### 8.2 한국어 OCR 이슈

- 한글 자모 분리/조합 문제: OCR 결과에서 자모가 분리되는 경우 후처리 필요
- 한자 혼용 텍스트: text_language 속성에서 `text_ko_hanja_mixed` 추가 고려
- 세로 쓰기: 한국 전통 문서나 일부 신문에서 세로 쓰기 존재 → text_rotate 속성으로 대응

---

## 9. API 설계 개요

### 핵심 엔드포인트

구현 완료된 엔드포인트에 ✅ 표시.

```text
# 프로젝트 관리
POST   /api/v1/projects                      ✅ 프로젝트 생성
GET    /api/v1/projects                      ✅ 프로젝트 목록
GET    /api/v1/projects/{id}/documents       ✅ 프로젝트 문서 목록
DELETE /api/v1/projects/{id}                 ✅ 프로젝트 삭제

# 문서 업로드 & 처리
POST   /api/v1/projects/{id}/documents       ✅ PDF 업로드 (→ 변환 + 텍스트/이미지 추출)
DELETE /api/v1/documents/{id}                ✅ 문서 삭제

# 페이지 레이블링
GET    /api/v1/pages/{id}                    ✅ 페이지 데이터 + annotation + auto_extracted 로드
PUT    /api/v1/pages/{id}                    ✅ 어노테이션 저장
PUT    /api/v1/pages/{id}/attributes         ✅ 페이지 속성 저장

# 자동 추출 수락
POST   /api/v1/pages/{id}/accept-extraction  ✅ auto_extracted_data → annotation_data 복사

# 레이아웃 요소
POST   /api/v1/pages/{id}/elements           ✅ 새 요소 추가
DELETE /api/v1/pages/{id}/elements/{anno_id} ✅ 요소 삭제

# 내보내기
POST   /api/v1/projects/{id}/export          ✅ OmniDocBench JSON 생성 & 다운로드

# 미구현 (후속)
POST   /api/v1/pages/{id}/relations          관계 추가
DELETE /api/v1/relations/{id}                관계 삭제
GET    /api/v1/tasks                         내 할당 작업 목록
PUT    /api/v1/tasks/{id}/submit             작업 제출
PUT    /api/v1/tasks/{id}/review             리뷰 결과 (승인/반려)
```

---

## 10. 리스크 & 완화 전략

| 리스크 | 영향 | 완화 |
| -------- | ------ | ------ |
| 자동 추출 품질 부족으로 수동 작업량 증가 | 높 | 추출 도구 비교 평가 후 최적 선택; 점진적 개선 루프 |
| 고해상도 이미지 렌더링 성능 | 중 | 타일 기반 렌더링, 이미지 피라미드 활용 |
| 복잡한 레이블링 UI로 인한 어노테이터 학습 곡선 | 중 | 튜토리얼 모드, 단계별 가이드, 단축키 치트시트 |
| 동시 편집 충돌 | 중 | 페이지 단위 배타적 잠금 (locked_at + assigned_to) |
| JSONB 데이터 일관성 깨짐 | 중 | JSON Schema 검증을 저장 시 서버에서 수행; task_history 스냅샷으로 복원 |
| asyncpg raw SQL 마이그레이션 | 낮 | Repository 패턴으로 SQL 격리; 마이그레이션 파일(`migrations/`)로 스키마 관리 |
| 파일 저장소 유실 | 중 | Docker volume 마운트; 추후 S3/MinIO 전환 시 백업 자동화 |
| OmniDocBench 스키마 버전 변경 | 낮 | annotation_data에 schema_version 필드 관리; 마이그레이션 스크립트 준비 |

---

## 11. 성공 지표 (KPI)

| 지표 | 목표 |
| ------ | ------ |
| 페이지당 평균 레이블링 시간 | 자동추출 없이 30분 이내, 자동추출 시 10분 이내 |
| Inter-Annotator Agreement (Category) | Cohen's κ ≥ 0.85 |
| Inter-Annotator Agreement (Attribute) | Cohen's κ ≥ 0.80 |
| JSON 스키마 유효성 통과율 | 100% |
| OmniDocBench 평가 스크립트 호환성 | 수정 없이 실행 가능 |

---

## 부록: 참고 레포지토리 요약

| 항목 | KO-VLM-Benchmark | OmniDocBench |
| ------ | ------------------- | -------------- |
| 목적 | 한국어 VLM 성능 평가 | 문서 파싱 벤치마크 |
| 규모 | 한국어 문서 데이터셋 기반 | 1,355 PDF, 9문서유형 |
| 평가 태스크 | VDC, VQA, OCRAG | End-to-End, Layout, Table, Formula, OCR |
| 평가 지표 | Edit Dist, BLEU, METEOR | Edit Dist, BLEU, METEOR, TEDS, CDM, mAP |
| 데이터 형식 | 이미지 + JSON | JSON + 이미지/PDF |
| 본 프로젝트 역할 | 평가 태스크 정의 참조 | **출력 포맷 표준** |
