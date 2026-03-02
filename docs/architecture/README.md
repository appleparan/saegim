# 아키텍처 문서

saegim의 시스템 아키텍처를 구성 요소별로 설명한다.

## 전체 구조

```text
saegim
  ├── Frontend (Svelte 5 SPA)
  │     ├── 캔버스 에디터 (Konva.js)
  │     ├── PDF 렌더러 (PDF.js)
  │     └── OCR 설정 패널
  │
  ├── Backend (FastAPI)
  │     ├── REST API / asyncpg
  │     ├── OCR Engine Factory
  │     │     ├── DocIR 중간 표현
  │     │     ├── Adapter (모델별 파싱)
  │     │     └── Exporter (OmniDocBench 변환)
  │     └── 비동기 추출 태스크
  │
  └── 외부 서비스
        ├── PostgreSQL (JSONB)
        ├── vLLM 서버 (GPU)
        └── Gemini API (Cloud)
```

## 문서 목록

### 핵심 파이프라인

| 문서 | 설명 |
| ---- | ---- |
| [자동 추출 파이프라인](extraction-pipeline.md) | OCR 엔진 아키텍처, 엔진 타입별 흐름, `ocr_config` 구조 |
| [DocIR 아키텍처](docir-architecture.md) | 3-stage 파이프라인 (Provider-Adapter-Exporter), 중간 표현, 모델 카탈로그 |

### 데이터 및 레이블링

| 문서 | 설명 |
| ---- | ---- |
| [데이터 스키마](data-schema.md) | DB 테이블, JSONB 구조, OmniDocBench 포맷 |
| [레이블링 워크플로우](labeling-workflow.md) | 에디터 UI, 캔버스 레이어, 키보드 단축키 |
| [데이터 큐레이션](data-curation.md) | 데이터 검증, 품질 관리, 내보내기 |

### 운영

| 문서 | 설명 |
| ---- | ---- |
| [다중 사용자 협업](multi-user-collaboration.md) | 동시 편집, 충돌 해결, 권한 관리 |

## 읽는 순서

1. 전체 흐름을 이해하려면 [자동 추출 파이프라인](extraction-pipeline.md)부터 읽는다.
2. OCR 모델 추가/변경이 목적이면 [DocIR 아키텍처](docir-architecture.md)를 참고한다.
3. 데이터 구조를 파악하려면 [데이터 스키마](data-schema.md)를 읽는다.
4. 레이블링 UI를 수정하려면 [레이블링 워크플로우](labeling-workflow.md)를 읽는다.
