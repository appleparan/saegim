/**
 * Category types, attribute enums, and display labels for the labeling UI.
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
        label: 'Text Language',
        type: 'select',
        options: TEXT_LANGUAGES,
      },
      {
        key: 'text_background',
        label: 'Background',
        type: 'select',
        options: TEXT_BACKGROUNDS,
      },
      {
        key: 'text_rotate',
        label: 'Rotation',
        type: 'select',
        options: TEXT_ROTATIONS,
      },
    ],
    title: [
      {
        key: 'text_language',
        label: 'Text Language',
        type: 'select',
        options: TEXT_LANGUAGES,
      },
      {
        key: 'text_background',
        label: 'Background',
        type: 'select',
        options: TEXT_BACKGROUNDS,
      },
      {
        key: 'text_rotate',
        label: 'Rotation',
        type: 'select',
        options: TEXT_ROTATIONS,
      },
    ],
    table: [
      {
        key: 'table_layout',
        label: 'Table Orientation',
        type: 'select',
        options: TABLE_LAYOUTS,
      },
      { key: 'with_span', label: 'Merged Cells', type: 'toggle' },
      { key: 'line', label: 'Line Style', type: 'select', options: TABLE_LINES },
      {
        key: 'language',
        label: 'Table Language',
        type: 'select',
        options: TABLE_LANGUAGES,
      },
      { key: 'include_equation', label: 'Contains Formula', type: 'toggle' },
      { key: 'include_background', label: 'Contains Background', type: 'toggle' },
      { key: 'table_vertical', label: 'Vertical Rotation', type: 'toggle' },
    ],
    equation_isolated: [
      {
        key: 'formula_type',
        label: 'Formula Type',
        type: 'select',
        options: FORMULA_TYPES,
      },
      {
        key: 'equation_language',
        label: 'Formula Language',
        type: 'select',
        options: EQUATION_LANGUAGES,
      },
    ],
  }

// --- Labels for UI display ---

export const CATEGORY_LABELS: Record<BlockCategoryType, string> = {
  title: 'Title',
  text_block: 'Body Text',
  figure: 'Figure',
  figure_caption: 'Figure Caption',
  figure_footnote: 'Figure Footnote',
  table: 'Table',
  table_caption: 'Table Caption',
  table_footnote: 'Table Footnote',
  equation_isolated: 'Isolated Equation',
  equation_caption: 'Equation Number',
  header: 'Header',
  footer: 'Footer',
  page_number: 'Page Number',
  page_footnote: 'Page Footnote',
  abandon: 'Ignored Content',
  code_txt: 'Code Block',
  code_txt_caption: 'Code Caption',
  reference: 'Reference',
}

export const SPAN_LABELS: Record<SpanCategoryType, string> = {
  text_span: 'Text Line',
  equation_ignore: 'Ignored Equation',
  equation_inline: 'Inline Equation',
  footnote_mark: 'Footnote Mark',
}

/** Labels for page-level attribute values */
export const DATA_SOURCE_LABELS: Record<DataSource, string> = {
  academic_literature: 'Academic Literature',
  PPT2PDF: 'PPT → PDF',
  book: 'Book',
  colorful_textbook: 'Colorful Textbook',
  exam_paper: 'Exam Paper',
  note: 'Note',
  magazine: 'Magazine',
  research_report: 'Research Report',
  newspaper: 'Newspaper',
  government_doc: 'Government Document',
  financial_report_kr: 'Financial Report',
}

export const PAGE_LANGUAGE_LABELS: Record<PageLanguage, string> = {
  ko: 'Korean',
  en: 'English',
  ko_en_mixed: 'Korean-English Mixed',
  ko_ch_mixed: 'Korean-Chinese Mixed',
}

export const PAGE_LAYOUT_LABELS: Record<PageLayout, string> = {
  single_column: 'Single Column',
  double_column: 'Double Column',
  three_column: 'Three Columns',
  '1andmore_column': 'Mixed Columns',
  other_layout: 'Other',
}
