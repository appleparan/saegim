# 자동 추출 파이프라인

## Engine Type 기반 OCR 아키텍처

프로젝트별 `ocr_config` JSONB의 `engine_type` 키로 추출 엔진을 선택한다.
`BaseOCREngine` ABC를 통한 Strategy 패턴으로, 4가지 엔진 타입을 지원한다:

```text
ocr_config.engine_type
  ├── pdfminer           → pdfminer.six 폴백 (GPU 불필요, 동기)
  ├── commercial_api     → VLM API (Gemini/vLLM) full-page 분석
  ├── vllm               → vLLM 서버 (Chandra 등)
  └── split_pipeline     → Docling 레이아웃 + 외부 OCR (Gemini/vLLM)
```

| Engine Type | 설명 | 외부 서비스 | 사용 시나리오 |
| --- | --- | --- | --- |
| `pdfminer` | pdfminer.six 기본 추출 | 없음 | CI/테스트/GPU 없는 환경 |
| `commercial_api` | 상업용 VLM API (Gemini, vLLM) | Gemini API 또는 vLLM 서버 | 고품질 full-page OCR |
| `vllm` | vLLM OpenAI-compatible VLM 서버 | vLLM 서버 | 로컬 GPU 기반 OCR |
| `split_pipeline` | 분리 파이프라인 (Layout + OCR) | Docling (로컬) + Gemini/vLLM | 레이아웃은 Docling, OCR은 VLM |

## pdfminer.six 폴백 (`engine_type: pdfminer`)

```text
PDF 업로드
  → pypdfium2 페이지 렌더링 (2x scale PNG)
  → pdfminer.six extract_pages() → LTPage 트리 (동기)
     ├── LTTextBox → category_type: "text_block", get_text() 추출
     └── LTFigure/LTImage → category_type: "figure"
  → 좌표 변환: pdfminer 좌하단 원점 → 좌상단 원점 (y-flip) × 2.0 = 이미지 픽셀 좌표
  → auto_extracted_data JSONB에 OmniDocBench 형식으로 저장
  → document status: processing → ready (즉시)
  → 프론트엔드에서 "수락" → annotation_data로 복사
```

## Commercial API Engine (`engine_type: commercial_api`)

```text
PDF 업로드
  → pypdfium2 페이지 렌더링 (2x scale PNG)
  → asyncio 백그라운드 태스크 디스패치
     → 페이지별:
        1. VLM API에 full-page 이미지 전송
           - gemini: Google Gemini API (structured output 프롬프트)
           - vllm: vLLM OpenAI-compatible API
        2. JSON 응답 파싱 → OmniDocBench layout_dets 변환
     → asyncpg로 각 페이지 auto_extracted_data 업데이트
     → document status: extracting → ready (또는 extraction_failed)
```

## vLLM Engine (`engine_type: vllm`)

vLLM OpenAI-compatible API를 통한 full-page OCR:

```text
PDF 업로드
  → pypdfium2 페이지 렌더링 (2x scale PNG)
  → asyncio 백그라운드 태스크 디스패치
     → 페이지별:
        1. VllmOcrProvider.extract_page(image_path)
           → vLLM /v1/chat/completions (base64 이미지)
           → structured OCR 프롬프트로 JSON 파싱
        2. OmniDocBench layout_dets 변환
     → asyncpg로 각 페이지 auto_extracted_data 업데이트
     → document status: extracting → ready (또는 extraction_failed)
```

## Split Pipeline Engine (`engine_type: split_pipeline`)

Docling 레이아웃 감지 + 외부 OCR (Gemini/vLLM) 조합:

```text
PDF 업로드
  → pypdfium2 페이지 렌더링 (2x scale PNG)
  → asyncio 백그라운드 태스크 디스패치
     → 페이지별:
        1. DoclingLayoutDetector.detect_layout(image_path)
           → ibm-granite/granite-docling-258M 레이아웃 감지
           → list[LayoutRegion(bbox, category, score, text)]
        2. 텍스트 영역 크롭 (PIL/Pillow)
        3. 외부 OCR 프로바이더로 텍스트 추출:
           - gemini: Gemini API (category_hint별 프롬프트)
           - vllm: vLLM API (OlmOCR 등)
        4. OmniDocBench 조합 (equation→latex, table→html, 기타→text)
     → asyncpg로 각 페이지 auto_extracted_data 업데이트
     → document status: extracting → ready (또는 extraction_failed)
  → 프론트엔드에서 "수락" → annotation_data로 복사
```

## `ocr_config` JSONB 구조

```json
// commercial_api
{
  "engine_type": "commercial_api",
  "commercial_api": {
    "provider": "gemini",
    "api_key": "...",
    "model": "gemini-3-flash-preview"
  }
}

// vllm
{
  "engine_type": "vllm",
  "vllm": { "host": "localhost", "port": 8000, "model": "prithivMLmods/chandra-FP8-Latest" }
}

// split_pipeline (Docling + Gemini)
{
  "engine_type": "split_pipeline",
  "split_pipeline": {
    "docling_model_name": "ibm-granite/granite-docling-258M",
    "ocr_provider": "gemini",
    "ocr_api_key": "...",
    "ocr_model": "gemini-3-flash-preview"
  }
}

// pdfminer (fallback)
{ "engine_type": "pdfminer" }
```

## 구현 파일

### 엔진 추상화 (`services/engines/`)

- `services/engines/base.py`: `BaseOCREngine` ABC (`extract_page()`, `test_connection()`)
- `services/engines/factory.py`: `build_engine(ocr_config)` 팩토리 (`engine_type` 분기)
- `services/engines/pdfminer_engine.py`: `PdfminerEngine`
- `services/engines/commercial_api_engine.py`: `CommercialApiEngine` (Gemini/vLLM full-page)
- `services/engines/vllm_engine.py`: `VllmEngine` (vLLM OpenAI-compatible API)
- `services/engines/split_pipeline_engine.py`: `SplitPipelineEngine` (Docling 레이아웃 + 외부 OCR)

### 하위 서비스

- `services/layout_types.py`: `LayoutRegion` dataclass, `LayoutDetector` Protocol
- `services/docling_layout_service.py`: `DoclingLayoutDetector` (ibm-granite/granite-docling-258M)
- `services/ocr_pipeline.py`: 2단계 파이프라인 오케스트레이터 (`OcrPipeline`, `TextOcrProvider` Protocol)
- `services/ocr_provider.py`: 프롬프트 상수, `bbox_to_poly()`, `build_omnidocbench_page()`
- `services/gemini_ocr_service.py`: `GeminiOcrProvider`, `GeminiTextOcrProvider`
- `services/vllm_ocr_service.py`: `VllmOcrProvider`, `VllmTextOcrProvider`
- `services/ocr_connection_test.py`: 개별 연결 테스트 (`check_gemini_connection`, `check_vllm_connection`, `check_docling_connection`)
- `services/extraction_service.py`: pdfminer.six 폴백 추출

### 통합

- `services/document_service.py`: asyncio 백그라운드 태스크 (`build_engine()` → `asyncio.to_thread(engine.extract_page())`)
- `schemas/project.py`: `EngineType`, `CommercialApiConfig`, `VllmServerConfig`, `SplitPipelineConfig`
- `OcrSettingsPanel.svelte`: 엔진 타입 선택 카드 UI + 연결 테스트

## 재추출 (Re-extract)

OCR 엔진을 변경한 후 기존 문서를 새 엔진으로 재추출할 수 있다.

```text
라벨 페이지 좌측 패널의 "전체 재스캔" 버튼 클릭
  → POST /documents/{id}/re-extract
  → document_service.re_extract()
     1. 문서 상태 확인 (이미 extracting이면 409)
     2. 프로젝트 OCR 설정 로드 (_resolve_ocr_config)
     3. page_repo.list_for_extraction()으로 페이지 목록 조회
     4. 엔진 타입에 따라 동기/비동기 추출
  → auto_extracted_data만 갱신 (annotation_data는 유지)
  → 프론트엔드: 3초 간격 폴링 (extracting → ready)
  → 완료 후 ExtractionPreview에서 수락/강제 수락 가능
```

**강제 수락**: 재추출 후 기존 어노테이션이 있는 경우,
`POST /pages/{id}/force-accept-extraction`으로 기존 주석을 새 추출 결과로 대체할 수 있다.
기존 `accept-extraction`과 달리 `annotation_data` 비어있는지 체크하지 않는다.

## 후보 도구 비교

| 도구 | 특징 | 장점 | 단점 | 상태 |
| ------ | ------ | ------ | ------ | ------ |
| **MinerU** (OpenDataLab) | OmniDocBench 제작팀 도구 (AGPL) | OmniDocBench 포맷과 직접 호환, 15+ 카테고리 | AGPL 라이선스 | **제거됨** (라이선스 이슈) |
| **PP-StructureV3** (PaddlePaddle) | 레이아웃+OCR+테이블 통합 | 높은 정확도 (OmniDocBench Overall 86.73) | 패들 의존성 (Docker 서비스) | **제거됨** (Docling으로 대체) |
| **DocLayout-YOLO** | 경량 레이아웃 검출 | 빠른 추론 속도 | 텍스트 인식 별도 필요 | 미구현 |
| **Marker** (VikParuchuri) | PDF → Markdown 변환 | 간단한 파이프라인 | Attribute 정보 없음 | 미구현 |
| **Google Gemini API** | VLM structured output | 고품질 OCR, 클라우드 API | API 비용, 네트워크 의존 | **구현 완료** (프로젝트별 설정) |
| **vLLM (로컬)** | OpenAI-compatible VLM 서버 | 로컬 실행, 비용 없음 | GPU 필요, 모델 관리 | **구현 완료** (프로젝트별 설정) |

## 자동 Attribute 분류 전략

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
