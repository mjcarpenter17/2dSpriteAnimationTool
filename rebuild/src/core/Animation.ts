export interface AnimationFrameRef { frameIndex: number; durationMs: number; }
export interface AnimationData {
  name: string;
  sheetPath: string; // association to SpriteSheet path
  frames: AnimationFrameRef[]; // ordered
  loop: boolean;
  playback: { mode: 'forward'; speedScale: number };
  tags: string[];
}

export class Animation implements AnimationData {
  name: string;
  sheetPath: string;
  frames: AnimationFrameRef[] = [];
  loop: boolean = true;
  playback = { mode: 'forward' as const, speedScale: 1.0 };
  tags: string[] = [];

  constructor(init: Partial<AnimationData> & { name: string; sheetPath: string }) {
    this.name = init.name;
    this.sheetPath = init.sheetPath;
    if (init.frames) this.frames = init.frames;
    if (typeof init.loop === 'boolean') this.loop = init.loop;
    if (init.playback) this.playback = init.playback;
    if (init.tags) this.tags = init.tags;
  }

  addFrame(frameIndex: number, durationMs = 83) { this.frames.push({ frameIndex, durationMs }); }
  totalDuration(): number { return this.frames.reduce((a,f)=>a+f.durationMs,0); }
}

export class AnimationStore {
  private list: Animation[] = [];

  createFromSelection(name: string, sheetPath: string, selectionOrder: number[], defaultDuration = 83): Animation {
    const anim = new Animation({ name, sheetPath, frames: selectionOrder.map(i => ({ frameIndex: i, durationMs: defaultDuration })) });
    this.list.push(anim);
    return anim;
  }

  all(): Animation[] { return [...this.list]; }
}
