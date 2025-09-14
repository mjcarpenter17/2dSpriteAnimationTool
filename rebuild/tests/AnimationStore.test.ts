import { AnimationStore } from '../src/core/Animation';

describe('AnimationStore', () => {
  test('createFromSelection builds ordered frame list', () => {
    const store = new AnimationStore();
    const anim = store.createFromSelection('run', 'sheet.png', [5,2,9]);
    expect(anim.frames.map(f=>f.frameIndex)).toEqual([5,2,9]);
    expect(store.all().length).toBe(1);
  });
});
