/**
 * @jest-environment jsdom
 */

import { SliceStore, SliceType } from '../src/core/Slices';

describe('SliceStore Persistence', () => {
  let store: SliceStore;

  beforeEach(() => {
    store = new SliceStore();
  });

  test('creates slices with unique IDs', () => {
    const id1 = store.create('hitbox', 'hit', 0, { x: 10, y: 10, w: 20, h: 20 }, '#f44');
    const id2 = store.create('hurtbox', 'hurt', 0, { x: 15, y: 15, w: 15, h: 15 }, '#fa4');
    
    expect(id1).not.toBe(id2);
    expect(typeof id1).toBe('string');
    expect(typeof id2).toBe('string');
  });

  test('stores and retrieves slice data correctly', () => {
    const rect = { x: 10, y: 10, w: 20, h: 20 };
    const id = store.create('test-slice', 'custom', 5, rect, '#6cf');
    
    const retrieved = store.get(id);
    expect(retrieved).toBeDefined();
    expect(retrieved!.name).toBe('test-slice');
    expect(retrieved!.type).toBe('custom');
    expect(retrieved!.color).toBe('#6cf');
    expect(retrieved!.keys.get(5)).toEqual(rect);
  });

  test('handles timeline key operations', () => {
    const id = store.create('moving-box', 'hit', 0, { x: 0, y: 0, w: 10, h: 10 }, '#f44');
    
    // Add keyframe at frame 5
    store.setKey(id, 5, { x: 50, y: 0, w: 10, h: 10 });
    
    // Add keyframe at frame 10
    store.setKey(id, 10, { x: 100, y: 0, w: 10, h: 10 });
    
    // Test retrieval at exact keyframes
    expect(store.getRectAt(id, 0)).toEqual({ x: 0, y: 0, w: 10, h: 10 });
    expect(store.getRectAt(id, 5)).toEqual({ x: 50, y: 0, w: 10, h: 10 });
    expect(store.getRectAt(id, 10)).toEqual({ x: 100, y: 0, w: 10, h: 10 });
    
    // Test retrieval between keyframes (should use nearest previous)
    expect(store.getRectAt(id, 3)).toEqual({ x: 0, y: 0, w: 10, h: 10 }); // Uses frame 0
    expect(store.getRectAt(id, 7)).toEqual({ x: 50, y: 0, w: 10, h: 10 }); // Uses frame 5
    expect(store.getRectAt(id, 15)).toEqual({ x: 100, y: 0, w: 10, h: 10 }); // Uses frame 10
  });

  test('removes keys correctly', () => {
    const id = store.create('test', 'hit', 0, { x: 0, y: 0, w: 10, h: 10 }, '#f44');
    store.setKey(id, 5, { x: 50, y: 0, w: 10, h: 10 });
    
    // Verify key exists
    expect(store.getRectAt(id, 5)).toEqual({ x: 50, y: 0, w: 10, h: 10 });
    
    // Remove key
    store.removeKey(id, 5);
    
    // Should fall back to previous key (frame 0)
    expect(store.getRectAt(id, 5)).toEqual({ x: 0, y: 0, w: 10, h: 10 });
  });

  test('deletes slices completely', () => {
    const id = store.create('temp', 'custom', 0, { x: 0, y: 0, w: 10, h: 10 }, '#fff');
    
    expect(store.get(id)).toBeDefined();
    
    store.delete(id);
    
    expect(store.get(id)).toBeUndefined();
  });

  test('serializes and deserializes correctly', () => {
    // Create some test data
    const id1 = store.create('hitbox', 'hit', 0, { x: 10, y: 10, w: 20, h: 20 }, '#f44');
    store.setKey(id1, 5, { x: 15, y: 10, w: 20, h: 20 });
    
    const id2 = store.create('attachment', 'attachment', 2, { x: 30, y: 30, w: 5, h: 5 }, '#4af');
    
    // Serialize
    const serialized = store.toJSON();
    expect(Array.isArray(serialized)).toBe(true);
    expect(serialized.length).toBe(2);
    
    // Deserialize into new store
    const newStore = SliceStore.fromJSON(serialized);
    const allSlices = newStore.all();
    
    expect(allSlices.length).toBe(2);
    
    // Find reconstructed slices by name
    const hitbox = allSlices.find(s => s.name === 'hitbox');
    const attachment = allSlices.find(s => s.name === 'attachment');
    
    expect(hitbox).toBeDefined();
    expect(hitbox!.type).toBe('hit');
    expect(hitbox!.color).toBe('#f44');
    expect(hitbox!.keys.size).toBe(2); // frame 0 and 5
    expect(newStore.getRectAt(hitbox!.id, 0)).toEqual({ x: 10, y: 10, w: 20, h: 20 });
    expect(newStore.getRectAt(hitbox!.id, 5)).toEqual({ x: 15, y: 10, w: 20, h: 20 });
    
    expect(attachment).toBeDefined();
    expect(attachment!.type).toBe('attachment');
    expect(attachment!.color).toBe('#4af');
    expect(newStore.getRectAt(attachment!.id, 2)).toEqual({ x: 30, y: 30, w: 5, h: 5 });
  });

  test('handles empty and malformed JSON', () => {
    // Empty array
    const emptyStore = SliceStore.fromJSON([]);
    expect(emptyStore.all().length).toBe(0);
    
    // Null/undefined
    const nullStore = SliceStore.fromJSON(null);
    expect(nullStore.all().length).toBe(0);
    
    // Malformed entries should be skipped
    const malformedStore = SliceStore.fromJSON([
      null,
      { id: 'valid', name: 'test', type: 'hit', color: '#f44', keys: [{ frame: 0, rect: { x: 0, y: 0, w: 10, h: 10 } }] },
      { name: 'missing-id' }, // missing ID, should be skipped
      'not-an-object',
      { id: 'another-valid', keys: [] } // minimal valid entry
    ]);
    
    const slices = malformedStore.all();
    expect(slices.length).toBe(2);
    expect(slices.find(s => s.name === 'test')).toBeDefined();
    expect(slices.find(s => s.id === 'another-valid')).toBeDefined();
  });

  test('handles timeline edge cases', () => {
    const id = store.create('edge-case', 'hit', 10, { x: 100, y: 100, w: 10, h: 10 }, '#f44');
    
    // Requesting before first keyframe should return undefined
    expect(store.getRectAt(id, 5)).toBeUndefined();
    
    // Requesting at exact first keyframe should work
    expect(store.getRectAt(id, 10)).toEqual({ x: 100, y: 100, w: 10, h: 10 });
    
    // Requesting after should use last key
    expect(store.getRectAt(id, 20)).toEqual({ x: 100, y: 100, w: 10, h: 10 });
  });

  test('preserves data isolation between gets', () => {
    const id = store.create('isolation-test', 'custom', 0, { x: 0, y: 0, w: 10, h: 10 }, '#fff');
    
    const data1 = store.get(id);
    const data2 = store.get(id);
    
    // Should be different objects
    expect(data1).not.toBe(data2);
    
    // But with same content
    expect(data1).toEqual(data2);
    
    // Modifying one shouldn't affect the other
    if (data1 && data2) {
      data1.name = 'modified';
      expect(data2.name).toBe('isolation-test');
    }
  });
});