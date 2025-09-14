export type SliceType = 'hit' | 'hurt' | 'attachment' | 'custom';

export interface SliceKeyRect { x: number; y: number; w: number; h: number; }

export interface SliceKey { frame: number; rect: SliceKeyRect; }

export interface SliceData {
  id: string; // stable id
  name: string;
  type: SliceType;
  keys: Map<number, SliceKeyRect>; // frame -> rect
  color: string; // display color
}

export class SliceStore {
  private slices: Map<string, SliceData> = new Map();

  create(name: string, type: SliceType, frame: number, rect: SliceKeyRect, color: string): string {
    const id = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
    this.slices.set(id,{ id, name, type, keys: new Map([[frame, { ...rect }]]), color });
    return id;
  }

  delete(id: string) { this.slices.delete(id); }

  get(id: string): SliceData | undefined {
    const s = this.slices.get(id); if (!s) return;
    return { id: s.id, name: s.name, type: s.type, color: s.color, keys: new Map(Array.from(s.keys.entries()).map(([f,r])=>[f,{...r}])) };
  }

  restore(data: SliceData) { this.slices.set(data.id, { id:data.id, name:data.name, type:data.type, color:data.color, keys: new Map(Array.from(data.keys.entries()).map(([f,r])=>[f,{...r}])) }); }

  setKey(id: string, frame: number, rect: SliceKeyRect) {
    const s = this.slices.get(id); if (!s) return; s.keys.set(frame, { ...rect });
  }

  removeKey(id: string, frame: number) { const s = this.slices.get(id); if (!s) return; s.keys.delete(frame); }

  getRectAt(id: string, frame: number): SliceKeyRect | undefined {
    const s = this.slices.get(id); if (!s) return; if (s.keys.has(frame)) return s.keys.get(frame);
    // fallback: find last prior
    let best: SliceKeyRect | undefined; let bestFrame = -1;
    s.keys.forEach((r,f)=>{ if (f<=frame && f>bestFrame) { best = r; bestFrame = f; } });
    return best ? { ...best } : undefined;
  }

  all(): SliceData[] { return Array.from(this.slices.values()); }

  toJSON() {
    const out: any[] = [];
    this.slices.forEach(s => {
      out.push({ id: s.id, name: s.name, type: s.type, color: s.color, keys: Array.from(s.keys.entries()).map(([f,r])=>({frame:f, rect:r})) });
    });
    return out;
  }

  static fromJSON(raw: any): SliceStore {
    const store = new SliceStore();
    if (Array.isArray(raw)) {
      raw.forEach(entry => {
        if (entry && typeof entry === 'object' && typeof entry.id === 'string') {
          const data: SliceData = { id: entry.id, name: entry.name||entry.id, type: entry.type||'custom', color: entry.color||'#6cf', keys: new Map() };
          if (Array.isArray(entry.keys)) entry.keys.forEach((k:any)=>{ if (k && typeof k.frame==='number' && k.rect) data.keys.set(k.frame, { ...k.rect }); });
          store.slices.set(data.id, data);
        }
      });
    }
    return store;
  }
}
