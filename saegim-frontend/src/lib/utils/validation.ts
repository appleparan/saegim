/**
 * Annotation validation helpers.
 */

import type { AnnotationData, LayoutElement } from "$lib/types/omnidocbench";
import { BLOCK_CATEGORIES } from "$lib/types/categories";

export interface ValidationError {
  readonly elementId: number | null;
  readonly field: string;
  readonly message: string;
}

/** Validate a single layout element. */
export function validateElement(
  element: LayoutElement,
): readonly ValidationError[] {
  const errors: ValidationError[] = [];
  const id = element.anno_id;

  if (!BLOCK_CATEGORIES.includes(element.category_type)) {
    errors.push({
      elementId: id,
      field: "category_type",
      message: `Invalid category: ${element.category_type}`,
    });
  }

  if (element.poly.length !== 8) {
    errors.push({
      elementId: id,
      field: "poly",
      message: "Poly must have exactly 8 values (4 corners)",
    });
  }

  const hasNegativeCoords = element.poly.some((v) => v < 0);
  if (hasNegativeCoords) {
    errors.push({
      elementId: id,
      field: "poly",
      message: "Poly contains negative coordinates",
    });
  }

  return errors;
}

/** Validate complete annotation data. */
export function validateAnnotation(
  data: AnnotationData,
): readonly ValidationError[] {
  const errors: ValidationError[] = [];

  for (const element of data.layout_dets) {
    errors.push(...validateElement(element));
  }

  // Check for duplicate anno_ids
  const ids = data.layout_dets.map((e) => e.anno_id);
  const duplicates = ids.filter((id, i) => ids.indexOf(id) !== i);
  for (const dupId of new Set(duplicates)) {
    errors.push({
      elementId: dupId,
      field: "anno_id",
      message: `Duplicate anno_id: ${dupId}`,
    });
  }

  // Validate relations reference existing elements
  for (const rel of data.extra.relation) {
    if (!ids.includes(rel.source_anno_id)) {
      errors.push({
        elementId: null,
        field: "relation",
        message: `Relation source ${rel.source_anno_id} does not exist`,
      });
    }
    if (!ids.includes(rel.target_anno_id)) {
      errors.push({
        elementId: null,
        field: "relation",
        message: `Relation target ${rel.target_anno_id} does not exist`,
      });
    }
  }

  return errors;
}
