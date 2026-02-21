/**
 * Canvas viewport state management using Svelte 5 runes.
 */

import type { ToolMode, ViewportState } from "$lib/types/canvas";

const MIN_SCALE = 0.1;
const MAX_SCALE = 10;

class CanvasStore {
  toolMode = $state<ToolMode>("select");
  scale = $state(1);
  offsetX = $state(0);
  offsetY = $state(0);
  imageWidth = $state(0);
  imageHeight = $state(0);
  imageLoaded = $state(false);

  viewport = $derived<ViewportState>({
    scale: this.scale,
    offsetX: this.offsetX,
    offsetY: this.offsetY,
  });

  setTool(mode: ToolMode): void {
    this.toolMode = mode;
  }

  setScale(scale: number): void {
    this.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale));
  }

  setOffset(x: number, y: number): void {
    this.offsetX = x;
    this.offsetY = y;
  }

  /** Atomically update scale and offset to avoid intermediate desync. */
  setViewport(scale: number, offsetX: number, offsetY: number): void {
    this.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale));
    this.offsetX = offsetX;
    this.offsetY = offsetY;
  }

  resetView(): void {
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;
  }

  setImageDimensions(width: number, height: number): void {
    this.imageWidth = width;
    this.imageHeight = height;
    this.imageLoaded = true;
  }

  zoomIn(): void {
    this.setScale(this.scale * 1.2);
  }

  zoomOut(): void {
    this.setScale(this.scale / 1.2);
  }

  fitToContainer(containerWidth: number, containerHeight: number): void {
    if (this.imageWidth === 0 || this.imageHeight === 0) return;

    const scaleX = containerWidth / this.imageWidth;
    const scaleY = containerHeight / this.imageHeight;
    const fitScale = Math.min(scaleX, scaleY, 1);

    this.setViewport(
      fitScale,
      (containerWidth - this.imageWidth * fitScale) / 2,
      (containerHeight - this.imageHeight * fitScale) / 2,
    );
  }
}

export const canvasStore = new CanvasStore();
