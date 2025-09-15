import { FrameOverridesStore } from '../src/core/FrameOverridesStore';

describe('Overrides pruning', () => {
  test('prunes entries with frame index beyond new frame count', () => {
    const store = new FrameOverridesStore();
    store.setPivot(0, { x: 1, y: 1 });
    store.setPivot(5, { x: 2, y: 2 });
    store.setTrim(7, { x:0,y:0,w:10,h:10 });
    // Before pruning we have entries at 0,5,7
    const before = JSON.stringify(store.toJSON());
    expect(before.includes('5')).toBe(true);
    expect(before.includes('7')).toBe(true);
    // Suppose new frame count is 6 (valid indices 0..5)
    store.pruneInvalid((idx) => idx < 6);
    const after = JSON.stringify(store.toJSON());
    expect(after.includes('7')).toBe(false);
    expect(after.includes('5')).toBe(true);
  });
});
