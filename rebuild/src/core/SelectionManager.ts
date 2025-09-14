export class SelectionManager {
  private ordered: number[] = [];
  private anchor: number | null = null;

  get order(): number[] { return [...this.ordered]; }

  clear() { this.ordered = []; this.anchor = null; }

  selectAll(total: number) {
    this.ordered = [];
    for (let i = 0; i < total; i++) this.ordered.push(i);
    this.anchor = this.ordered.length ? this.ordered[0] : null;
  }

  isSelected(i: number) { return this.ordered.includes(i); }

  click(index: number, opts: { ctrl?: boolean; shift?: boolean } = {}) {
    const { ctrl, shift } = opts;
    if (shift && this.anchor != null) {
      const start = Math.min(this.anchor, index);
      const end = Math.max(this.anchor, index);
      const range: number[] = [];
      for (let i = start; i <= end; i++) range.push(i);
      // preserve existing order, append new items in ascending
      const existing = new Set(this.ordered);
      const added = range.filter(i => !existing.has(i));
      this.ordered = [...this.ordered, ...added];
      return;
    }
    if (ctrl) {
      if (this.isSelected(index)) {
        this.ordered = this.ordered.filter(i => i !== index);
      } else {
        this.ordered.push(index);
        if (this.anchor == null) this.anchor = index;
      }
      return;
    }
    // plain click
    this.ordered = [index];
    this.anchor = index;
  }
}
