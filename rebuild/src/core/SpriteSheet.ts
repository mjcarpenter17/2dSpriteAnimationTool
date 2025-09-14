export interface SpriteSheetParams {
  tileWidth: number;
  tileHeight: number;
  margin: number;
  spacing: number;
}

export interface FrameRect { x: number; y: number; w: number; h: number; index: number; row: number; col: number; }

export class SpriteSheet {
  readonly path: string;
  readonly width: number;
  readonly height: number;
  params: SpriteSheetParams;

  constructor(path: string, width: number, height: number, params: Partial<SpriteSheetParams> = {}) {
    this.path = path;
    this.width = width;
    this.height = height;
    this.params = {
      tileWidth: params.tileWidth ?? 32,
      tileHeight: params.tileHeight ?? 32,
      margin: params.margin ?? 0,
      spacing: params.spacing ?? 0
    };
  }

  setParams(next: Partial<SpriteSheetParams>) {
    this.params = { ...this.params, ...next };
  }

  get columns(): number {
    const { tileWidth, margin, spacing } = this.params;
    if (tileWidth <= 0) return 0;
    const innerWidth = this.width - margin * 2;
    return Math.max(0, Math.floor((innerWidth + spacing) / (tileWidth + spacing)));
  }

  get rows(): number {
    const { tileHeight, margin, spacing } = this.params;
    if (tileHeight <= 0) return 0;
    const innerHeight = this.height - margin * 2;
    return Math.max(0, Math.floor((innerHeight + spacing) / (tileHeight + spacing)));
  }

  frameCount(): number { return this.rows * this.columns; }

  frameRect(index: number): FrameRect | null {
    if (index < 0 || index >= this.frameCount()) return null;
    const col = index % this.columns;
    const row = Math.floor(index / this.columns);
    const { tileWidth, tileHeight, margin, spacing } = this.params;
    const x = margin + col * (tileWidth + spacing);
    const y = margin + row * (tileHeight + spacing);
    return { x, y, w: tileWidth, h: tileHeight, index, row, col };
  }

  allFrameRects(): FrameRect[] {
    const out: FrameRect[] = [];
    for (let i = 0; i < this.frameCount(); i++) {
      const r = this.frameRect(i);
      if (r) out.push(r);
    }
    return out;
  }
}
