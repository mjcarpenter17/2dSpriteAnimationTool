import { SpriteSheet } from '../src/core/SpriteSheet';

describe('SpriteSheet grid calculations', () => {
  test('computes columns and rows correctly', () => {
    const sheet = new SpriteSheet('dummy.png', 128, 64, { tileWidth: 32, tileHeight: 16, margin:0, spacing:0 });
    expect(sheet.columns).toBe(4);
    expect(sheet.rows).toBe(4);
    expect(sheet.frameCount()).toBe(16);
  });

  test('frameRect returns correct position', () => {
    const sheet = new SpriteSheet('dummy.png', 96, 32, { tileWidth: 16, tileHeight: 16, margin: 8, spacing: 4 });
    // inner width = 96 - 16 = 80; tile+spacing=20 -> columns=4
    expect(sheet.columns).toBe(4);
    const r = sheet.frameRect(5); // row=1 col=1
    expect(r).not.toBeNull();
    expect(r!.x).toBe(8 + 1*(16+4));
    expect(r!.y).toBe(8 + 1*(16+4));
  });
});
