import { FrameAnalyzer } from '../src/core/FrameAnalyzer';

function makePixels(width: number, height: number, opaqueCoords: Array<[number, number]>): Uint8ClampedArray {
  const arr = new Uint8ClampedArray(width * height * 4);
  // all zero alpha by default
  for (const [x, y] of opaqueCoords) {
    const idx = (y * width + x) * 4;
    arr[idx] = 255; // r
    arr[idx + 1] = 255; // g
    arr[idx + 2] = 255; // b
    arr[idx + 3] = 255; // a
  }
  return arr;
}

describe('FrameAnalyzer', () => {
  test('fully transparent frame returns null trim', () => {
    const pixels = makePixels(32, 32, []);
    const trim = FrameAnalyzer.computeTrim(pixels, 16, 16, 32, 0, 0);
    expect(trim).toBeNull();
  });

  test('trim detects tight bounds', () => {
    // Opaque pixels at (2,3) and (7,10) within frame origin (0,0)
    const pixels = makePixels(32, 32, [ [2,3], [7,10] ]);
    const trim = FrameAnalyzer.computeTrim(pixels, 16, 16, 32, 0, 0);
    expect(trim).not.toBeNull();
    expect(trim!.x).toBe(2);
    expect(trim!.y).toBe(3);
    expect(trim!.w).toBe(7 - 2 + 1);
    expect(trim!.h).toBe(10 - 3 + 1);
  });

  test('pivot bottom-center strategy', () => {
    const trim = { x: 10, y: 20, w: 8, h: 12 };
    const pivot = FrameAnalyzer.computePivot(trim, 'bottom-center', { x:0,y:0,w:16,h:16 });
    expect(pivot.x).toBe(14); // 10 + 8/2
    expect(pivot.y).toBe(32); // 20 + 12
  });
});
