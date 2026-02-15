# 개요

## 배경

한국어 문서 VLM 벤치마크를 구축하려면 문서의 레이아웃 요소(제목, 본문, 표, 수식 등)를
사람이 직접 어노테이션해야 합니다. saegim은 이 과정을 체계적으로 관리하는 플랫폼입니다.

## 상위 비전

saegim의 출발점은 논문 리뷰 에이전트(Key Figure 추출, OCR, 핵심 아이디어 구조화)이며,
궁극적으로는 KO-VLM-Benchmark의 3가지 평가 태스크를 모두 커버하는 프레임워크를 지향합니다:

- **KO-VDC**: 한국어 문서 이미지 → 텍스트 변환 정확도 평가 (현재 MVP의 핵심)
- **KO-VQA**: 문서 이미지에 대한 질의응답 정확도 평가 (Phase 4b 계획)
- **KO-OCRAG**: OCR 기반 검색-생성 파이프라인 평가 (Phase 4c 계획)

이를 위해 두 가지 어노테이션 패러다임이 공존합니다:

1. **Element-centric** (Phase 1~3): `Page → [Element(bbox, category, text, attribute)]`
2. **Task-centric** (Phase 4b~4c): `Page → [Task(question, answer, evidence_regions)]`

또한 논문 리뷰 에이전트를 위한 **문서 분석 메타데이터**(Overview, Core Idea, Key Figures,
Limitations)를 document-level JSONB(`documents.analysis_data`)로 관리합니다.
외부 AI(VLM/LLM)가 자동 추출하고 사람이 검수하는 패턴은 기존 auto-extraction과 동일합니다.

## OmniDocBench 포맷

saegim은 [OmniDocBench](https://github.com/opendatalab/OmniDocBench) 포맷을 사용합니다.
각 페이지의 어노테이션 데이터는 다음 구조를 따릅니다:

```json
{
  "layout_dets": [
    {
      "category_type": "text_block",
      "poly": [x1, y1, x2, y2, x3, y3, x4, y4],
      "ignore": false,
      "order": 0,
      "anno_id": 0,
      "text": "본문 텍스트",
      "attribute": {
        "text_language": "text_ko",
        "text_background": "white",
        "text_rotate": "normal"
      },
      "line_with_spans": [],
      "merge_list": [],
      "latex": "",
      "html": ""
    }
  ],
  "page_attribute": {
    "data_source": "academic_literature",
    "language": "ko",
    "layout": "single_column",
    "watermark": false,
    "fuzzy_scan": false,
    "colorful_background": false
  },
  "extra": {
    "relation": []
  }
}
```

### 블록 레벨 카테고리 (15종)

| 카테고리 | 설명 |
| ---------- | ------ |
| `title` | 제목 |
| `text_block` | 본문 텍스트 블록 |
| `figure` | 그림/이미지 |
| `figure_caption` | 그림 캡션 |
| `table` | 표 |
| `table_caption` | 표 캡션 |
| `table_footnote` | 표 각주 |
| `equation_isolated` | 독립 수식 |
| `equation_caption` | 수식 번호/캡션 |
| `header` | 페이지 헤더 |
| `footer` | 페이지 푸터 |
| `page_number` | 페이지 번호 |
| `reference` | 참고문헌 |
| `abstract` | 초록 |
| `code_block` | 코드 블록 |

### 스팬 레벨 카테고리 (4종)

| 카테고리 | 설명 |
| ---------- | ------ |
| `text_span` | 텍스트 스팬 |
| `equation_inline` | 인라인 수식 |
| `footnote_mark` | 각주 표시 |
| `reference_mark` | 참조 표시 |

## 워크플로우

```mermaid
graph TD
    A[PDF 업로드] --> B[페이지 이미지 변환]
    B --> C[레이아웃 자동 추출]
    B --> F[AI 문서 분석]
    C --> D[페이지별 레이블링]
    F --> G[분석 메타데이터 검수]
    D --> E{검토}
    G --> E
    E -->|승인| H[내보내기]
    E -->|반려| D
    H --> H1[OmniDocBench JSON]
    H --> H2[VQA Export]
    H --> H3[OCRAG Export]
```

1. **PDF 업로드**: 프로젝트에 PDF 문서를 업로드합니다
2. **이미지 변환**: PyMuPDF가 각 페이지를 2배 해상도 PNG로 변환합니다
3. **자동 추출** (Phase 2): 레이아웃 검출 + OCR로 annotation_data 초안 생성
4. **AI 문서 분석** (Phase 4a): VLM/LLM으로 Overview, Core Idea, Key Figures, Limitations 자동 추출 → `analysis_data`에 저장
5. **레이블링**: 어노테이터가 각 페이지의 레이아웃 요소를 표시합니다
6. **분석 메타데이터 검수**: AI가 추출한 문서 분석 결과를 사람이 검토합니다
7. **검토**: 리뷰어가 어노테이션을 검토합니다
8. **내보내기**: 프로젝트 유형에 따라 OmniDocBench / VQA / OCRAG 형식으로 내보냅니다

## 설계 원칙

- **SQLAlchemy 없이 raw SQL**: asyncpg로 PostgreSQL에 직접 raw SQL 실행
- **JSONB 활용**: 어노테이션 데이터를 PostgreSQL JSONB 컬럼에 저장
- **레이어드 아키텍처**: Repository → Service → Router 계층 분리
- **비동기 처리**: asyncpg + FastAPI의 async/await 기반
