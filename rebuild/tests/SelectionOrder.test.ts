import { SelectionManager } from '../src/core/SelectionManager';

describe('Selection ordering', () => {
  test('plain click replaces selection', () => {
    const sel = new SelectionManager();
    sel.click(2);
    sel.click(5);
    expect(sel.order).toEqual([5]);
  });

  test('ctrl click toggles', () => {
    const sel = new SelectionManager();
    sel.click(1);
    sel.click(3, { ctrl: true });
    sel.click(1, { ctrl: true }); // remove 1
    expect(sel.order).toEqual([3]);
  });

  test('shift click adds range preserving order', () => {
    const sel = new SelectionManager();
    sel.click(2); // anchor 2
    sel.click(6, { shift: true }); // adds 2..6 => appended after existing order (2 already there)
    expect(sel.order).toEqual([2,3,4,5,6]);
  });

  test('selectAll populates ordered sequence', () => {
    const sel = new SelectionManager();
    sel.selectAll(5);
    expect(sel.order).toEqual([0,1,2,3,4]);
  });

  test('clear empties selection', () => {
    const sel = new SelectionManager();
    sel.selectAll(3);
    sel.clear();
    expect(sel.order).toEqual([]);
  });
});
