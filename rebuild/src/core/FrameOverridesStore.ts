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

  clearPivot(frameIndex: number) {
    const existing = this.frameMap.get(frameIndex);
    if (existing) {
      delete existing.pivot;
      if (!existing.trim) {
        this.frameMap.delete(frameIndex);
      }
    }
  }

  setTrim(frameIndex: number, trim: TrimOverride) {
    const existing = this.frameMap.get(frameIndex) || {};
    existing.trim = { ...trim };
    this.frameMap.set(frameIndex, existing);
  }

  getTrim(frameIndex: number): TrimOverride | undefined {
    return this.frameMap.get(frameIndex)?.trim;
  }

  clearTrim(frameIndex: number) {
    const existing = this.frameMap.get(frameIndex);
    if (existing) {
      delete existing.trim;
      if (!existing.pivot) {
        this.frameMap.delete(frameIndex);
      }
    }
  }

  pruneInvalid(predicate?: (frameIndex:number, data:FrameOverrideData)=>boolean) {
    if (!predicate) return; // future: add default trimming rules if needed
    const toDelete: number[] = [];
    this.frameMap.forEach((data, idx)=>{ if (!predicate(idx, data)) toDelete.push(idx); });
    toDelete.forEach(i=>this.frameMap.delete(i));
  }

  /**
   * Advanced pruning with multiple strategies for stale override cleanup
   */
  pruneStaleOverrides(options: {
    maxFrameIndex?: number;
    invalidGeometry?: boolean;
    sheetBounds?: { width: number; height: number };
    removeEmptyEntries?: boolean;
  } = {}) {
    const toDelete: number[] = [];
    
    this.frameMap.forEach((data, frameIndex) => {
      let shouldDelete = false;
      
      // Strategy 1: Remove overrides beyond valid frame range
      if (options.maxFrameIndex !== undefined && frameIndex >= options.maxFrameIndex) {
        shouldDelete = true;
      }
      
      // Strategy 2: Remove overrides with invalid geometry
      if (options.invalidGeometry && data.trim) {
        if (data.trim.w <= 0 || data.trim.h <= 0 || 
            data.trim.x < 0 || data.trim.y < 0) {
          delete data.trim;
        }
      }
      
      // Strategy 3: Remove overrides outside sheet bounds
      if (options.sheetBounds && data.trim) {
        const { width, height } = options.sheetBounds;
        if (data.trim.x >= width || data.trim.y >= height ||
            data.trim.x + data.trim.w <= 0 || data.trim.y + data.trim.h <= 0) {
          delete data.trim;
        }
      }
      
      // Strategy 4: Remove entries with no overrides
      if (options.removeEmptyEntries && !data.pivot && !data.trim) {
        shouldDelete = true;
      }
      
      if (shouldDelete) {
        toDelete.push(frameIndex);
      }
    });
    
    toDelete.forEach(idx => this.frameMap.delete(idx));
    
    return toDelete.length; // Return number of pruned entries
  }

  /**
   * Get statistics about override usage for monitoring
   */
  getStats() {
    const stats = {
      totalFrames: this.frameMap.size,
      pivotOverrides: 0,
      trimOverrides: 0,
      bothOverrides: 0,
      memoryEstimateBytes: 0
    };
    
    this.frameMap.forEach(data => {
      const hasPivot = !!data.pivot;
      const hasTrim = !!data.trim;
      
      if (hasPivot) stats.pivotOverrides++;
      if (hasTrim) stats.trimOverrides++;
      if (hasPivot && hasTrim) stats.bothOverrides++;
      
      // Rough memory estimate (object overhead + data)
      stats.memoryEstimateBytes += 64; // base object overhead
      if (hasPivot) stats.memoryEstimateBytes += 16; // x, y numbers
      if (hasTrim) stats.memoryEstimateBytes += 32; // x, y, w, h numbers
    });
    
    return stats;
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

  /**
   * Remove sheets that no longer have any active overrides
   */
  pruneEmptySheets(): string[] {
    const emptySheets: string[] = [];
    
    this.sheets.forEach((store, path) => {
      const stats = store.getStats();
      if (stats.totalFrames === 0) {
        emptySheets.push(path);
        this.sheets.delete(path);
      }
    });
    
    return emptySheets;
  }

  /**
   * Get memory usage statistics across all sheets
   */
  getGlobalStats() {
    const global = {
      totalSheets: this.sheets.size,
      totalFrames: 0,
      totalPivotOverrides: 0,
      totalTrimOverrides: 0,
      totalMemoryEstimateBytes: 0,
      sheetBreakdown: [] as Array<{path: string; frames: number; memory: number}>
    };
    
    this.sheets.forEach((store, path) => {
      const stats = store.getStats();
      global.totalFrames += stats.totalFrames;
      global.totalPivotOverrides += stats.pivotOverrides;
      global.totalTrimOverrides += stats.trimOverrides;
      global.totalMemoryEstimateBytes += stats.memoryEstimateBytes;
      
      global.sheetBreakdown.push({
        path: path.split('/').pop() || path, // Just filename for brevity
        frames: stats.totalFrames,
        memory: stats.memoryEstimateBytes
      });
    });
    
    return global;
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