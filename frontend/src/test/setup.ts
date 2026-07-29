import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

function createMockCanvasContext(): CanvasRenderingContext2D {
  const noop = () => undefined;
  return {
    canvas: document.createElement("canvas"),
    clearRect: noop,
    fillRect: noop,
    strokeRect: noop,
    fillText: noop,
    strokeText: noop,
    measureText: () => ({ width: 0 }) as TextMetrics,
    beginPath: noop,
    closePath: noop,
    moveTo: noop,
    lineTo: noop,
    stroke: noop,
    fill: noop,
    save: noop,
    restore: noop,
    translate: noop,
    scale: noop,
    rotate: noop,
    arc: noop,
    rect: noop,
    clip: noop,
    setLineDash: noop,
    getLineDash: () => [],
    createLinearGradient: () =>
      ({ addColorStop: noop }) as CanvasGradient,
    createRadialGradient: () =>
      ({ addColorStop: noop }) as CanvasGradient,
    drawImage: noop,
    getImageData: () =>
      ({ data: new Uint8ClampedArray(4), width: 1, height: 1 }) as ImageData,
    putImageData: noop,
    setTransform: noop,
    resetTransform: noop,
    transform: noop,
    isPointInPath: () => false,
    globalAlpha: 1,
    globalCompositeOperation: "source-over",
    fillStyle: "#000",
    strokeStyle: "#000",
    lineWidth: 1,
    lineCap: "butt",
    lineJoin: "miter",
    miterLimit: 10,
    font: "10px sans-serif",
    textAlign: "start",
    textBaseline: "alphabetic",
  } as unknown as CanvasRenderingContext2D;
}

HTMLCanvasElement.prototype.getContext = vi.fn().mockImplementation(
  (type: string) => {
    if (type === "2d") {
      return createMockCanvasContext();
    }
    return null;
  },
) as typeof HTMLCanvasElement.prototype.getContext;

if (typeof globalThis.Path2D === "undefined") {
  class Path2DStub {
    addPath() {
      return undefined;
    }
    closePath() {
      return undefined;
    }
    moveTo() {
      return undefined;
    }
    lineTo() {
      return undefined;
    }
    bezierCurveTo() {
      return undefined;
    }
    quadraticCurveTo() {
      return undefined;
    }
    arc() {
      return undefined;
    }
    arcTo() {
      return undefined;
    }
    ellipse() {
      return undefined;
    }
    rect() {
      return undefined;
    }
  }
  globalThis.Path2D = Path2DStub as unknown as typeof Path2D;
}

afterEach(() => {
  cleanup();
});
