import { app } from 'electron';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

export type Preferences = {
  layout: {
    window_width: number;
    window_height: number;
  };
  file_management: {
    recent_sprite_sheets: string[];
    recent_files_limit: number;
    last_active_sheet?: string | null;
  };
  analysis?: {
    pivot_strategy?: string; // 'bottom-center' | 'center' | 'top-left' | 'top-right'
  };
  overrides?: { // per sheet path -> per frame overrides
    [sheetPath: string]: {
      [frameIndex: number]: {
        pivot?: { x: number; y: number };
        trim?: { x: number; y: number; w: number; h: number };
      }
    }
  };
};

const DEFAULTS: Preferences = {
  layout: { window_width: 1280, window_height: 800 },
  file_management: { recent_sprite_sheets: [], recent_files_limit: 10, last_active_sheet: null },
  analysis: { pivot_strategy: 'bottom-center' }
};

export class PreferencesManager {
  private data: Preferences = DEFAULTS;
  private filepath: string;

  constructor(filename = 'preferences.json') {
    const base = app.getPath('userData');
    mkdirSync(base, { recursive: true });
    this.filepath = join(base, filename);
    this.load();
  }

  private load() {
    if (existsSync(this.filepath)) {
      try {
        const raw = readFileSync(this.filepath, 'utf-8');
        const parsed = JSON.parse(raw);
        this.data = { ...DEFAULTS, ...parsed };
      } catch {
        this.data = DEFAULTS;
      }
    }
  }

  save() {
    writeFileSync(this.filepath, JSON.stringify(this.data, null, 2), 'utf-8');
  }

  get(): Preferences {
    return this.data;
  }

  addRecentSheet(p: string) {
    const list = this.data.file_management.recent_sprite_sheets;
    const cleaned = [p, ...list.filter(x => x !== p)].slice(0, this.data.file_management.recent_files_limit);
    this.data.file_management.recent_sprite_sheets = cleaned;
    this.save();
  }

  setLastActiveSheet(path: string | null) {
    this.data.file_management.last_active_sheet = path || null;
    this.save();
  }

  getPivotStrategy(): string {
    return this.data.analysis?.pivot_strategy || 'bottom-center';
  }

  setPivotStrategy(strategy: string) {
    if (!this.data.analysis) this.data.analysis = {};
    this.data.analysis.pivot_strategy = strategy;
    this.save();
  }

  getOverrides(): NonNullable<Preferences['overrides']> {
    return this.data.overrides || {};
  }

  setOverrides(next: NonNullable<Preferences['overrides']>) {
    this.data.overrides = next;
    this.save();
  }
}
