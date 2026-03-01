# 한국어 문서 VLM 벤치마크 레이블링 웹앱 — 플래닝 가이드

---

## 1. 프로젝트 개요 및 평가

### 1.1 목표 정의

PDF 등 한국어 문서 데이터셋을 업로드하면 OmniDocBench 포맷의 3가지 메타데이터
(Dataset Format, Evaluation Categories, Attribute Labels)를 자동 추출하고,
사람이 이를 검수·레이블링하여 최종 벤치마크 데이터셋을 생산하는 웹앱을 구축한다.

### 1.1.1 상위 비전: 논문 리뷰 에이전트에서 VLM 벤치마크 플랫폼으로

본 프로젝트의 출발점은 **논문 리뷰 에이전트**다. 논문의 Key Figure를 추출하고,
OCR 품질을 검증하며, 핵심 아이디어를 구조화하는 것이 원래 목표였다.
이 과정에서 Key Figure 추출과 OCR이 핵심 병목임을 확인했고,
이를 체계적으로 해결하기 위해 에이전트 기반 레이블링 프레임워크를 구상했다.

이후 VLM 벤치마크 데이터셋의 부족(특히 한국어)을 인식하고, KO-VLM-Benchmark를 참조하여 레이블링 프레임워크를 범용 VLM 벤치마크 구축 플랫폼으로 확장하기로 결정했다.

**궁극적 목표는 3가지 평가 태스크를 모두 커버하는 프레임워크**:

| 태스크 | 평가 대상 | saegim에서의 역할 |
| ------ | --------- | ----------------- |
| **KO-VQA** | 다양한 도메인의 한국어 문서 이해 능력 + 문서 기반 답변 추론 능력 | Q&A 쌍 + 근거 영역 레이블링 |
| **KO-VDC** | 한국어 시각화 도식 자료 이해 능력 + 도식 기반 설명문 생성/이해 능력 | Element-level 구조 레이블링 (현재 MVP) |
| **KO-OCRAG** | 복잡한 구조의 한국어 문서 OCR 능력 + Visual Context parsing 능력 | Context-Query-Answer 트리플렛 레이블링 |

이를 위해 **두 가지 어노테이션 패러다임**이 공존해야 한다:

```text
패러다임 1: Element-centric (KO-VDC 중심) ← 현재 구현 범위
  Page → [Element(bbox, category, text, attribute)]

패러다임 2: Task-centric (KO-VQA/OCRAG 중심) ← 향후 확장
  Page → [Task(question, answer, evidence_regions)]
```

### 1.1.2 논문 리뷰 에이전트를 위한 문서 분석 메타데이터

논문 리뷰 에이전트의 핵심 기능인 **의미 수준 분석**(핵심 아이디어, 주요 그림 해석 등)은
구조적 레이블링과는 다른 계층에 속한다.
이를 **document-level 메타데이터**로 분리하여 `documents.analysis_data` JSONB 컬럼에 저장한다.

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

이 프로젝트의 핵심 가치는 "자동 추출 + 사람 검증"의 하이브리드 파이프라인에 있다.
순수 수동 레이블링은 비용이 너무 크고, 순수 자동 추출은 품질이 보장되지 않기 때문에,
PDF에서 가능한 메타데이터를 자동으로 뽑고 사람이 검수/보정하는 구조가 현실적이다.

다만 주의할 점이 있다:

- PDF에서 레이아웃 요소를 자동 검출하는 단계의 품질이 전체 파이프라인의 병목이 된다. 초기 버전에서는 기존 도구(MinerU, PP-Structure 등)를 활용하되, 자체 모델을 학습할 로드맵도 고려해야 한다.
- OmniDocBench의 Attribute Labels는 상당히 세분화되어 있어, 한국어 문서에 맞게 일부 커스터마이징(예: 한글 서체 분류, 한국 문서 유형 세분화)이 필요할 수 있다.
- KO-VLM-Benchmark의 평가 태스크(VDC, VQA, OCRAG)를 모두 커버하려면 레이블링 범위가 넓어지므로, Phase를 나누어 점진적으로 확장하는 것을 권장한다.

---

## 2. 출력 데이터 스키마 (OmniDocBench 기반)

레이블링 결과물은 3가지 계층 (Dataset Format, Evaluation Categories, Attribute Labels)으로 구성된 JSON을 최종 출력한다.

상세: [데이터 스키마](docs/architecture/data-schema.md)

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
[Phase C: 검증 & 내보내기]
     │  ├── 자동 검증 규칙 (필수 필드, 좌표 유효성 등)
     │  └── OmniDocBench JSON 내보내기
     │
     ▼
[최종 벤치마크 데이터셋]
```

### 3.2 기술 스택 요약

| 계층 | 기술 |
| ---- | ---- |
| **프론트엔드** | Svelte 5 (Runes) + TypeScript + Vite 7 + Konva.js + PDF.js |
| **백엔드** | FastAPI + asyncpg (raw SQL) + Repository 패턴 |
| **DB** | PostgreSQL 15+ (JSONB) |
| **OCR 엔진** | 4종 Strategy 패턴 (pdfminer, commercial_api, vllm, split_pipeline) |
| **배포** | Docker Compose |

상세 문서:

- [백엔드 아키텍처](docs/backend/architecture/architecture.md)
- [데이터베이스](docs/backend/architecture/database.md)
- [추출 파이프라인](docs/architecture/extraction-pipeline.md)
- [레이블링 워크플로우](docs/architecture/labeling-workflow.md)
- [API 엔드포인트](docs/backend/guide/api.md)
- [프론트엔드 아키텍처](docs/frontend/architecture/architecture.md)
- [배포 가이드](docs/deployment/quickstart.md)

---

## 4. 개발 단계별 로드맵

### Phase 1: MVP ✅ 완료

**목표**: 단일 PDF를 업로드하고, 수동으로 OmniDocBench JSON을 생산할 수 있는 최소 기능.

- PDF → 이미지 변환 (pypdfium2), 3-layer 하이브리드 레이블링 UI
- Category/Attribute/Text 편집, OmniDocBench JSON Export
- 프로젝트/문서/페이지 CRUD, E2E 테스트

### Phase 2: 자동 추출 통합 ✅ 완료

**목표**: 자동 추출 → 사람 검수 파이프라인 완성.

- pdfminer.six 텍스트/이미지 자동 추출 + 좌표 스케일링 (PR #28)
- 2단계 OCR 파이프라인: Docling 레이아웃 + Gemini/vLLM OCR (PR #6 → PR #10 → PR #60)
- Engine Type 기반 아키텍처 (`BaseOCREngine` ABC + Strategy 패턴) (PR #12)
- asyncio 백그라운드 OCR 추출 — Celery/Redis 제거 (PR #14)
- 프로젝트별 OCR 설정 UI + 연결 테스트
- 그리기 영역 OCR 텍스트 추출 (PR #32)
- 자동 Attribute 분류기 — 페이지/테이블/텍스트/수식 속성 자동 분류 (PR #36)
- Docling 레이아웃 감지 엔진 — ibm-granite/granite-docling-258M 기반 문서 레이아웃 자동 감지 (PR #46)
- Relation 연결 도구 — CRUD API + UI (RelationPanel) + SVG 오버레이 (PR #49)
- 읽기 순서 에디터 — 드래그앤드롭 재정렬 + 캔버스 오버레이 + `O` 단축키 (PR #50)

### Phase 3: 멀티유저 협업

**목표**: 여러 사용자가 프로젝트를 공유하고, 역할 기반으로 레이블링 작업을 분담·검수한다.

- 인증/인가 (JWT), 프로젝트-유저 매핑 (`project_members` 테이블)
- 태스크 할당/제출/승인·반려 워크플로우 API
- 동시 편집 방지 (기존 `pages.locked_at` 활용)
- 프론트엔드: 로그인, 태스크 대시보드, 검수 큐

상세: [멀티유저 협업](docs/architecture/multi-user-collaboration.md)

### Phase 4: Data Curation & 품질 관리

**목표**: 데이터셋의 다양성과 품질을 실시간으로 모니터링하고 큐레이션 조언을 제공한다.

- 분포 대시보드 (문서유형/언어/레이아웃/카테고리별 시각화)
- 다양성 스코어 및 큐레이션 추천 (목표 분포 대비 커버리지)
- 어노테이션 품질 지표 (텍스트/속성 완성도, 이상치 탐지)
- Inter-Annotator Agreement (Phase 3 의존, Cohen's Kappa / IoU)

상세: [Data Curation](docs/architecture/data-curation.md)

---

## 5. 한국어 문서 특화 고려사항

### 5.1 OmniDocBench 포맷 커스터마이징

OmniDocBench는 영어/중국어 중심이므로, 한국어 문서에 맞게 다음을 확장한다:

- **language 필드**: `ko`, `en`, `ko_en_mixed` 추가.
- **data_source 확장**: `government_doc` (공문서), `legal_doc` (법률 문서), `medical_report` (의료 보고서) 등 한국 특화 문서 유형 추가 가능.
- **Evaluation Category 확장**: 한국어 문서에 자주 등장하는 요소(인감/도장, 한자 혼용 텍스트 등)를 추가 카테고리 또는 속성으로 반영 검토.
- 기본 스키마를 변경하지 않고 **확장(additive)** 방식으로 구현하여 OmniDocBench 호환성을 유지한다.

### 5.2 한국어 OCR 이슈

- 한글 자모 분리/조합 문제: OCR 결과에서 자모가 분리되는 경우 후처리 필요
- 한자 혼용 텍스트: text_language 속성에서 `text_ko_hanja_mixed` 추가 고려
- 세로 쓰기: 한국 전통 문서나 일부 신문에서 세로 쓰기 존재 → text_rotate 속성으로 대응

---

## 6. 리스크 & 완화 전략

| 리스크 | 영향 | 완화 |
| -------- | ------ | ------ |
| 자동 추출 품질 부족으로 수동 작업량 증가 | 높 | 추출 도구 비교 평가 후 최적 선택; 점진적 개선 루프 |
| 고해상도 이미지 렌더링 성능 | 중 | 타일 기반 렌더링, 이미지 피라미드 활용 |
| 복잡한 레이블링 UI로 인한 학습 곡선 | 중 | 단축키 치트시트, 단계별 가이드 |
| JSONB 데이터 일관성 깨짐 | 중 | JSON Schema 검증을 저장 시 서버에서 수행; task_history 스냅샷으로 복원 |
| asyncpg raw SQL 마이그레이션 | 낮 | Repository 패턴으로 SQL 격리; 마이그레이션 파일(`migrations/`)로 스키마 관리 |
| 파일 저장소 유실 | 중 | Docker volume 마운트; 추후 S3/MinIO 전환 시 백업 자동화 |
| OmniDocBench 스키마 버전 변경 | 낮 | annotation_data에 schema_version 필드 관리; 마이그레이션 스크립트 준비 |

---

## 7. 성공 지표 (KPI)

| 지표 | 목표 |
| ------ | ------ |
| 페이지당 평균 레이블링 시간 | 자동추출 없이 30분 이내, 자동추출 시 10분 이내 |
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
