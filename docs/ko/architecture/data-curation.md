# Data Curation & 품질 관리

## 목표

레이블링 데이터셋의 다양성과 품질을 실시간으로 모니터링하고,
벤치마크로서의 대표성을 확보하기 위한 큐레이션 도구를 제공한다.

## 배경

벤치마크 데이터셋의 가치는 **다양성과 균형**에 달려 있다.
OmniDocBench가 9종 문서유형, 4종 레이아웃, 3종 언어를 커버하는 것도 이 때문이다.
레이블링 작업이 진행될수록 "어떤 유형이 부족한지", "분포가 편향되지 않았는지"를
파악하는 것이 데이터셋 품질에 직결된다.

## 활용 가능한 기존 데이터

현재 `annotation_data` JSONB에 이미 풍부한 메타데이터가 존재한다:

| 필드 | 위치 | 분석 용도 |
| ------ | ------ | ----------- |
| `page_attribute.data_source` | 페이지 속성 | 문서 유형 분포 |
| `page_attribute.language` | 페이지 속성 | 언어 분포 |
| `page_attribute.layout` | 페이지 속성 | 레이아웃 유형 분포 |
| `layout_dets[].category_type` | 요소별 | 카테고리 분포 (15 Block + 4 Span) |
| `layout_dets[].attribute` | 요소별 | 속성 완성도 |
| `page_info.width/height` | 페이지 | 해상도 분포 |
| `pages.status` | 페이지 | 작업 진행률 |

## 구현 단계

### 4-A: 분포 대시보드

**목표**: 프로젝트 내 데이터 분포를 시각화한다.

#### 백엔드 API

| Method | Path | 설명 |
| -------- | ------ | ------ |
| `GET` | `/api/v1/projects/:id/stats/overview` | 전체 요약 통계 |
| `GET` | `/api/v1/projects/:id/stats/distribution` | 속성별 분포 |
| `GET` | `/api/v1/projects/:id/stats/progress` | 작업 진행률 |

#### 쿼리 예시

```sql
-- 문서 유형별 페이지 수
SELECT
    annotation_data->'page_attribute'->>'data_source' AS data_source,
    COUNT(*) AS page_count
FROM pages p
JOIN documents d ON p.document_id = d.id
WHERE d.project_id = $1
    AND annotation_data->'page_attribute'->>'data_source' IS NOT NULL
GROUP BY data_source
ORDER BY page_count DESC;

-- 카테고리별 요소 수
SELECT
    elem->>'category_type' AS category,
    COUNT(*) AS element_count
FROM pages p
JOIN documents d ON p.document_id = d.id,
    jsonb_array_elements(p.annotation_data->'layout_dets') AS elem
WHERE d.project_id = $1
GROUP BY category
ORDER BY element_count DESC;
```

#### 프론트엔드 차트

| 차트 | 데이터 | 라이브러리 |
| ------ | -------- | ------------ |
| 도넛 차트 | 문서 유형 / 언어 / 레이아웃 분포 | Chart.js 또는 Layerchart |
| 막대 차트 | 카테고리별 요소 수 | Chart.js 또는 Layerchart |
| 진행률 바 | 페이지 상태별 비율 | Tailwind CSS |
| 히트맵 | 문서유형 × 레이아웃 교차 분포 | Chart.js 또는 Layerchart |

### 4-B: 다양성 스코어 및 큐레이션 조언

**목표**: 목표 분포 대비 현재 커버리지를 점수화하고, 부족한 영역을 추천한다.

#### 다양성 스코어 산출

```text
목표 분포 (예시):
  data_source: {academic_paper: 30%, government_doc: 20%, textbook: 15%, ...}
  language: {ko: 60%, en: 20%, ko_en_mixed: 20%}
  layout: {single_column: 40%, double_column: 30%, three_column: 10%, ...}

다양성 스코어 = 1 - Σ |목표비율 - 실제비율| / 2
  → 0.0 (완전 편향) ~ 1.0 (목표와 완벽 일치)
```

#### 큐레이션 조언 규칙

| 조건 | 조언 |
| ------ | ------ |
| 특정 유형이 목표 대비 50% 미만 | "X 유형 문서를 더 추가하세요" |
| 특정 카테고리 요소가 전체의 1% 미만 | "Y 카테고리 샘플이 부족합니다" |
| 단일 유형이 전체의 60% 초과 | "Z 유형이 과대 대표되고 있습니다" |

#### API

| Method | Path | 설명 |
| -------- | ------ | ------ |
| `GET` | `/api/v1/projects/:id/curation/score` | 다양성 스코어 |
| `GET` | `/api/v1/projects/:id/curation/recommendations` | 큐레이션 조언 |
| `PUT` | `/api/v1/projects/:id/curation/targets` | 목표 분포 설정 |

### 4-C: 어노테이션 품질 지표

**목표**: 레이블링 완성도와 일관성을 정량화한다.

#### 지표

| 지표 | 산출 방법 |
| ------ | ----------- |
| 요소 밀도 | 페이지당 평균 `layout_dets` 수 |
| 텍스트 완성도 | `text` 필드가 비어있지 않은 요소 비율 |
| 속성 완성도 | `attribute` 필드가 설정된 요소 비율 |
| 페이지 속성 완성도 | `page_attribute` 필수 필드 채워진 비율 |
| 이상치 탐지 | bbox 면적이 극단적으로 크거나 작은 요소 |

### 4-D: Inter-Annotator Agreement (Phase 3 의존)

**목표**: 동일 페이지에 대한 복수 어노테이터의 일치도를 측정한다.

멀티유저 환경이 구축된 후에만 가능하다.

#### 측정 방법

| 방법 | 대상 | 설명 |
| ------ | ------ | ------ |
| Cohen's Kappa | 카테고리 분류 | 2명의 어노테이터 간 카테고리 일치도 |
| IoU (Intersection over Union) | 바운딩 박스 | bbox 위치/크기 일치도 |
| Edit Distance | OCR 텍스트 | 텍스트 인식 결과 일치도 |

#### 워크플로우

```text
1. 동일 페이지를 2명 이상에게 독립적으로 할당
2. 각자 레이블링 완료 후 제출
3. IAA 점수 자동 산출
4. 불일치 영역을 reviewer가 최종 판정
```

## 리스크

| 리스크 | 완화 |
| -------- | ------ |
| JSONB 집계 쿼리 성능 | GIN 인덱스 활용 (이미 존재), 캐싱 |
| 목표 분포 설정의 주관성 | OmniDocBench 분포를 기본값으로 제공 |
| IAA 구현 복잡도 | 4-D는 최후 순위, 기본 IoU부터 시작 |

## 선행 조건

- 4-A~C: Phase 2 (자동 추출) 완료, 충분한 어노테이션 데이터 축적
- 4-D: Phase 3 (멀티유저 협업) 완료
