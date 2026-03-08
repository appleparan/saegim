# Output Data Schema (Based on OmniDocBench)

The labeling output is a JSON structured in the following 3 layers.

## Dataset Format (JSON Structure)

```text
Per-page JSON array. Each page contains:
├── layout_dets[]          # List of elements within the page
│   ├── category_type      # Evaluation Category (see below)
│   ├── poly[8]            # 4-vertex coordinates (x1,y1,...,x4,y4)
│   ├── ignore             # Whether to ignore during evaluation
│   ├── order              # Reading order
│   ├── anno_id            # Unique ID
│   ├── text               # OCR text (optional)
│   ├── latex              # LaTeX (formula/table, optional)
│   ├── html               # HTML (table, optional)
│   ├── attribute{}        # Attribute Labels (see below)
│   ├── line_with_spans[]  # Span-level sub-elements
│   └── merge_list[]       # Merged relation elements
├── page_info{}
│   ├── page_no, height, width, image_path
│   └── page_attribute{}   # Page attribute labels
└── extra{}
    └── relation[]         # Inter-element relations (caption-body, etc.)
```

## Evaluation Categories

### Block-level (15 types)

| Category | Description | Korean Document Reference |
| --------- | ------ | ---------------- |
| title | Title | Paper title, chapter/section headings |
| text_block | Body text paragraph | General text |
| figure | Figure/image | Charts, photos |
| figure_caption | Figure caption | "Figure 1. ..." |
| figure_footnote | Figure footnote | Additional description below figure |
| table | Table body | Table |
| table_caption | Table caption | "Table 1. ..." |
| table_footnote | Table footnote | Additional description below table |
| equation_isolated | Display equation | Standalone equation |
| equation_caption | Equation number | "(1)", "(2.3)", etc. |
| header | Header | Top of page |
| footer | Footer | Bottom of page |
| page_number | Page number | |
| page_footnote | Page footnote | Footnotes at bottom of body |
| abandon | Ignore target | Ads, watermark text, etc. |
| code_txt | Code block | Programming code |
| code_txt_caption | Code caption | |
| reference | References | Reference list at end of paper |

### Span-level (4 types)

| Category | Description |
| --------- | ------ |
| text_span | Text line unit |
| equation_ignore | Equation to ignore |
| equation_inline | Inline equation |
| footnote_mark | Superscript/subscript mark |

## Attribute Labels

### Page Attributes (Page-level)

| Attribute | Values | Korean Extension Proposal |
| ------ | ----- | ----------------- |
| data_source | academic_literature, PPT2PDF, book, colorful_textbook, exam_paper, note, magazine, research_report, newspaper | + `government_doc` (official documents), `financial_report_kr` (Korean financial reports) |
| language | en, simplified_chinese, en_ch_mixed | Change to `ko`, `en`, `ko_en_mixed`, `ko_ch_mixed` |
| layout | single_column, double_column, three_column, 1andmore_column, other_layout | Use as-is |
| watermark | true / false | Same |
| fuzzy_scan | true / false | Same |
| colorful_background | true / false | Same |

### Table Attributes (Block-level: Table)

| Attribute | Values |
| ------ | ----- |
| table_layout | vertical / horizontal |
| with_span | True / False (presence of merged cells) |
| line | full_line / less_line / fewer_line / wireless_line |
| language | table_ko / table_en / table_ko_en_mixed |
| include_equation | True / False |
| include_background | True / False |
| table_vertical | True / False (90/270 degree rotation) |

### Text Attributes (Block-level: Text)

| Attribute | Values |
| ------ | ----- |
| text_language | text_ko / text_en / text_ko_en_mixed |
| text_background | white / single_colored / multi_colored |
| text_rotate | normal / rotate90 / rotate180 / rotate270 / horizontal |

### Formula Attributes (Block-level: Formula)

| Attribute | Values |
| ------ | ----- |
| formula_type | print / handwriting |
| equation_language | equation_ko / equation_en |
