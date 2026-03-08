# Data Curation & Quality Management

## Goal

Provide curation tools to monitor the diversity and quality of labeling datasets in real-time,
ensuring representativeness as a benchmark.

## Background

The value of a benchmark dataset lies in its **diversity and balance**.
This is why OmniDocBench covers 9 document types, 4 layouts, and 3 languages.
As labeling work progresses, identifying "which types are lacking" and "whether the distribution is biased"
directly impacts dataset quality.

## Available Existing Data

Rich metadata already exists in the current `annotation_data` JSONB:

| Field | Location | Analysis Purpose |
| ------ | ------ | ----------- |
| `page_attribute.data_source` | Page attribute | Document type distribution |
| `page_attribute.language` | Page attribute | Language distribution |
| `page_attribute.layout` | Page attribute | Layout type distribution |
| `layout_dets[].category_type` | Per element | Category distribution (15 Block + 4 Span) |
| `layout_dets[].attribute` | Per element | Attribute completeness |
| `page_info.width/height` | Page | Resolution distribution |
| `pages.status` | Page | Work progress |

## Implementation Stages

### 4-A: Distribution Dashboard

**Goal**: Visualize data distribution within a project.

#### Backend API

| Method | Path | Description |
| -------- | ------ | ------ |
| `GET` | `/api/v1/projects/:id/stats/overview` | Overall summary statistics |
| `GET` | `/api/v1/projects/:id/stats/distribution` | Per-attribute distribution |
| `GET` | `/api/v1/projects/:id/stats/progress` | Work progress |

#### Query Examples

```sql
-- Page count by document type
SELECT
    annotation_data->'page_attribute'->>'data_source' AS data_source,
    COUNT(*) AS page_count
FROM pages p
JOIN documents d ON p.document_id = d.id
WHERE d.project_id = $1
    AND annotation_data->'page_attribute'->>'data_source' IS NOT NULL
GROUP BY data_source
ORDER BY page_count DESC;

-- Element count by category
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

#### Frontend Charts

| Chart | Data | Library |
| ------ | -------- | ------------ |
| Donut chart | Document type / language / layout distribution | Chart.js or Layerchart |
| Bar chart | Element count by category | Chart.js or Layerchart |
| Progress bar | Ratio by page status | Tailwind CSS |
| Heatmap | Document type x layout cross-distribution | Chart.js or Layerchart |

### 4-B: Diversity Score & Curation Recommendations

**Goal**: Score current coverage against target distributions and recommend areas that need more data.

#### Diversity Score Calculation

```text
Target distribution (example):
  data_source: {academic_paper: 30%, government_doc: 20%, textbook: 15%, ...}
  language: {ko: 60%, en: 20%, ko_en_mixed: 20%}
  layout: {single_column: 40%, double_column: 30%, three_column: 10%, ...}

Diversity score = 1 - sum(|target_ratio - actual_ratio|) / 2
  → 0.0 (completely biased) ~ 1.0 (perfect match with target)
```

#### Curation Recommendation Rules

| Condition | Recommendation |
| ------ | ------ |
| A specific type is below 50% of target | "Please add more X-type documents" |
| A specific category has less than 1% of total elements | "Y category samples are insufficient" |
| A single type exceeds 60% of total | "Z type is over-represented" |

#### API

| Method | Path | Description |
| -------- | ------ | ------ |
| `GET` | `/api/v1/projects/:id/curation/score` | Diversity score |
| `GET` | `/api/v1/projects/:id/curation/recommendations` | Curation recommendations |
| `PUT` | `/api/v1/projects/:id/curation/targets` | Set target distribution |

### 4-C: Annotation Quality Metrics

**Goal**: Quantify labeling completeness and consistency.

#### Metrics

| Metric | Calculation Method |
| ------ | ----------- |
| Element density | Average `layout_dets` count per page |
| Text completeness | Ratio of elements with non-empty `text` field |
| Attribute completeness | Ratio of elements with `attribute` field set |
| Page attribute completeness | Ratio of required `page_attribute` fields filled |
| Outlier detection | Elements with extremely large or small bbox area |

### 4-D: Inter-Annotator Agreement (Phase 3 Dependent)

**Goal**: Measure agreement between multiple annotators on the same page.

This is only possible after the multi-user environment is established.

#### Measurement Methods

| Method | Target | Description |
| ------ | ------ | ------ |
| Cohen's Kappa | Category classification | Category agreement between 2 annotators |
| IoU (Intersection over Union) | Bounding boxes | bbox position/size agreement |
| Edit Distance | OCR text | Text recognition result agreement |

#### Workflow

```text
1. Independently assign the same page to 2 or more annotators
2. Each completes labeling and submits
3. IAA score automatically calculated
4. Reviewer makes final judgment on disagreement areas
```

## Risks

| Risk | Mitigation |
| -------- | ------ |
| JSONB aggregate query performance | GIN index utilization (already exists), caching |
| Subjectivity of target distribution settings | Provide OmniDocBench distribution as defaults |
| IAA implementation complexity | 4-D is lowest priority, start with basic IoU |

## Prerequisites

- 4-A through 4-C: Phase 2 (automatic extraction) complete, sufficient annotation data accumulated
- 4-D: Phase 3 (multi-user collaboration) complete
