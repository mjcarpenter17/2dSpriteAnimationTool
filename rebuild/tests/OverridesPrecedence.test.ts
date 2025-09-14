import { FrameAnalyzer } from '../src/core/FrameAnalyzer';
import { OverridesRegistry } from '../src/core/FrameOverridesStore';

function makePixels(width: number, height: number, opaque: Array<[number, number]>): Uint8ClampedArray {
  const arr = new Uint8ClampedArray(width * height * 4);
  for (const [x,y] of opaque) {
    const idx = (y * width + x) * 4;
    arr[idx] = 255; arr[idx+1]=255; arr[idx+2]=255; arr[idx+3]=255;
  }
  return arr;
}

describe('Overrides precedence', () => {
  test('override pivot takes precedence over auto', () => {
    const pixels = makePixels(32,32,[ [1,1],[4,4] ]);
    // simulate one frame 8x8 at (0,0) inside 32 sheet width
    const trim = FrameAnalyzer.computeTrim(pixels, 8,8,32,0,0);
    const autoPivot = FrameAnalyzer.computePivot(trim!, 'bottom-center', { x:0,y:0,w:8,h:8 });
    const registry = new OverridesRegistry();
    const store = registry.getSheet('sheetA');
    store.setPivot(0,{ x: 99, y: 77 });
    // expectation: manual pivot differs; ensure not equal to auto
    expect(store.getPivot(0)).toEqual({ x:99, y:77 });
    expect(store.getPivot(0)).not.toEqual(autoPivot);
  });

  test('override trim replaces auto for frame', () => {
    const pixels = makePixels(32,32,[ [2,2],[5,5] ]);
    const auto = FrameAnalyzer.computeTrim(pixels, 8,8,32,0,0);
    const registry = new OverridesRegistry();
    const store = registry.getSheet('sheetB');
    store.setTrim(0,{ x:0,y:0,w:3,h:3 });
    expect(store.getTrim(0)).toEqual({ x:0,y:0,w:3,h:3 });
    expect(store.getTrim(0)).not.toEqual(auto!);
  });
});

describe('Trim bounds validity', () => {
  test('manual trim within frame bounds acceptable', () => {
    const registry = new OverridesRegistry();
    const store = registry.getSheet('sheetC');
    store.setTrim(5,{ x:10,y:12,w:4,h:6 });
    const t = store.getTrim(5);
    expect(t).toBeDefined();
    expect(t!.w).toBe(4);
    expect(t!.h).toBe(6);
  });

  test('fully transparent frame auto trim null, manual override persists', () => {
    // 8x8 transparent area in a 16x16 sheet (all zeros)
    const pixels = new Uint8ClampedArray(16 * 16 * 4); // all alpha=0
    const auto = FrameAnalyzer.computeTrim(pixels, 8,8,16,0,0,1);
    expect(auto).toBeNull();
    const registry = new OverridesRegistry();
    const store = registry.getSheet('sheetT');
    store.setTrim(0,{ x:0,y:0,w:2,h:3 });
    expect(store.getTrim(0)).toEqual({ x:0,y:0,w:2,h:3 });
  });
});
