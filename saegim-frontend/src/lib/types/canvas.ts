/**
 * Canvas-related types for the image viewer and bbox editor.
 */

export interface Point {
  readonly x: number
  readonly y: number
}

export interface Rect {
  readonly x: number
  readonly y: number
  readonly width: number
  readonly height: number
}

export type ToolMode = 'select' | 'draw' | 'pan'

export interface ViewportState {
  readonly scale: number
  readonly offsetX: number
  readonly offsetY: number
}
