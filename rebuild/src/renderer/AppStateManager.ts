import { SpriteSheet } from '../core/SpriteSheet';
import { SelectionManager } from '../core/SelectionManager';
import { AnimationStore } from '../core/Animation';
import { PlaybackController } from '../core/PlaybackController';
import { OverridesRegistry } from '../core/FrameOverridesStore';
import { SliceStore } from '../core/Slices';

export interface SheetContext {
  sheet: SpriteSheet;
  image: HTMLImageElement;
  selection: SelectionManager;
}

export interface Command {
  label: string;
  do(): void;
  undo(): void;
}

export class CommandStack {
  private done: Command[] = [];
  private undone: Command[] = [];

  push(cmd: Command) {
    cmd.do();
    this.done.push(cmd);
    this.undone = [];
  }

  undo(): boolean {
    const c = this.done.pop();
    if (c) {
      c.undo();
      this.undone.push(c);
      return true;
    }
    return false;
  }

  redo(): boolean {
    const c = this.undone.pop();
    if (c) {
      c.do();
      this.done.push(c);
      return true;
    }
    return false;
  }

  clear() {
    this.done = [];
    this.undone = [];
  }

  counts() {
    return { done: this.done.length, undone: this.undone.length };
  }
}

export class ZoomManager {
  scale = 1;
  min = 0.25;
  max = 6;
  offsetX = 0;
  offsetY = 0;

  zoom(delta: number, pivotX: number, pivotY: number) {
    const prev = this.scale;
    this.scale = Math.min(this.max, Math.max(this.min, this.scale * delta));
    const factor = this.scale / prev;
    
    // Adjust offsets so that the point under pivot stays in place
    this.offsetX = pivotX - (pivotX - this.offsetX) * factor;
    this.offsetY = pivotY - (pivotY - this.offsetY) * factor;
  }

  pan(dx: number, dy: number) {
    this.offsetX += dx;
    this.offsetY += dy;
  }

  reset() {
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;
  }
}

export interface AnalysisCache {
  pixels: Uint8ClampedArray;
  width: number;
  height: number;
  frameCache: Map<number, { trim: any; pivot: any }>;
}

export class AppStateManager {
  // Core instances
  public readonly animationStore = new AnimationStore();
  public readonly playback = new PlaybackController();
  public readonly overrides = new OverridesRegistry();
  public readonly sliceStore = new SliceStore();
  public readonly commandStack = new CommandStack();
  public readonly zoomMgr = new ZoomManager();

  // Analysis cache
  public readonly sheetAnalysisCache: Record<string, AnalysisCache> = {};

  // State
  public sheets: SheetContext[] = [];
  public activeSheetPath: string | null = null;

  constructor() {
    // Initialize any cross-manager dependencies here
  }

  getActiveSheet(): SheetContext | null {
    if (!this.activeSheetPath) return null;
    return this.sheets.find(s => s.sheet.path === this.activeSheetPath) || null;
  }

  addSheet(context: SheetContext) {
    // Remove existing sheet with same path
    this.sheets = this.sheets.filter(s => s.sheet.path !== context.sheet.path);
    this.sheets.push(context);
    this.activeSheetPath = context.sheet.path;
  }

  removeSheet(path: string) {
    this.sheets = this.sheets.filter(s => s.sheet.path !== path);
    if (this.activeSheetPath === path) {
      this.activeSheetPath = this.sheets.length > 0 ? this.sheets[0].sheet.path : null;
    }
  }

  clear() {
    this.sheets = [];
    this.activeSheetPath = null;
    this.commandStack.clear();
    this.zoomMgr.reset();
    Object.keys(this.sheetAnalysisCache).forEach(key => delete this.sheetAnalysisCache[key]);
  }

  serializeSlices(): Record<string, any[]> {
    const out: Record<string, any[]> = {};
    this.sheets.forEach(ctx => {
      // For now a single global sliceStore; future: per-sheet store mapping
      out[ctx.sheet.path] = this.sliceStore.toJSON();
    });
    return out;
  }

  loadSlices(data: Record<string, any[]>) {
    if (!data || typeof data !== 'object') return;
    // naive: merge all slices from provided sheet path arrays into global store
    Object.keys(data).forEach(path => {
      const arr = data[path];
      if (Array.isArray(arr)) {
        const loaded = SliceStore.fromJSON(arr); // new instance
        loaded.all().forEach((s) => this.sliceStore.restore(s));
      }
    });
  }
}
