/**
 * OmniDocBench JSON type definitions.
 *
 * Matches the annotation_data JSONB structure stored in the backend's pages table.
 * All types use readonly to enforce immutability.
 */

import type { BlockCategoryType, SpanCategoryType } from "./categories";

/** 4-corner polygon: [x1, y1, x2, y2, x3, y3, x4, y4] */
export type Poly = readonly [
  number,
  number,
  number,
  number,
  number,
  number,
  number,
  number,
];

/** Span-level element within a block (e.g., text_span, equation_inline) */
export interface SpanElement {
  readonly category_type: SpanCategoryType;
  readonly poly: Poly;
  readonly ignore: boolean;
  readonly text?: string;
}

/** Element-level attribute labels, keyed by attribute name */
export type ElementAttribute = Readonly<Record<string, string | boolean>>;

/** Block-level layout element (e.g., title, text_block, table, figure) */
export interface LayoutElement {
  readonly category_type: BlockCategoryType;
  readonly poly: Poly;
  readonly ignore: boolean;
  readonly order: number;
  readonly anno_id: number;
  readonly text?: string;
  readonly latex?: string;
  readonly html?: string;
  readonly attribute?: ElementAttribute;
  readonly line_with_spans?: readonly SpanElement[];
  readonly merge_list?: readonly LayoutElement[];
}

/** Relation between two elements (e.g., figure <-> caption) */
export interface Relation {
  readonly source_anno_id: number;
  readonly target_anno_id: number;
  readonly relation_type: string;
}

/** Page-level attribute labels */
export interface PageAttribute {
  readonly data_source?: string;
  readonly language?: string;
  readonly layout?: string;
  readonly watermark?: boolean;
  readonly fuzzy_scan?: boolean;
  readonly colorful_background?: boolean;
}

/** Complete annotation data for a single page (OmniDocBench format) */
export interface AnnotationData {
  readonly layout_dets: readonly LayoutElement[];
  readonly page_attribute: PageAttribute;
  readonly extra: {
    readonly relation: readonly Relation[];
  };
}
