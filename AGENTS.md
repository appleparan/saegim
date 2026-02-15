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

```jsonc
// documents.analysis_data JSONB 구조
{
  "overview": {
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "venue": "NeurIPS 2017",
    "summary": "RNN/CNN 없이 attention만으로 sequence transduction 수행",
    "tags": ["transformer", "attention", "NLP"]
  },
  "core_idea": {
    "problem": "RNN의 순차 연산이 병렬화를 막고 long-range dependency 학습이 어려움",
    "approach": "Self-attention으로 모든 위치 간 직접 연결",
    "novelty": "순수 attention 기반 encoder-decoder로 RNN/CNN 완전 대체",
    "key_equations": [
      {"page": 3, "anno_id": 7, "description": "Scaled Dot-Product Attention"}
    ]
  },
  "key_figures": [
    {
      "page": 2,
      "anno_id": 3,
      "label": "Figure 1",
      "why_important": "Transformer 전체 아키텍처 구조도",
      "rank": 1
    }
  ],
  "limitations": {
    "stated": ["고정 길이 입력에 대한 일반화 미검증"],
    "implicit": ["메모리 O(n²) — 긴 시퀀스에 비효율"],
    "future_work": ["이미지, 오디오 등 다른 모달리티 확장"]
  },
  "_meta": {
    "model": "claude-sonnet-4-5-20250929",
    "extracted_at": "2026-02-15T10:00:00Z",
    "reviewed": false,
    "reviewed_by": null
  }
}
```

**Key Figures가 element-level과 document-level을 연결하는 브릿지 역할**:

```text
Document-level (analysis_data)          Page-level (annotation_data)
┌─────────────────────┐                ┌─────────────────────┐
│ key_figures: [       │    참조        │ layout_dets: [       │
│   { page: 2,        │───────────────▶│   { anno_id: 3,      │
│     anno_id: 3,     │                │     category: figure, │
│     why_important }  │                │     poly: [...],      │
│ ]                    │                │     text: "Fig 1..." }│
└─────────────────────┘                └─────────────────────┘
```

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
| **ORM** | SQLAlchemy | DB 종류에 독립적인 코드 작성. 개발 시 SQLite → 배포 시 PostgreSQL 전환 가능 |
| **DB** | PostgreSQL | 2~5명 동시 접속 + JSONB 지원 (아래 3.3 상세 설명) |
| **파일 저장** | 로컬 파일시스템 (→ 추후 MinIO/S3) | PDF 원본, 페이지 이미지 등 바이너리 파일 |
| **자동 추출** | MinerU / PP-StructureV3 / DocLayout-YOLO 중 택1 | 레이아웃 검출 + OCR 통합 파이프라인 |
| **태스크 큐** | Celery + Redis | PDF 변환, 자동 추출 등 비동기 무거운 작업 처리 |
| **배포** | Docker Compose | 로컬/서버 동일 환경. 배포 환경 미정이어도 유연하게 대응 |

#### 프론트엔드 ↔ 백엔드 연결 구조

Svelte 5와 FastAPI는 완전히 독립된 프로세스로, HTTP/JSON으로만 통신한다.
Svelte가 Python을 import하지 않으며, 서로 존재를 알 필요가 없다.

```text
Svelte 5 (포트 5173)              FastAPI (포트 8000)              PostgreSQL
┌──────────────────┐              ┌──────────────────┐            ┌──────────┐
│  UI, bbox 편집기  │   fetch()    │  비즈니스 로직,   │  SQLAlchemy │          │
│  $state로 상태관리 │ ◄──JSON───► │  PDF변환, 저장    │ ◄──SQL───► │  JSONB   │
│  Canvas 렌더링    │              │  자동 추출 파이프   │            │          │
└──────────────────┘              └──────────────────┘            └──────────┘
```

개발 시 터미널 두 개를 별도로 실행한다:

```bash
# 터미널 1: FastAPI 백엔드
cd backend && uvicorn main:app --port 8000 --reload

# 터미널 2: SvelteKit 프론트엔드
cd frontend && npm run dev    # → localhost:5173
```

Svelte 쪽에서 FastAPI를 호출하는 패턴:

```typescript
// frontend/src/lib/api/pages.ts
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function getPage(pageId: string) {
  const res = await fetch(`${API_BASE}/api/pages/${pageId}`);
  return res.json();
}

export async function savePage(pageId: string, annotationData: object) {
  await fetch(`${API_BASE}/api/pages/${pageId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ annotation_data: annotationData })
  });
}
```

```svelte
<!-- frontend/src/routes/label/[pageId]/+page.svelte -->
<script lang="ts">
  import { getPage, savePage } from '$lib/api/pages';

  let annotation = $state(null);
  let imageUrl = $state('');

  async function load(pageId: string) {
    const data = await getPage(pageId);
    annotation = data.annotation_data;    // OmniDocBench JSON 그대로
    imageUrl = data.image_url;
  }
</script>

<canvas> <!-- bbox 오버레이 렌더링 --> </canvas>
<button onclick={() => savePage(pageId, annotation)}>저장</button>
```

FastAPI 쪽은 프론트엔드가 Svelte든 React든 무관하게 동일한 JSON API를 제공한다.
CORS 설정에서 Svelte 개발 서버 주소만 허용하면 된다.

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # SvelteKit 기본 포트
    allow_methods=["*"],
    allow_headers=["*"],
)
```

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

#### 개발 환경 전략: SQLite → PostgreSQL 전환

SQLAlchemy ORM을 사용하면 개발 초기에는 SQLite로 빠르게 시작하고,
팀 작업 시점에 PostgreSQL로 전환할 수 있다. 코드 변경은 환경변수 1줄이다.

```python
# .env (개발)
DATABASE_URL=sqlite:///./labeling.db

# .env (배포)
DATABASE_URL=postgresql://user:pass@localhost:5432/labeling
```

단, JSONB 전용 기능(부분 업데이트, GIN 인덱스 등)은 PostgreSQL 전환 후에 추가한다.
개발 단계에서는 JSON을 TEXT로 저장해도 수천 페이지 규모에서 성능 문제가 없다.

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

DB 접근을 직접 하지 않고 Repository 계층으로 감싸, DB 변경 시 영향 범위를 최소화한다.

```text
backend/
├── models/           # SQLAlchemy ORM 모델 정의
│   ├── project.py
│   ├── document.py
│   ├── page.py
│   └── user.py
├── repositories/     # DB 접근 로직 캡슐화
│   ├── page_repo.py        # get_annotation(), save_annotation() 등
│   ├── document_repo.py
│   └── project_repo.py
├── services/         # 비즈니스 로직 (repository 호출)
│   ├── labeling_service.py
│   ├── export_service.py
│   └── extraction_service.py
├── api/              # FastAPI 라우터 (service 호출)
│   ├── pages.py
│   ├── documents.py
│   └── projects.py
└── core/
    ├── config.py     # DATABASE_URL 등 환경변수
    └── database.py   # SQLAlchemy 엔진/세션 설정
```

이 구조에서 DB를 SQLite → PostgreSQL로 바꿀 때 수정 파일은 `config.py`의 URL 1줄뿐이다.
나중에 파일 저장소를 로컬 → S3로 바꿀 때도 repository 내부만 수정하면 된다.

### 3.4 Docker Compose 구성

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: labeling
      POSTGRES_USER: labeling
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://labeling:${DB_PASSWORD}@postgres:5432/labeling
      STORAGE_PATH: /app/storage
      CORS_ORIGINS: http://localhost:5173   # SvelteKit
    volumes:
      - ./storage:/app/storage
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  frontend:
    build: ./frontend                       # SvelteKit
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend

  # Phase 2에서 추가
  # redis:
  #   image: redis:7
  # worker:
  #   build: ./backend
  #   command: celery -A worker worker

volumes:
  postgres_data:
```

`docker-compose up` 한 줄이면 로컬에서도, 서버에서도 동일하게 동작한다.
배포 환경이 정해지지 않은 현 시점에서 가장 유연한 구성이다.

### 3.5 프로젝트 디렉토리 구조

```text
ko-doc-labeling/
├── docker-compose.yml
├── .env                          # DATABASE_URL, DB_PASSWORD 등
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI 앱 진입점
│   ├── core/
│   │   ├── config.py             # 환경변수 로드 (DATABASE_URL 등)
│   │   └── database.py           # SQLAlchemy 엔진/세션
│   ├── models/                   # SQLAlchemy ORM 모델
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── page.py
│   │   └── user.py
│   ├── repositories/             # DB 접근 캡슐화
│   │   ├── page_repo.py
│   │   ├── document_repo.py
│   │   └── project_repo.py
│   ├── services/                 # 비즈니스 로직
│   │   ├── labeling_service.py
│   │   ├── export_service.py
│   │   └── extraction_service.py # Phase 2
│   ├── api/                      # FastAPI 라우터
│   │   ├── pages.py
│   │   ├── documents.py
│   │   └── projects.py
│   └── schemas/                  # Pydantic 요청/응답 스키마
│       ├── page.py
│       └── annotation.py         # OmniDocBench JSON 검증용
│
├── frontend/                             # SvelteKit + Svelte 5
│   ├── Dockerfile
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   └── src/
│       ├── lib/
│       │   ├── api/                      # FastAPI 호출 함수
│       │   │   ├── pages.ts
│       │   │   ├── documents.ts
│       │   │   └── projects.ts
│       │   ├── components/
│       │   │   ├── ImageViewer.svelte     # Canvas + bbox 오버레이 렌더링
│       │   │   ├── BboxEditor.svelte      # bbox 드래그/리사이즈
│       │   │   ├── AttributePanel.svelte  # 속성 라벨 편집 (카테고리별 조건부 UI)
│       │   │   ├── ElementList.svelte     # 요소 목록/선택
│       │   │   └── TextEditor.svelte      # text/latex/html 편집
│       │   ├── stores/
│       │   │   └── annotation.svelte.ts   # $state 기반 어노테이션 상태 관리
│       │   └── types/
│       │       └── omnidocbench.ts        # OmniDocBench JSON 타입 정의
│       └── routes/
│           ├── +page.svelte               # 프로젝트 목록
│           ├── projects/[id]/+page.svelte # 문서 목록
│           └── label/[pageId]/+page.svelte# 레이블링 메인 화면
│
└── storage/                      # 파일시스템 저장소 (Docker volume 마운트)
    ├── pdfs/                     # 원본 PDF
    └── images/                   # 페이지별 렌더링 이미지
```

### 3.6 핵심 컴포넌트 설계

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

### 5.1 후보 도구 비교

| 도구 | 특징 | 장점 | 단점 |
| ------ | ------ | ------ | ------ |
| **MinerU** (OpenDataLab) | OmniDocBench 제작팀 도구 | OmniDocBench 포맷과 직접 호환 | 한국어 최적화 필요 |
| **PP-StructureV3** (PaddlePaddle) | 레이아웃+OCR+테이블 통합 | 높은 정확도 (OmniDocBench Overall 86.73) | 패들 의존성 |
| **DocLayout-YOLO** | 경량 레이아웃 검출 | 빠른 추론 속도 | 텍스트 인식 별도 필요 |
| **Marker** (VikParuchuri) | PDF → Markdown 변환 | 간단한 파이프라인 | Attribute 정보 없음 |

**권장**: MinerU 또는 PP-StructureV3를 1차 파이프라인으로 쓰고, 한국어 OCR 부분은 별도 보강(예: Naver Clova OCR, PaddleOCR 한국어 모델). 자동 추출은 "초안" 역할이므로 완벽할 필요 없이 사람 검수 부하를 줄이는 것이 목표.

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
├── status          ENUM             # uploading / processing / ready / error
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

```json
{
  "layout_dets": [
    {
      "category_type": "text_block",
      "poly": [136, 781, 340, 781, 340, 806, 136, 806],
      "ignore": false,
      "order": 0,
      "anno_id": 0,
      "text": "한국어 텍스트 내용...",
      "attribute": {
        "text_language": "text_ko",
        "text_background": "white",
        "text_rotate": "normal"
      },
      "line_with_spans": [
        {
          "category_type": "text_span",
          "poly": [136, 781, 340, 781, 340, 793, 136, 793],
          "ignore": false,
          "text": "한국어 텍스트..."
        }
      ]
    },
    {
      "category_type": "table",
      "poly": [100, 400, 500, 400, 500, 700, 100, 700],
      "ignore": false,
      "order": 1,
      "anno_id": 1,
      "latex": "\\begin{tabular}...",
      "html": "<table>...</table>",
      "attribute": {
        "table_layout": "horizontal",
        "with_span": false,
        "line": "full_line",
        "language": "table_ko"
      }
    }
  ],
  "page_attribute": {
    "data_source": "academic_literature",
    "language": "ko",
    "layout": "double_column",
    "watermark": false,
    "fuzzy_scan": false,
    "colorful_background": false
  },
  "extra": {
    "relation": [
      {
        "source_anno_id": 3,
        "target_anno_id": 4,
        "relation_type": "parent_son"
      }
    ]
  }
}
```

### 6.3 PostgreSQL JSONB 활용 쿼리 예시

JSONB를 쓰면 정규화 없이도 내부 필드를 검색할 수 있다.

```sql
-- 특정 프로젝트에서 table 카테고리가 포함된 페이지 찾기
SELECT p.id, p.page_no
FROM pages p
WHERE p.document_id IN (SELECT id FROM documents WHERE project_id = :pid)
  AND p.annotation_data @> '{"layout_dets": [{"category_type": "table"}]}';

-- 아직 page_attribute.language가 설정 안 된 페이지 찾기
SELECT p.id
FROM pages p
WHERE p.annotation_data->'page_attribute'->>'language' IS NULL;

-- GIN 인덱스 (대량 데이터 시 성능 최적화)
CREATE INDEX idx_pages_annotation ON pages USING GIN (annotation_data);
```

### 6.4 Export 로직 (OmniDocBench JSON 생성)

```python
# export_service.py (의사코드)
def export_project(project_id: str) -> list[dict]:
    pages = page_repo.get_all_by_project(project_id)

    result = []
    for page in pages:
        entry = page.annotation_data                  # JSONB 그대로 사용
        entry["page_info"] = {
            "page_no": page.page_no,
            "height": page.height,
            "width": page.width,
            "image_path": page.image_path,
            "page_attribute": entry.pop("page_attribute", {})
        }
        result.append(entry)

    return result  # → JSON 파일로 저장하면 OmniDocBench 포맷 완성
```

annotation_data를 OmniDocBench 구조로 저장했기 때문에,
Export는 사실상 **DB에서 꺼내서 page_info를 붙이는 것**이 전부다.

---

## 7. 개발 단계별 로드맵

### Phase 1: MVP (4~6주)

**목표**: 단일 PDF를 업로드하고, 수동으로 OmniDocBench JSON을 생산할 수 있는 최소 기능.

#### 개발 환경 셋업

- SQLite + SQLAlchemy ORM으로 로컬 개발 시작 (DB 설치 불필요)
- Repository 패턴 적용하여 DB 접근 캡슐화
- 파일 저장은 로컬 `./storage/` 디렉토리

#### 기능 구현

- PDF → 이미지 변환 파이프라인 구축
- 이미지 뷰어 + bbox 드로잉/편집 기본 기능
- Category 선택 UI (드롭다운)
- Page/Block Attribute 입력 UI
- Text/LaTeX/HTML 편집 패널
- OmniDocBench JSON 내보내기 (annotation_data 조합)
- 사용자 인증 기본 구현

**자동 추출 없이** 순수 수동 레이블링만 지원. 이 단계에서 UI/UX를 검증한다.

### Phase 2: 자동 추출 통합 + PostgreSQL 전환 (3~4주)

**목표**: 자동 추출 → 사람 검수 파이프라인 완성. 팀 작업 준비.

#### 인프라 전환

- Docker Compose 구성 (PostgreSQL + Backend + Frontend)
- .env의 DATABASE_URL을 PostgreSQL로 변경 (코드 수정 없음)
- JSONB GIN 인덱스 추가
- Celery + Redis 도입 (PDF 변환, 자동 추출 비동기 처리)

#### 기능 구현 (자동 추출)

- MinerU 또는 PP-StructureV3 통합
- 한국어 OCR 엔진 통합
- 자동 Attribute 분류기 추가
- 자동 추출 결과를 auto_extracted_data 컬럼에 저장 → annotation_data에 복사 → 사람이 수정
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

```text
# 프로젝트 관리
POST   /api/projects                   프로젝트 생성
GET    /api/projects/{id}              프로젝트 조회

# 문서 업로드 & 처리
POST   /api/projects/{id}/documents    PDF 업로드 (→ 자동 변환 시작)
GET    /api/documents/{id}/status      변환/추출 진행 상태

# 페이지 레이블링
GET    /api/pages/{id}                 페이지 데이터 + 자동 추출 결과 로드
PUT    /api/pages/{id}                 레이블링 결과 저장
PUT    /api/pages/{id}/attributes      페이지 속성 저장

# 레이아웃 요소
POST   /api/pages/{id}/elements        새 요소 추가
PUT    /api/elements/{id}              요소 수정 (bbox, category, attribute, text 등)
DELETE /api/elements/{id}              요소 삭제

# 관계
POST   /api/pages/{id}/relations       관계 추가
DELETE /api/relations/{id}             관계 삭제

# 내보내기
POST   /api/projects/{id}/export       OmniDocBench JSON 생성 & 다운로드

# 작업 관리
GET    /api/tasks                      내 할당 작업 목록
PUT    /api/tasks/{id}/submit          작업 제출
PUT    /api/tasks/{id}/review          리뷰 결과 (승인/반려)
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
| SQLite → PostgreSQL 전환 시 호환성 | 낮 | SQLAlchemy ORM으로 추상화; JSONB 전용 기능은 Phase 2부터 추가 |
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
