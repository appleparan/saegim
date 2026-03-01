# OCR 엔진 시스템 리팩토링 계획

## Context

현재 5종의 OCR 엔진(pdfminer, commercial_api, integrated_server, split_pipeline, docling)이 있으나 여러 문제가 있음:
- 엔진 변경이 실제로 반영되지 않음 (pdfminer만 동작)
- PP-StructureV3는 이미지를 받을 수 없어서 사용 불가
- docling 독립 엔진이 GPU가 있어도 CPU로만 로딩됨
- vLLM 테스트가 통과하지 않음
- 현재 활성 엔진이 UI에 표시되지 않음

**목표**: 4개 엔진으로 정리하고, 엔진 전환이 정상 동작하며, 프로젝트 페이지에 현재 엔진을 표시

### 최종 엔진 목록
| 엔진 | 설명 |
|------|------|
| `pdfminer` | 폴백 (GPU 불필요, 동기) |
| `commercial_api` | Gemini API (full-page VLM) |
| `vllm` | vLLM 서버 (기존 `integrated_server`에서 PP 제거 후 이름변경) |
| `split_pipeline` | Docling 레이아웃 + Gemini/vLLM 텍스트 OCR |

---

## Stage 1: LayoutRegion을 공유 모듈로 이동 + Docling 레이아웃 서비스 생성

**Goal**: `LayoutRegion`을 `ppstructure_service.py`에서 분리하고, docling 기반 레이아웃 감지 서비스 생성

### 수정 파일
- **신규**: `saegim-backend/src/saegim/services/layout_types.py`
  - `LayoutRegion` dataclass 이동 (from `ppstructure_service.py`)
  - `LayoutDetector` Protocol 정의: `detect_layout(image_path: Path) -> list[LayoutRegion]`

- **신규**: `saegim-backend/src/saegim/services/docling_layout_service.py`
  - `docling_engine.py`의 핵심 로직 추출:
    - 상수: `_DOCTAGS_COORD_SIZE`, `_TAG_TO_CATEGORY`, `_ELEMENT_RE`, `_LOC_RE`
    - 함수: `_extract_locs()`, `_scale_to_poly()`, `_otsl_to_html()`
  - `DoclingLayoutDetector` 클래스:
    - `__init__(model_name)` — lazy loading
    - `detect_layout(image_path)` → `list[LayoutRegion]` (이미지에서 크기 자동 취득)
    - `test_connection()` → `tuple[bool, str]`
    - `_ensure_model_loaded()` — CUDA 감지 + 명시적 로깅

- **수정**: `saegim-backend/src/saegim/services/ocr_pipeline.py`
  - `LayoutRegion` import를 `layout_types`에서 가져오도록 변경
  - `OcrPipeline.__init__`의 `layout_client` 타입을 `LayoutDetector` Protocol로 변경

### 테스트
- `docling_layout_service` 단위 테스트 (DocTags 파싱, 좌표 변환, OTSL→HTML)
- `ocr_pipeline` 기존 테스트가 새 Protocol로도 통과 확인

---

## Stage 2: `integrated_server` → `vllm` 이름변경 및 PP-StructureV3 제거

**Goal**: vLLM 전용 엔진으로 단순화

### 수정 파일
- **이름변경**: `engines/integrated_server_engine.py` → `engines/vllm_engine.py`
  - `IntegratedServerEngine` → `VllmEngine`
  - PP-StructureV3 분기 코드 전부 삭제 (`_is_ppstructure_model`, `PpstructureClient`, `OcrPipeline` import)
  - `VllmOcrProvider`만 유지

- **수정**: `engines/factory.py`
  - `'integrated_server'` → `'vllm'`
  - `_build_integrated_server()` → `_build_vllm()`
  - `'docling'` 분기 삭제
  - valid 엔진 목록 업데이트: `'commercial_api', 'vllm', 'split_pipeline', 'pdfminer'`

- **수정**: `schemas/project.py`
  - `EngineType` = `Literal['commercial_api', 'vllm', 'split_pipeline', 'pdfminer']`
  - `IntegratedServerConfig` → `VllmServerConfig` (host, port, model 유지)
  - `DoclingConfig` 삭제
  - `SplitPipelineConfig` — `layout_server_url` → `docling_model_name` (기본값: `ibm-granite/granite-docling-258M`)
  - `OcrConfigUpdate` / `OcrConfigResponse` — `integrated_server` → `vllm`, `docling` 삭제

- **수정**: `api/routes/projects.py`
  - `_validate_ocr_config()` — `integrated_server` → `vllm`, `docling` 삭제
  - test connection 로직 업데이트

- **수정**: `ocr_connection_test.py`
  - `check_ppstructure_connection()` 삭제

- **수정**: `engines/__init__.py` docstring 업데이트

### 테스트
- `test_integrated_server_engine.py` → `test_vllm_engine.py` (PP-StructureV3 테스트 삭제)
- `test_factory.py` 업데이트
- `test_project_ocr_config.py` 업데이트

---

## Stage 3: split_pipeline을 Docling 레이아웃으로 전환

**Goal**: PP-StructureV3 대신 Docling을 레이아웃 감지기로 사용

### 수정 파일
- **수정**: `engines/split_pipeline_engine.py`
  - `PpstructureClient` → `DoclingLayoutDetector` import
  - `__init__`: `layout_server_url` → `docling_model_name`, `DoclingLayoutDetector` 생성
  - `_parse_url()` 헬퍼 삭제 (더 이상 URL 파싱 불필요)
  - `test_connection()`: docling 가용성 확인 + OCR 프로바이더 확인

- **수정**: `engines/factory.py` `_build_split_pipeline()`
  - `layout_server_url` → `docling_model_name` 추출

### 테스트
- `test_split_pipeline_engine.py` — `PpstructureClient` mock → `DoclingLayoutDetector` mock
- 양쪽 OCR 프로바이더(gemini, vllm) 테스트

---

## Stage 4: PP-StructureV3 및 standalone docling 파일 삭제

**Goal**: 데드 코드 완전 제거

### 삭제 파일
- `saegim-backend/src/saegim/services/ppstructure_service.py`
- `saegim-backend/src/saegim/services/engines/docling_engine.py`
- `saegim-backend/tests/services/test_ppstructure_service.py` (존재 시)
- `saegim-backend/tests/services/engines/test_docling_engine.py`

### 확인
- `ruff check` — 미사용 import 없음
- grep으로 `ppstructure`, `DoclingEngine`, `DoclingConfig` 참조 0건 확인

---

## Stage 5: DB 마이그레이션

**Goal**: 기존 프로젝트의 `ocr_config` JSONB 데이터를 새 스키마에 맞게 변환

### 신규 파일
- `saegim-backend/migrations/002_rename_engine_types.sql`

```sql
-- integrated_server → vllm
UPDATE projects
SET ocr_config = jsonb_set(
    ocr_config, '{engine_type}', '"vllm"'
) || jsonb_build_object('vllm', ocr_config->'integrated_server')
   - (ARRAY['integrated_server'])
WHERE ocr_config->>'engine_type' = 'integrated_server';

-- docling → pdfminer (폴백)
UPDATE projects
SET ocr_config = '{"engine_type": "pdfminer"}'::jsonb
WHERE ocr_config->>'engine_type' = 'docling';

-- split_pipeline: layout_server_url → docling_model_name
UPDATE projects
SET ocr_config = jsonb_set(
    ocr_config, '{split_pipeline}',
    (ocr_config->'split_pipeline') - 'layout_server_url'
    || '{"docling_model_name": "ibm-granite/granite-docling-258M"}'::jsonb
)
WHERE ocr_config->>'engine_type' = 'split_pipeline'
  AND ocr_config->'split_pipeline' IS NOT NULL;
```

---

## Stage 6: 프론트엔드 업데이트

**Goal**: 타입, 설정 UI 업데이트 + 프로젝트 페이지 헤더에 엔진 배지 표시

### 수정 파일
- **수정**: `saegim-frontend/src/lib/api/types.ts`
  - `EngineType` → `'commercial_api' | 'vllm' | 'split_pipeline' | 'pdfminer'`
  - `IntegratedServerConfig` → `VllmServerConfig`
  - `DoclingConfig` 삭제
  - `SplitPipelineConfig` — `layout_server_url` → `docling_model_name`
  - `OcrConfigResponse` / `OcrConfigUpdate` — `integrated_server?` → `vllm?`, `docling?` 삭제

- **수정**: `saegim-frontend/src/lib/components/settings/OcrSettingsPanel.svelte`
  - `engineTypes` 배열: 4개 엔진으로 업데이트
  - integrated_server → vllm (라벨: "vLLM 서버")
  - docling 옵션 삭제
  - split_pipeline 설명: "Docling 레이아웃 + Gemini/vLLM OCR"
  - split_pipeline 설정 UI: layout_server_url 입력 → docling_model_name 입력
  - 상태/이벤트 핸들러 업데이트

- **수정**: `saegim-frontend/src/routes/projects/[id]/+page.svelte`
  - `getOcrConfig` import 추가
  - `loadData()`에서 OCR config 함께 로드
  - 프로젝트 헤더에 엔진 배지 추가:
    - `<Badge variant="secondary">`로 엔진명 표시
    - 클릭 시 설정 페이지로 이동
  - 엔진 라벨 매핑:
    - `pdfminer` → "pdfminer"
    - `commercial_api` → "Gemini API"
    - `vllm` → "vLLM"
    - `split_pipeline` → "Docling + OCR"

- **수정**: `saegim-frontend/src/routes/projects/[id]/settings/+page.svelte`
  - 새 엔진 타입에 맞게 업데이트

### 테스트
- `OcrSettingsPanel.test.ts` 업데이트

---

## Stage 7: 테스트 수정 및 전체 검증

**Goal**: 모든 테스트 통과 + lint/format/type check 통과

### 작업
1. 백엔드: `uv run pytest --cov` — 전체 통과 확인
2. 백엔드: `uv run ruff format` + `uv run ruff check` + `uv run ty check`
3. 프론트엔드: `bun run test` — 전체 통과 확인
4. 프론트엔드: `bunx oxlint` + `bun run check` (svelte-check)
5. grep으로 데드 참조 최종 확인: `ppstructure`, `integrated_server`, `DoclingEngine`

### E2E 검증
- pdfminer 엔진으로 PDF 업로드 → 동기 추출 확인
- 설정에서 엔진 변경 후 re-extract → 비동기 추출 확인
- 프로젝트 페이지 헤더에 엔진 배지 표시 확인
