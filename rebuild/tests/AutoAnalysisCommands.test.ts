import { SpriteSheet } from '../src/core/SpriteSheet';
import { FrameOverridesStore } from '../src/core/FrameOverridesStore';
import { createAutoTrimCommand, createAutoPivotCommand } from '../src/core/AutoAnalysis';
import { CommandStack } from '../src/renderer/AppStateManager';

function mockCanvas(pixels: Uint8ClampedArray, width: number, height: number) {
  (HTMLCanvasElement.prototype as any).getContext = function () {
    return {
      drawImage: () => {},
      getImageData: () => ({ data: pixels })
    };
  };
}

function makeImage(width: number, height: number): HTMLImageElement {
  const img = new Image();
  Object.defineProperty(img, 'naturalWidth', { value: width });
  Object.defineProperty(img, 'naturalHeight', { value: height });
  return img as HTMLImageElement;
}

describe('AutoAnalysis Commands', () => {
  test('auto trim sets trim override and undo restores state', () => {
    const sheet = new SpriteSheet('test', 64, 32, { tileWidth:32, tileHeight:32 });
    const pixels = new Uint8ClampedArray(sheet.width * sheet.height * 4);
    // Mark a 10x10 opaque area starting at (2,2)
    for (let y=2; y<12; y++) {
      for (let x=2; x<12; x++) {
        const idx = (y * sheet.width + x) * 4;
        pixels[idx+3] = 255; // alpha
      }
    }
    mockCanvas(pixels, sheet.width, sheet.height);
    const img = makeImage(sheet.width, sheet.height);
    const store = new FrameOverridesStore();
    const stack = new CommandStack();
    const cmd = createAutoTrimCommand(sheet, img, store, [0]);
    expect(cmd).not.toBeNull();
    stack.push(cmd!);
    const t = store.getTrim(0);
    expect(t).toBeTruthy();
    expect(t!.x).toBe(2); expect(t!.y).toBe(2);
    stack.undo(); expect(store.getTrim(0)).toBeUndefined();
    stack.redo(); expect(store.getTrim(0)).toBeTruthy();
  });

  test('auto pivot sets pivot override considering strategy', () => {
    const sheet = new SpriteSheet('test', 64, 32, { tileWidth:32, tileHeight:32 });
    const pixels = new Uint8ClampedArray(sheet.width * sheet.height * 4);
    // Fill first tile fully opaque
    for (let y=0; y<32; y++) {
      for (let x=0; x<32; x++) {
        const idx = (y * sheet.width + x) * 4; pixels[idx+3] = 255;
      }
    }
    mockCanvas(pixels, sheet.width, sheet.height);
    const img = makeImage(sheet.width, sheet.height);
    const store = new FrameOverridesStore();
    const stack = new CommandStack();
    const cmd = createAutoPivotCommand(sheet, img, store, [0], 'center');
    expect(cmd).not.toBeNull();
    stack.push(cmd!);
    const pv = store.getPivot(0); expect(pv).toBeTruthy();
    expect(Math.round(pv!.x)).toBe(16); expect(Math.round(pv!.y)).toBe(16);
    stack.undo(); expect(store.getPivot(0)).toBeUndefined();
    stack.redo(); expect(store.getPivot(0)).toBeTruthy();
  });
});
