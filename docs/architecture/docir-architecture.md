# DocIR 아키텍처

## 1. 배경 및 동기

### 현재 아키텍처의 문제점

현재 OCR 엔진들이 **모델 호출 + 응답 파싱 + OmniDocBench 변환**을 하나의 클래스에서 처리한다:

```mermaid
flowchart LR
    A["extract_page()"] --> B["프롬프트 생성 (모델 특화)"]
    B --> C["HTTP POST (전송)"]
    C --> D["응답 파싱 (모델 특화)"]
    D --> E["OmniDocBench 변환"]
```

모델을 추가할 때마다 Provider 클래스 전체를 새로 작성하거나,
기존 클래스에 분기 로직을 추가해야 한다.

### 모델 출력 형식의 이질성

| 모델 | 출력 형식 |
| ---- | --------- |
| Chandra | JSON 배열 `[{category_type, bbox, text}]` |
| LightOnOCR-bbox-soup | 텍스트 + `![image](image_N.png)x1,y1,x2,y2` (좌표 0-1000) |
| PaddleOCR-VL | 프롬프트 의존 텍스트 (`OCR:`, `Table Recognition:`) |
| PP-DocLayoutV3 | bbox + label + score (텍스트 없음) |
| Docling | `LayoutRegion(bbox, category, score)` |
| Gemini API | 구조화 JSON 또는 텍스트 |

하나의 Parser로 모든 형식을 처리하면 복잡도가 폭발한다.

### 해결 방향

**모델별 파싱 로직을 분리하고, 공통 중간 표현(DocIR)을 도입한다.**

## 2. 3-Stage 아키텍처

```mermaid
flowchart LR
    P["Provider: 모델 호출"]
    A["Adapter: raw → DocIR"]
    D["DocIR (PageIR)"]
    E["Exporter: DocIR → 출력"]

    P --> A --> D --> E
```

### 컴포넌트 책임

| 컴포넌트 | 책임 | 금지 |
| -------- | ---- | ---- |
| **Provider** | HTTP 호출 또는 로컬 추론. raw 출력 반환 | 파싱 로직 없음 |
| **Adapter** | raw 출력 → PageIR 변환. 좌표 정규화, 라벨 매핑 | OmniDocBench 변환 없음 |
| **Engine** | 오케스트레이션만 (provider → adapter → exporter) | 모델 특화 로직 없음 |
| **Exporter** | PageIR → 최종 출력 (OmniDocBench dict) | 모델 특화 로직 없음 |

### 핵심 원칙

- 모델별 로직은 **Adapter에만** 존재한다.
- 새 모델 추가 시 **1 Adapter** (+선택적 Provider)만 작성한다.
- Engine과 Exporter는 모델에 무관하게 동작한다.

### 적용 범위

DocIR 3-stage 파이프라인은 **이미지 기반 OCR 엔진**에만 적용된다:

| 엔진 | DocIR 적용 | 이유 |
| ---- | ---------- | ---- |
| `vllm` | O | 이미지 → VLM API → JSON/텍스트 |
| `commercial_api` (Gemini) | O (향후) | 이미지 → Gemini API → JSON |
| `split_pipeline` | O | 이미지 → Layout + OCR → 합성 |
| `pdfminer` (폴백) | **X** | PDF 파일 직접 처리, 이미지 불필요 |

**pdfminer**는 완전히 다른 실행 경로를 사용한다:

```mermaid
flowchart LR
    subgraph DocIR["이미지 기반 엔진 (DocIR 적용)"]
        IMG["페이지 이미지"] --> PROV["Provider"]
        PROV --> ADPT["Adapter"]
        ADPT --> PIR["PageIR"]
        PIR --> EXP["Exporter"]
    end

    subgraph Pdfminer["pdfminer 폴백 (DocIR 미적용)"]
        PDF["PDF 파일"] --> PM["pdfminer.six extract_pages()"]
        PM --> ODB2["OmniDocBench dict"]
    end

    EXP --> ODB1["OmniDocBench dict"]
```

pdfminer는 `PdfminerEngine.extract_page()`가 `NotImplementedError`를 raise하며,
실제 추출은 `extraction_service.extract_page_elements(pdf_path, page_no)`에서
PDF를 직접 읽어 동기적으로 처리한다. Adapter 변환 대상이 아니다.

## 3. DocIR 명세

### PageIR

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class PageIR:
    page_id: str                            # 페이지 식별자
    width_px: int                           # 이미지 너비 (pixel)
    height_px: int                          # 이미지 높이 (pixel)
    elements: tuple[ElementIR, ...]         # 불변 요소 목록
    artifacts: dict[str, Any] = field(      # 임베디드 이미지, 크롭 영역 등
        default_factory=dict,
    )
    meta: dict[str, Any] = field(           # model_name, params, runtime 등
        default_factory=dict,
    )
```

**필드 설명**:

- `elements`: 페이지에서 감지된 모든 레이아웃 요소. `tuple`로 불변성 보장.
- `artifacts`: 모델이 생산한 부가 데이터 (예: LightOnOCR의 임베디드 이미지).
- `meta`: 모델 이름, 추론 파라미터, 런타임 정보.
  디버그 모드에서 `meta["raw_model_output"]`으로 원본 출력을 보존할 수 있다.

### ElementIR

```python
from typing import Literal

ElementKind = Literal[
    'text_block', 'title', 'table', 'figure', 'equation',
    'header', 'footer', 'page_number', 'code', 'reference',
    'caption', 'footnote', 'unknown',
]

@dataclass(frozen=True)
class ElementIR:
    id: str                                      # 고유 식별자
    kind: ElementKind | str                      # 요소 유형 (확장 가능)
    geometry: Geometry | None = None             # 위치 정보 (없을 수 있음)
    text: str | None = None                      # 텍스트 내용
    reading_order: int | None = None             # 읽기 순서
    scores: dict[str, float] = field(            # 모델 신뢰도
        default_factory=dict,
    )
    tags: dict[str, Any] = field(                # 모델별 원본 라벨, 메타데이터
        default_factory=dict,
    )
```

**설계 결정**:

- `kind`는 `Literal` + `str` union. 알려진 타입은 타입 안전, 새 모델의 커스텀 라벨도 허용.
- `geometry`는 Optional. PaddleOCR-VL 등 geometry 없는 출력 지원.
- `text`는 Optional. Layout-only 모델(PP-DocLayoutV3, Docling) 지원.
- `scores`는 자유 형식. 모델별로 `{"det": 0.95}`, `{"rec": 0.87}` 등 사용.
- `tags`에 원본 모델 라벨 보존. 예: `tags["model_label"] = "paragraph_title"`.

### Geometry

```python
@dataclass(frozen=True)
class Geometry:
    bbox: tuple[float, float, float, float] | None = None  # [x1, y1, x2, y2]
    polygon: list[tuple[float, float]] | None = None        # [[x, y], ...]
    rotation: float = 0.0                                    # 회전 각도 (도)
```

**좌표 규칙**: Adapter가 항상 **pixel 좌표**로 정규화한다.
모델이 정규화 좌표(0-1000)를 출력하면 Adapter에서 pixel로 변환한다.

### RecognitionResult (Split Pipeline 전용)

```python
@dataclass(frozen=True)
class RecognitionResult:
    element_id: str               # 매칭할 ElementIR의 id
    text: str                     # 추출된 텍스트
    category_hint: str            # table → html, equation → latex
    confidence: float | None = None
```

Split pipeline의 merge 단계에서 `element_id`로 레이아웃 ElementIR과 매칭하여
텍스트를 주입한다.

## 4. 지원 모델 카탈로그

### 4.1. datalab-to/chandra (vLLM, Full-page OCR)

- **역할**: Full-page OCR (레이아웃 + 텍스트)
- **런타임**: vLLM OpenAI-compatible API
- **입력**: STRUCTURED_OCR_PROMPT + base64 이미지
- **출력**: JSON 배열 `[{category_type, bbox, text, order}]` (pixel 좌표)

**DocIR 매핑**:

| 모델 출력 | DocIR 필드 |
| --------- | ---------- |
| `category_type` | `ElementIR.kind` |
| `bbox [x1,y1,x2,y2]` | `Geometry.bbox` (pixel, 변환 불필요) |
| `text` | `ElementIR.text` |
| `order` | `ElementIR.reading_order` |

**vLLM 서빙**:

```bash
vllm serve datalab-to/chandra \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 4 \
    --max-model-len 32768
```

### 4.2. lightonai/LightOnOCR-2-1B-bbox-soup (vLLM, Full-page OCR)

- **역할**: Full-page OCR (텍스트 중심 + 이미지 위치)
- **런타임**: vLLM OpenAI-compatible API
- **입력**: 이미지만 (프롬프트 없음)
- **출력**: 텍스트 + 임베디드 이미지 bbox

```text
Some document text here.
More text content.
![image](image_0.png)120,50,850,400
Additional text below the image.
```

좌표는 **[0, 1000] 정규화** 범위이다.

**DocIR 매핑**:

| 모델 출력 | DocIR 필드 |
| --------- | ---------- |
| 텍스트 블록 | `ElementIR(kind='text_block', geometry=None, text=...)` |
| `![image]` bbox | `ElementIR(kind='figure', geometry=Geometry(bbox=pixel변환))` |
| 전체 텍스트 | `PageIR.meta['fulltext']` |
| 임베디드 이미지 | `PageIR.artifacts['embedded_images']` |

**좌표 변환**: `x_px = x_norm * page_width / 1000`

**vLLM 서빙**:

```bash
vllm serve lightonai/LightOnOCR-2-1B-bbox-soup \
    --limit-mm-per-prompt '{"image": 1}' \
    --mm-processor-cache-gb 0 \
    --no-enable-prefix-caching
```

### 4.3. PaddlePaddle/PaddleOCR-VL (vLLM, Multi-task VLM)

- **역할**: Multi-task VLM (OCR, 테이블 인식, 수식 인식)
- **런타임**: vLLM OpenAI-compatible API
- **입력**: 태스크 프롬프트 (`"OCR:"`, `"Table Recognition:"`) + 이미지
- **출력**: 텍스트 (프롬프트에 따라 형식 변동)

**DocIR 매핑**:

| 모델 출력 | DocIR 필드 |
| --------- | ---------- |
| 텍스트 응답 | `ElementIR(kind='text_block', geometry=None, text=...)` |
| 구조화 테이블 | `ElementIR(kind='table', text=...)` |
| 프롬프트 정보 | `PageIR.meta['prompt']` |

**vLLM 서빙**:

```bash
vllm serve PaddlePaddle/PaddleOCR-VL \
    --trust-remote-code \
    --max-num-batched-tokens 16384 \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0
```

### 4.4. PaddlePaddle/PP-DocLayoutV3 (로컬, Layout Detection)

- **역할**: Layout Detection (bbox + 카테고리만, 텍스트 없음)
- **런타임**: 로컬 PyTorch (safetensors)
- **입력**: 이미지
- **출력**: `[{cls_id, label, score, coordinate: [x1,y1,x2,y2]}]`
- **카테고리**: 23종 (document_title, paragraph_title, text, table,
  image, formula, header, footer, page_number, footnote, seal 등)

**DocIR 매핑**:

| 모델 출력 | DocIR 필드 |
| --------- | ---------- |
| `label` | `ElementIR.kind` (매핑 테이블로 변환) |
| `coordinate` | `Geometry.bbox` (pixel) |
| `score` | `scores["det"]` |
| 원본 label | `tags["model_label"]` |

**라벨 매핑 테이블** (일부):

| PP-DocLayoutV3 label | ElementIR kind |
| -------------------- | -------------- |
| `document_title` | `title` |
| `paragraph_title` | `title` |
| `text` | `text_block` |
| `table` | `table` |
| `image` | `figure` |
| `formula` | `equation` |
| `header` | `header` |
| `footer` | `footer` |
| `page_number` | `page_number` |
| 기타 | `unknown` |

### 4.5. ibm-granite/granite-docling-258M (로컬, Layout Detection)

- **역할**: 문서 레이아웃 감지 (기존 구현)
- **런타임**: 로컬 PyTorch
- **입력**: 이미지
- **출력**: `list[LayoutRegion(bbox, category, score, text)]`
- **split_pipeline**의 기본 layout detector

**DocIR 매핑**: `LayoutRegion` → `ElementIR` 직접 변환.
`LayoutRegion.text`가 있으면 `ElementIR.text`에 포함.

### 4.6. allenai/olmOCR-2-7B-1025 (vLLM, Text Extractor)

- **역할**: 크롭 이미지에서 텍스트 추출 (split_pipeline 2단계)
- **런타임**: vLLM OpenAI-compatible API
- **입력**: category별 프롬프트 + 크롭 이미지
- **출력**: 텍스트 문자열

**DocIR 매핑**: `RecognitionResult`로 변환 후 merge 단계에서 ElementIR에 주입.

### 4.7. Gemini API (Cloud, Full-page/Crop OCR)

- **역할**: Full-page OCR 또는 크롭 텍스트 추출
- **런타임**: Google Cloud API
- **입력**: 구조화 프롬프트 + 이미지
- **출력**: JSON 배열 (Chandra와 동일 형식) 또는 텍스트

**DocIR 매핑**: Chandra와 동일 (JSON → ElementIR).
API 파라미터는 `PageIR.meta`에 보존.

**Adapter 마이그레이션 설계**:

Gemini는 Chandra와 **동일한 `STRUCTURED_OCR_PROMPT`**를 사용하고
동일한 JSON 배열 형식을 출력한다. 따라서 `parse_response()` 로직은 공유 가능하다.

다만 API 호출 형식이 다르다:

| | vLLM (OpenAI-compatible) | Gemini REST API |
| --- | --- | --- |
| 엔드포인트 | `/v1/chat/completions` | `/v1beta/models/{model}:generateContent` |
| 메시지 형식 | `messages[{role, content}]` | `contents[{parts[{text, inline_data}]}]` |
| 인증 | 없음 (로컬) | API key (query param) |

이 차이는 **Provider 레이어**에서 흡수한다:

```mermaid
flowchart TD
    subgraph vLLM["vLLM 엔진"]
        VP["VllmProvider: OpenAI chat/completions"] --> CA["ChandraAdapter: parse_response()"]
    end

    subgraph Gemini["Gemini 엔진 (향후)"]
        GP["GeminiProvider: Gemini REST API"] --> GA["GeminiAdapter: parse_response()"]
    end

    CA --> PIR1["PageIR"]
    GA --> PIR2["PageIR"]

    PIR1 --> EX["Exporter"]
    PIR2 --> EX
```

`GeminiAdapter.parse_response()`는 Gemini 응답(`candidates[0].content.parts[0].text`)에서
JSON을 추출하는 부분만 다르고, JSON → PageIR 변환은 ChandraAdapter와 공유할 수 있다.
`build_messages()`는 Gemini REST API 형식에 맞게 별도 구현한다.

> **마이그레이션 시점**: PR 1\~3에서 vLLM 엔진을 먼저 Adapter 패턴으로 전환한 후,
> 별도 PR에서 CommercialApiEngine(Gemini)을 마이그레이션한다.

## 5. 파이프라인 모드

### 5.1. FullPageEngine

하나의 모델이 레이아웃 + 텍스트를 한번에 처리:

```mermaid
flowchart LR
    VP["VllmProvider (HTTP 호출)"]
    MA["ModelAdapter (raw → DocIR)"]
    PIR["PageIR"]
    EX["Exporter"]
    OUT["OmniDocBench dict"]

    VP --> MA --> PIR --> EX --> OUT
```

**적용 모델**: Chandra, LightOnOCR, PaddleOCR-VL, Gemini

### 5.2. SplitPipelineEngine

레이아웃 감지와 텍스트 추출을 분리:

```mermaid
flowchart TD
    LP["LayoutProvider (Docling / PP-DocLayoutV3)"]
    DPIR["Detection PageIR (text = None)"]
    CROP["영역 크롭"]
    TP["TextProvider (olmOCR / Gemini)"]
    RR["RecognitionResult (element_id, text)"]
    MERGE["Merge: element_id로 text 주입"]
    FPIR["Final PageIR"]
    EX["Exporter"]
    OUT["OmniDocBench dict"]

    LP --> DPIR
    DPIR --> CROP
    CROP --> TP
    TP --> RR
    DPIR --> MERGE
    RR --> MERGE
    MERGE --> FPIR
    FPIR --> EX --> OUT
```

**적용 모델**: Docling + olmOCR, PP-DocLayoutV3 + Gemini 등 조합

## 6. 컴포넌트 인터페이스

### ModelAdapter Protocol

```python
from typing import Any, Protocol

class ModelAdapter(Protocol):
    """모델별 프롬프트 생성 및 응답 파싱."""

    def build_messages(
        self,
        image_b64: str,
        mime_type: str,
        page_width: int,
        page_height: int,
    ) -> list[dict[str, Any]]:
        """OpenAI chat completions 형식의 messages 리스트 생성."""
        ...

    def parse_response(
        self,
        result: dict[str, Any],
        page_width: int,
        page_height: int,
    ) -> PageIR:
        """raw API 응답 → PageIR 변환."""
        ...
```

> **Note**: `build_messages()`는 OpenAI chat completions 형식을 반환한다.
> Gemini 등 비-OpenAI API는 자체 Provider에서 메시지 형식을 변환하거나,
> `build_messages()` 대신 Provider 고유의 요청 빌드 메서드를 사용한다.

### Adapter 자동 감지 (resolve_adapter)

```python
def resolve_adapter(model_name: str) -> ModelAdapter:
    """모델 이름에서 적절한 Adapter를 자동 선택."""
    lower = model_name.lower()
    if 'lightonocr' in lower or 'lighton' in lower:
        return LightOnOcrAdapter()
    if 'paddleocr-vl' in lower or 'paddleocr_vl' in lower:
        return PaddleOcrVlAdapter()
    # chandra, olmocr 등 기존 모델은 기본 Adapter
    return ChandraAdapter()
```

### OmniDocBench Exporter

```python
def export_page(page: PageIR) -> dict[str, Any]:
    """PageIR → OmniDocBench dict 변환.

    Returns:
        {'layout_dets': [...], 'page_attribute': {}, 'extra': {'relation': []}}
    """
```

### 기존 Protocol (변경 없음)

- `LayoutDetector` (`services/layout_types.py`): `detect_layout(image_path) -> list[LayoutRegion]`
- `TextOcrProvider` (`services/ocr_pipeline.py`): `extract_text(image_bytes, category_hint) -> str`

## 7. 새 모델 추가 가이드

### Full-page OCR 모델 추가

1. **Adapter 작성**: `services/adapters/{model_name}.py`
   - `ModelAdapter` Protocol 구현
   - `build_messages()`: 모델에 맞는 프롬프트 + 이미지 형식
   - `parse_response()`: raw 응답 → PageIR 변환

2. **resolver 등록**: `services/adapters/resolver.py`
   - `resolve_adapter()`에 모델 이름 패턴 추가

3. **테스트 작성**: `tests/services/adapters/test_{model_name}.py`
   - `build_messages()` 형식 검증
   - `parse_response()` 정상/엣지 케이스
   - `resolve_adapter()` 패턴 매칭

4. **문서 업데이트**: 이 파일의 모델 카탈로그(섹션 4)에 추가

### Layout Detection 모델 추가 (Split Pipeline)

1. **Detector 작성**: `services/{model_name}_service.py`
   - `LayoutDetector` Protocol 구현

2. **SplitPipelineEngine 연동**: layout_provider 선택지에 추가

3. **라벨 매핑 테이블**: 모델 카테고리 → ElementIR kind 매핑

## 8. 파일 구조

```text
saegim-backend/src/saegim/services/
├── docir.py                     # PageIR, ElementIR, Geometry, RecognitionResult
├── adapters/
│   ├── __init__.py
│   ├── base.py                  # ModelAdapter Protocol
│   ├── resolver.py              # resolve_adapter(model_name)
│   ├── chandra.py               # ChandraAdapter
│   ├── lightonocr.py            # LightOnOcrAdapter
│   └── paddleocr_vl.py          # PaddleOcrVlAdapter
├── exporters/
│   ├── __init__.py
│   └── omnidocbench.py          # export_page(PageIR) → dict
├── engines/
│   ├── base.py                  # BaseOCREngine (변경 없음)
│   ├── vllm_engine.py           # VllmEngine (adapter 주입)
│   ├── split_pipeline_engine.py # SplitPipelineEngine (DocIR 기반)
│   ├── commercial_api_engine.py # CommercialApiEngine (향후 마이그레이션)
│   ├── pdfminer_engine.py       # PdfminerEngine (DocIR 미적용, 변경 없음)
│   └── factory.py               # 엔진 팩토리
├── vllm_ocr_service.py          # VllmOcrProvider (adapter 사용)
├── gemini_ocr_service.py        # GeminiOcrProvider (향후 adapter 전환)
├── pp_doclayout_service.py      # PP-DocLayoutV3 detector
├── docling_layout_service.py    # Docling detector (기존)
├── extraction_service.py        # pdfminer 폴백 (PDF 직접 처리, DocIR 무관)
├── ocr_provider.py              # deprecated wrapper 유지
└── ...
```

## 9. 마이그레이션 계획

### PR 순서 및 의존성

```mermaid
flowchart TD
    PR0["PR 0: 설계 문서"]
    PR1["PR 1: DocIR + Exporter + ChandraAdapter"]
    PR2["PR 2: LightOnOCR Adapter + 기본값 변경"]
    PR3["PR 3: PaddleOCR-VL Adapter"]
    PR4["PR 4: PP-DocLayoutV3 + Split Pipeline DocIR"]

    PR0 --> PR1 --> PR2 --> PR3 --> PR4
```

### 하위 호환성 전략

- `engine_type='vllm'` 유지. 기존 설정은 그대로 동작한다.
- `resolve_adapter()`가 모델 이름으로 Adapter를 자동 선택하므로,
  기존 `datalab-to/chandra` 설정은 `ChandraAdapter`를 사용한다.
- 기존 `build_omnidocbench_page()`는 deprecated wrapper로 유지하고,
  내부에서 Exporter를 호출한다.
- Public API (`extract_page() → dict`)는 변경하지 않는다.
- pdfminer 폴백은 DocIR와 무관하게 기존 경로를 유지한다.
- Gemini(`CommercialApiEngine`)는 vLLM 마이그레이션 완료 후 별도 PR에서 전환한다.
