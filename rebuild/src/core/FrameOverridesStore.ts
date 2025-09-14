export interface PivotOverride { x: number; y: number; }
export interface TrimOverride { x: number; y: number; w: number; h: number; }
export const OVERRIDES_VERSION = 1; // Increment when schema changes


interface FrameOverrideData {
  pivot?: PivotOverride;
  trim?: TrimOverride;
}

// Stores overrides per frame index for a single sheet
export class FrameOverridesStore {
  private frameMap: Map<number, FrameOverrideData> = new Map();

  setPivot(frameIndex: number, pivot: PivotOverride) {
    const existing = this.frameMap.get(frameIndex) || {};
    existing.pivot = { ...pivot };
    this.frameMap.set(frameIndex, existing);
  }

  getPivot(frameIndex: number): PivotOverride | undefined {
    return this.frameMap.get(frameIndex)?.pivot;
  }

  setTrim(frameIndex: number, trim: TrimOverride) {
    const existing = this.frameMap.get(frameIndex) || {};
    existing.trim = { ...trim };
    this.frameMap.set(frameIndex, existing);
  }

  getTrim(frameIndex: number): TrimOverride | undefined {
    return this.frameMap.get(frameIndex)?.trim;
  }

  pruneInvalid(predicate?: (frameIndex:number, data:FrameOverrideData)=>boolean) {
    if (!predicate) return; // future: add default trimming rules if needed
    const toDelete: number[] = [];
    this.frameMap.forEach((data, idx)=>{ if (!predicate(idx, data)) toDelete.push(idx); });
    toDelete.forEach(i=>this.frameMap.delete(i));
  }

  toJSON() {
    const frames: Record<number, FrameOverrideData> = {} as any;
    this.frameMap.forEach((v,k)=>{ frames[k] = v; });
    return frames;
  }

  static fromJSON(obj: any): FrameOverridesStore {
    const store = new FrameOverridesStore();
    if (obj && typeof obj === 'object') {
      Object.keys(obj).forEach(k => {
        const idx = parseInt(k);
        if (!Number.isNaN(idx)) {
          const entry = obj[k];
            const data: FrameOverrideData = {};
            if (entry.pivot && typeof entry.pivot.x === 'number' && typeof entry.pivot.y === 'number') data.pivot = { x: entry.pivot.x, y: entry.pivot.y };
            if (entry.trim && ['x','y','w','h'].every(f=> typeof entry.trim[f] === 'number')) data.trim = { x: entry.trim.x, y: entry.trim.y, w: entry.trim.w, h: entry.trim.h };
            if (data.pivot || data.trim) store.frameMap.set(idx, data);
        }
      });
    }
    return store;
  }
}

// Central registry keyed by sheet path
export class OverridesRegistry {
  private sheets: Map<string, FrameOverridesStore> = new Map();

  getSheet(path: string): FrameOverridesStore {
    let s = this.sheets.get(path);
    if (!s) { s = new FrameOverridesStore(); this.sheets.set(path, s); }
    return s;
  }

  toJSON() {
    const sheets: Record<string, any> = {};
    this.sheets.forEach((store, path) => { sheets[path] = store.toJSON(); });
    return { __version: OVERRIDES_VERSION, sheets };
  }

  static fromJSON(obj: any): OverridesRegistry {
    const reg = new OverridesRegistry();
    if (!obj || typeof obj !== 'object') return reg;
    const version = obj.__version;
    if (version !== undefined && version !== OVERRIDES_VERSION) {
      // Version mismatch: skip loading to avoid corrupt interpretation
      return reg;
    }
    const sheets = obj.sheets && typeof obj.sheets === 'object' ? obj.sheets : obj;
    Object.keys(sheets).forEach(path => {
      if (path === '__version') return;
      try {
        reg.sheets.set(path, FrameOverridesStore.fromJSON(sheets[path]));
      } catch {}
    });
    return reg;
  }
}