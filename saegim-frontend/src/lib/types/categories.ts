/**
 * Category types, attribute enums, and Korean labels for the labeling UI.
 */

// --- Block-level categories (18 types) ---

export const BLOCK_CATEGORIES = [
  'title',
  'text_block',
  'figure',
  'figure_caption',
  'figure_footnote',
  'table',
  'table_caption',
  'table_footnote',
  'equation_isolated',
  'equation_caption',
  'header',
  'footer',
  'page_number',
  'page_footnote',
  'abandon',
  'code_txt',
  'code_txt_caption',
  'reference',
] as const

export type BlockCategoryType = (typeof BLOCK_CATEGORIES)[number]

// --- Span-level categories (4 types) ---

export const SPAN_CATEGORIES = [
  'text_span',
  'equation_ignore',
  'equation_inline',
  'footnote_mark',
] as const

export type SpanCategoryType = (typeof SPAN_CATEGORIES)[number]

// --- Page-level attribute values ---

export const DATA_SOURCES = [
  'academic_literature',
  'PPT2PDF',
  'book',
  'colorful_textbook',
  'exam_paper',
  'note',
  'magazine',
  'research_report',
  'newspaper',
  'government_doc',
  'financial_report_kr',
] as const
export type DataSource = (typeof DATA_SOURCES)[number]

export const PAGE_LANGUAGES = ['ko', 'en', 'ko_en_mixed', 'ko_ch_mixed'] as const
export type PageLanguage = (typeof PAGE_LANGUAGES)[number]

export const PAGE_LAYOUTS = [
  'single_column',
  'double_column',
  'three_column',
  '1andmore_column',
  'other_layout',
] as const
export type PageLayout = (typeof PAGE_LAYOUTS)[number]

// --- Table attribute values ---

export const TABLE_LAYOUTS = ['vertical', 'horizontal'] as const
export type TableLayout = (typeof TABLE_LAYOUTS)[number]

export const TABLE_LINES = ['full_line', 'less_line', 'fewer_line', 'wireless_line'] as const
export type TableLine = (typeof TABLE_LINES)[number]

export const TABLE_LANGUAGES = ['table_ko', 'table_en', 'table_ko_en_mixed'] as const
export type TableLanguage = (typeof TABLE_LANGUAGES)[number]

// --- Text attribute values ---

export const TEXT_LANGUAGES = ['text_ko', 'text_en', 'text_ko_en_mixed'] as const
export type TextLanguage = (typeof TEXT_LANGUAGES)[number]

export const TEXT_BACKGROUNDS = ['white', 'single_colored', 'multi_colored'] as const
export type TextBackground = (typeof TEXT_BACKGROUNDS)[number]

export const TEXT_ROTATIONS = [
  'normal',
  'rotate90',
  'rotate180',
  'rotate270',
  'horizontal',
] as const
export type TextRotation = (typeof TEXT_ROTATIONS)[number]

// --- Formula attribute values ---

export const FORMULA_TYPES = ['print', 'handwriting'] as const
export type FormulaType = (typeof FORMULA_TYPES)[number]

export const EQUATION_LANGUAGES = ['equation_ko', 'equation_en'] as const
export type EquationLanguage = (typeof EQUATION_LANGUAGES)[number]

// --- Category to attribute mapping ---

export interface AttributeFieldDef {
  readonly key: string
  readonly label: string
  readonly type: 'select' | 'toggle'
  readonly options?: readonly string[]
}

/** Attribute fields applicable to each category */
export const CATEGORY_ATTRIBUTES: Partial<Record<BlockCategoryType, readonly AttributeFieldDef[]>> =
  {
    text_block: [
      {
        key: 'text_language',
        label: '텍스트 언어',
        type: 'select',
        options: TEXT_LANGUAGES,
      },
      {
        key: 'text_background',
        label: '배경',
        type: 'select',
        options: TEXT_BACKGROUNDS,
      },
      {
        key: 'text_rotate',
        label: '회전',
        type: 'select',
        options: TEXT_ROTATIONS,
      },
    ],
    title: [
      {
        key: 'text_language',
        label: '텍스트 언어',
        type: 'select',
        options: TEXT_LANGUAGES,
      },
      {
        key: 'text_background',
        label: '배경',
        type: 'select',
        options: TEXT_BACKGROUNDS,
      },
      {
        key: 'text_rotate',
        label: '회전',
        type: 'select',
        options: TEXT_ROTATIONS,
      },
    ],
    table: [
      {
        key: 'table_layout',
        label: '테이블 방향',
        type: 'select',
        options: TABLE_LAYOUTS,
      },
      { key: 'with_span', label: '병합 셀', type: 'toggle' },
      { key: 'line', label: '선 스타일', type: 'select', options: TABLE_LINES },
      {
        key: 'language',
        label: '테이블 언어',
        type: 'select',
        options: TABLE_LANGUAGES,
      },
      { key: 'include_equation', label: '수식 포함', type: 'toggle' },
      { key: 'include_background', label: '배경 포함', type: 'toggle' },
      { key: 'table_vertical', label: '세로 회전', type: 'toggle' },
    ],
    equation_isolated: [
      {
        key: 'formula_type',
        label: '수식 유형',
        type: 'select',
        options: FORMULA_TYPES,
      },
      {
        key: 'equation_language',
        label: '수식 언어',
        type: 'select',
        options: EQUATION_LANGUAGES,
      },
    ],
  }

// --- Korean labels for UI display ---

export const CATEGORY_LABELS: Record<BlockCategoryType, string> = {
  title: '제목',
  text_block: '본문 텍스트',
  figure: '그림',
  figure_caption: '그림 설명',
  figure_footnote: '그림 주석',
  table: '테이블',
  table_caption: '테이블 설명',
  table_footnote: '테이블 주석',
  equation_isolated: '별행 수식',
  equation_caption: '수식 번호',
  header: '머리글',
  footer: '바닥글',
  page_number: '페이지 번호',
  page_footnote: '페이지 각주',
  abandon: '무시 대상',
  code_txt: '코드 블록',
  code_txt_caption: '코드 설명',
  reference: '참고문헌',
}

export const SPAN_LABELS: Record<SpanCategoryType, string> = {
  text_span: '텍스트 라인',
  equation_ignore: '무시할 수식',
  equation_inline: '인라인 수식',
  footnote_mark: '각주 마크',
}

/** Korean labels for page-level attribute values */
export const DATA_SOURCE_LABELS: Record<DataSource, string> = {
  academic_literature: '학술 논문',
  PPT2PDF: 'PPT → PDF',
  book: '도서',
  colorful_textbook: '컬러 교과서',
  exam_paper: '시험지',
  note: '노트',
  magazine: '잡지',
  research_report: '연구 보고서',
  newspaper: '신문',
  government_doc: '공문서',
  financial_report_kr: '재무보고서',
}

export const PAGE_LANGUAGE_LABELS: Record<PageLanguage, string> = {
  ko: '한국어',
  en: '영어',
  ko_en_mixed: '한영 혼합',
  ko_ch_mixed: '한중 혼합',
}

export const PAGE_LAYOUT_LABELS: Record<PageLayout, string> = {
  single_column: '단일 열',
  double_column: '이중 열',
  three_column: '삼중 열',
  '1andmore_column': '복합 열',
  other_layout: '기타',
}
