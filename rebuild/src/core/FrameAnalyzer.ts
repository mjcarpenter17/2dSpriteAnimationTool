// Basic FrameAnalyzer: computes trim (tight bounding box of non-transparent pixels)
// and pivot strategies. Image data should be provided as Uint8ClampedArray RGBA.

export interface TrimBox { x: number; y: number; w: number; h: number; }
export type PivotStrategy = 'bottom-center' | 'center' | 'top-left' | 'top-right';
export interface PivotPoint { x: number; y: number; }

export class FrameAnalyzer {
  static computeTrim(
    pixels: Uint8ClampedArray,
    frameWidth: number,
    frameHeight: number,
    strideWidth: number,
    originX: number,
    originY: number,
    alphaThreshold = 1
  ): TrimBox | null {
    let minX = frameWidth, minY = frameHeight, maxX = -1, maxY = -1;
    for (let y = 0; y < frameHeight; y++) {
      for (let x = 0; x < frameWidth; x++) {
        const globalX = originX + x;
        const globalY = originY + y;
        const idx = (globalY * strideWidth + globalX) * 4 + 3; // alpha channel
        if (pixels[idx] >= alphaThreshold) {
          if (x < minX) minX = x;
          if (y < minY) minY = y;
          if (x > maxX) maxX = x;
          if (y > maxY) maxY = y;
        }
      }
    }
    if (maxX === -1) return null; // fully transparent
    return { x: originX + minX, y: originY + minY, w: maxX - minX + 1, h: maxY - minY + 1 };
  }

  static computePivot(trim: TrimBox | null, strategy: PivotStrategy, fallbackFrame: { x: number; y: number; w: number; h: number }): PivotPoint {
    const box = trim ?? fallbackFrame;
    switch (strategy) {
      case 'bottom-center':
        return { x: box.x + box.w / 2, y: box.y + box.h }; // bottom center on baseline
      case 'center':
        return { x: box.x + box.w / 2, y: box.y + box.h / 2 };
      case 'top-left':
        return { x: box.x, y: box.y };
      case 'top-right':
        return { x: box.x + box.w, y: box.y };
      default:
        return { x: box.x + box.w / 2, y: box.y + box.h };
    }
  }
}
