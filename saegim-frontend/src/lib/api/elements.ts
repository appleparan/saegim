/**
 * Element CRUD API calls.
 */

import { api } from "./client";
import type {
  CreateElementRequest,
  UpdateElementRequest,
  ElementResponse,
} from "./types";

export async function createElement(
  pageId: string,
  data: CreateElementRequest,
): Promise<ElementResponse> {
  return api.post<ElementResponse>(`/api/v1/pages/${pageId}/elements`, data);
}

export async function updateElement(
  elementId: string,
  data: UpdateElementRequest,
): Promise<void> {
  await api.put(`/api/v1/elements/${elementId}`, data);
}

export async function deleteElement(elementId: string): Promise<void> {
  await api.delete(`/api/v1/elements/${elementId}`);
}
