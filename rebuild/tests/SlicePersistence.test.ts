import { SliceStore } from '../src/core/Slices';
import { AppStateManager } from '../src/renderer/AppStateManager';
import { SpriteSheet } from '../src/core/SpriteSheet';
import { SelectionManager } from '../src/core/SelectionManager';

describe('Slice persistence MVP', () => {
  test('serializeSlices and loadSlices round trip', () => {
    const app = new AppStateManager();
    const sheet = new SpriteSheet('player.png', 256, 256);
    app.addSheet({ sheet, image: {} as HTMLImageElement, selection: new SelectionManager() });
    const id = app.sliceStore.create('hitbox', 'hit', 0, { x: 4, y: 5, w: 10, h: 12 }, '#f00');
    app.sliceStore.setKey(id, 3, { x: 5, y: 6, w: 12, h: 14 });

    const serialized = app.serializeSlices();
    expect(serialized['player.png']).toBeDefined();
    const jsonArr = serialized['player.png'];
    expect(Array.isArray(jsonArr)).toBe(true);
    // Simulate new app load
    const app2 = new AppStateManager();
    const sheet2 = new SpriteSheet('player.png', 256, 256);
    app2.addSheet({ sheet: sheet2, image: {} as HTMLImageElement, selection: new SelectionManager() });
    app2.loadSlices(serialized);
    const slices = app2.sliceStore.all();
    expect(slices.length).toBe(1);
    const loaded = slices[0];
    expect(loaded.keys.size).toBe(2);
    expect(app2.sliceStore.getRectAt(loaded.id, 3)).toMatchObject({ x:5, y:6, w:12, h:14 });
  });
});
