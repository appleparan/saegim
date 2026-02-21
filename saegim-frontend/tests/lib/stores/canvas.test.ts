import { describe, it, expect, beforeEach } from "vitest";
import { canvasStore } from "$lib/stores/canvas.svelte";

describe("CanvasStore", () => {
  beforeEach(() => {
    canvasStore.setViewport(1, 0, 0);
    canvasStore.setImageDimensions(0, 0);
    canvasStore.setTool("select");
  });

  describe("setViewport", () => {
    it("updates scale, offsetX, and offsetY atomically", () => {
      canvasStore.setViewport(2.5, 100, 200);
      expect(canvasStore.scale).toBe(2.5);
      expect(canvasStore.offsetX).toBe(100);
      expect(canvasStore.offsetY).toBe(200);
    });

    it("clamps scale to MIN_SCALE (0.1)", () => {
      canvasStore.setViewport(0.01, 10, 20);
      expect(canvasStore.scale).toBe(0.1);
      expect(canvasStore.offsetX).toBe(10);
      expect(canvasStore.offsetY).toBe(20);
    });

    it("clamps scale to MAX_SCALE (10)", () => {
      canvasStore.setViewport(15, 10, 20);
      expect(canvasStore.scale).toBe(10);
      expect(canvasStore.offsetX).toBe(10);
      expect(canvasStore.offsetY).toBe(20);
    });

    it("allows negative offsets", () => {
      canvasStore.setViewport(1, -50, -100);
      expect(canvasStore.offsetX).toBe(-50);
      expect(canvasStore.offsetY).toBe(-100);
    });
  });

  describe("setScale", () => {
    it("clamps scale within bounds", () => {
      canvasStore.setScale(0.05);
      expect(canvasStore.scale).toBe(0.1);

      canvasStore.setScale(20);
      expect(canvasStore.scale).toBe(10);
    });

    it("sets valid scale", () => {
      canvasStore.setScale(3);
      expect(canvasStore.scale).toBe(3);
    });
  });

  describe("setOffset", () => {
    it("updates offset", () => {
      canvasStore.setOffset(50, 75);
      expect(canvasStore.offsetX).toBe(50);
      expect(canvasStore.offsetY).toBe(75);
    });
  });

  describe("resetView", () => {
    it("resets to default values", () => {
      canvasStore.setViewport(3, 100, 200);
      canvasStore.resetView();
      expect(canvasStore.scale).toBe(1);
      expect(canvasStore.offsetX).toBe(0);
      expect(canvasStore.offsetY).toBe(0);
    });
  });

  describe("zoomIn / zoomOut", () => {
    it("zoomIn multiplies scale by 1.2", () => {
      canvasStore.setScale(1);
      canvasStore.zoomIn();
      expect(canvasStore.scale).toBeCloseTo(1.2);
    });

    it("zoomOut divides scale by 1.2", () => {
      canvasStore.setScale(1);
      canvasStore.zoomOut();
      expect(canvasStore.scale).toBeCloseTo(1 / 1.2);
    });

    it("zoomIn is clamped at MAX_SCALE", () => {
      canvasStore.setScale(9.5);
      canvasStore.zoomIn();
      expect(canvasStore.scale).toBe(10);
    });

    it("zoomOut is clamped at MIN_SCALE", () => {
      canvasStore.setScale(0.11);
      canvasStore.zoomOut();
      expect(canvasStore.scale).toBe(0.1);
    });
  });

  describe("fitToContainer", () => {
    it("fits image to container with correct scale and centering", () => {
      canvasStore.setImageDimensions(1000, 2000);
      canvasStore.fitToContainer(500, 800);

      // scaleX = 500/1000 = 0.5, scaleY = 800/2000 = 0.4
      // fitScale = min(0.5, 0.4, 1) = 0.4
      expect(canvasStore.scale).toBeCloseTo(0.4);
      // offsetX = (500 - 1000 * 0.4) / 2 = (500 - 400) / 2 = 50
      expect(canvasStore.offsetX).toBeCloseTo(50);
      // offsetY = (800 - 2000 * 0.4) / 2 = (800 - 800) / 2 = 0
      expect(canvasStore.offsetY).toBeCloseTo(0);
    });

    it("caps scale at 1 (no upscale)", () => {
      canvasStore.setImageDimensions(200, 300);
      canvasStore.fitToContainer(1000, 1000);

      // scaleX = 5, scaleY = 3.33, min with 1 => 1
      expect(canvasStore.scale).toBe(1);
    });

    it("does nothing when image dimensions are zero", () => {
      canvasStore.setViewport(2, 100, 200);
      canvasStore.setImageDimensions(0, 0);
      canvasStore.fitToContainer(500, 500);

      // Should not change
      expect(canvasStore.scale).toBe(2);
      expect(canvasStore.offsetX).toBe(100);
      expect(canvasStore.offsetY).toBe(200);
    });

    it("centers small image in large container", () => {
      canvasStore.setImageDimensions(400, 400);
      canvasStore.fitToContainer(800, 600);

      // scaleX = 2, scaleY = 1.5, min with 1 => 1
      expect(canvasStore.scale).toBe(1);
      // offsetX = (800 - 400) / 2 = 200
      expect(canvasStore.offsetX).toBe(200);
      // offsetY = (600 - 400) / 2 = 100
      expect(canvasStore.offsetY).toBe(100);
    });
  });

  describe("setImageDimensions", () => {
    it("sets image dimensions and marks loaded", () => {
      canvasStore.setImageDimensions(1920, 1080);
      expect(canvasStore.imageWidth).toBe(1920);
      expect(canvasStore.imageHeight).toBe(1080);
      expect(canvasStore.imageLoaded).toBe(true);
    });
  });

  describe("viewport derived state", () => {
    it("reflects current scale and offset", () => {
      canvasStore.setViewport(2, 50, 75);
      expect(canvasStore.viewport).toEqual({
        scale: 2,
        offsetX: 50,
        offsetY: 75,
      });
    });
  });

  describe("setTool", () => {
    it("updates tool mode", () => {
      canvasStore.setTool("draw");
      expect(canvasStore.toolMode).toBe("draw");

      canvasStore.setTool("pan");
      expect(canvasStore.toolMode).toBe("pan");

      canvasStore.setTool("select");
      expect(canvasStore.toolMode).toBe("select");
    });
  });
});
