# 출력 데이터 스키마 (OmniDocBench 기반)

레이블링 결과물은 아래 3가지 계층으로 구성된 JSON을 최종 출력한다.

## Dataset Format (JSON 구조)

```text
페이지 단위 JSON 배열. 각 페이지는:
├── layout_dets[]          # 페이지 내 요소 리스트
│   ├── category_type      # Evaluation Category (아래 참조)
│   ├── poly[8]            # 4꼭짓점 좌표 (x1,y1,...,x4,y4)
│   ├── ignore             # 평가 시 무시 여부
│   ├── order              # 읽기 순서
│   ├── anno_id            # 고유 ID
│   ├── text               # OCR 텍스트 (선택)
│   ├── latex              # LaTeX (수식/테이블, 선택)
│   ├── html               # HTML (테이블, 선택)
│   ├── attribute{}        # Attribute Labels (아래 참조)
│   ├── line_with_spans[]  # Span-level 하위 요소
│   └── merge_list[]       # 병합 관계 요소
├── page_info{}
│   ├── page_no, height, width, image_path
│   └── page_attribute{}   # 페이지 속성 라벨
└── extra{}
    └── relation[]         # 요소 간 관계 (캡션-본체 등)
```

## Evaluation Categories

### Block-level (15종)

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

### Span-level (4종)

| 카테고리 | 설명 |
| --------- | ------ |
| text_span | 텍스트 라인 단위 |
| equation_ignore | 무시할 수식 |
| equation_inline | 인라인 수식 |
| footnote_mark | 위/아래첨자 마크 |

## Attribute Labels

### 페이지 속성 (Page-level)

| 속성 | 값 | 한국어 확장 제안 |
| ------ | ----- | ----------------- |
| data_source | academic_literature, PPT2PDF, book, colorful_textbook, exam_paper, note, magazine, research_report, newspaper | + `government_doc` (공문서), `financial_report_kr` (한국 재무보고서) |
| language | en, simplified_chinese, en_ch_mixed | → `ko`, `en`, `ko_en_mixed`, `ko_ch_mixed` 로 변경 |
| layout | single_column, double_column, three_column, 1andmore_column, other_layout | 동일 사용 |
| watermark | true / false | 동일 |
| fuzzy_scan | true / false | 동일 |
| colorful_background | true / false | 동일 |

### 테이블 속성 (Block-level: Table)

| 속성 | 값 |
| ------ | ----- |
| table_layout | vertical / horizontal |
| with_span | True / False (병합 셀 유무) |
| line | full_line / less_line / fewer_line / wireless_line |
| language | table_ko / table_en / table_ko_en_mixed |
| include_equation | True / False |
| include_background | True / False |
| table_vertical | True / False (90°/270° 회전) |

### 텍스트 속성 (Block-level: Text)

| 속성 | 값 |
| ------ | ----- |
| text_language | text_ko / text_en / text_ko_en_mixed |
| text_background | white / single_colored / multi_colored |
| text_rotate | normal / rotate90 / rotate180 / rotate270 / horizontal |

### 수식 속성 (Block-level: Formula)

| 속성 | 값 |
| ------ | ----- |
| formula_type | print / handwriting |
| equation_language | equation_ko / equation_en |
