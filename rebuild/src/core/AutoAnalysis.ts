import { FrameAnalyzer, PivotStrategy } from './FrameAnalyzer';
import { SpriteSheet } from './SpriteSheet';
import { FrameOverridesStore } from './FrameOverridesStore';
import { Command } from '../renderer/AppStateManager';

export function createAutoTrimCommand(sheet: SpriteSheet, image: HTMLImageElement, store: FrameOverridesStore, frameIndices: number[]): Command | null {
  if (!frameIndices.length) return null;
  const canvas = document.createElement('canvas');
  canvas.width = sheet.width; canvas.height = sheet.height;
  const ctx = canvas.getContext('2d'); if (!ctx) return null;
  ctx.drawImage(image, 0, 0);
  const pixels = ctx.getImageData(0, 0, sheet.width, sheet.height).data as Uint8ClampedArray;
  const before: Record<number, any> = {}; const after: Record<number, any> = {};
  frameIndices.forEach(idx => {
    before[idx] = { trim: store.getTrim(idx) };
    const fr = sheet.frameRect(idx); if (!fr) return;
    const t = FrameAnalyzer.computeTrim(pixels, fr.w, fr.h, sheet.width, fr.x, fr.y, 1);
    if (t) { after[idx] = { trim: t }; }
  });
  return {
    label: 'Auto Trim',
    do() { frameIndices.forEach(i => { const a = after[i]; if (a && a.trim) store.setTrim(i, a.trim); }); },
    undo() { frameIndices.forEach(i => { const b = before[i]; if (b.trim) store.setTrim(i, b.trim); else { const entry = (store as any).frameMap?.get(i); if (entry) delete entry.trim; } }); }
  };
}

export function createAutoPivotCommand(sheet: SpriteSheet, image: HTMLImageElement, store: FrameOverridesStore, frameIndices: number[], strategy: PivotStrategy): Command | null {
  if (!frameIndices.length) return null;
  const canvas = document.createElement('canvas'); canvas.width = sheet.width; canvas.height = sheet.height;
  const ctx = canvas.getContext('2d'); if (!ctx) return null;
  ctx.drawImage(image, 0, 0);
  const pixels = ctx.getImageData(0, 0, sheet.width, sheet.height).data as Uint8ClampedArray;
  const before: Record<number, any> = {}; const after: Record<number, any> = {};
  frameIndices.forEach(idx => {
    before[idx] = { pivot: store.getPivot(idx) };
    const fr = sheet.frameRect(idx); if (!fr) return;
    let trim = store.getTrim(idx);
    if (!trim) {
      const t = FrameAnalyzer.computeTrim(pixels, fr.w, fr.h, sheet.width, fr.x, fr.y, 1);
      if (t) trim = t;
    }
    const pv = FrameAnalyzer.computePivot(trim ? { x: trim.x, y: trim.y, w: trim.w, h: trim.h } : null, strategy, fr);
    after[idx] = { pivot: { x: pv.x, y: pv.y } };
  });
  return {
    label: 'Auto Pivot',
    do() { frameIndices.forEach(i => { const a = after[i]; if (a && a.pivot) store.setPivot(i, a.pivot); }); },
    undo() { frameIndices.forEach(i => { const b = before[i]; if (b.pivot) store.setPivot(i, b.pivot); else { const entry = (store as any).frameMap?.get(i); if (entry) delete entry.pivot; } }); }
  };
}
