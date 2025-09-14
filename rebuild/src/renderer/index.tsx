import React, { useEffect, useState, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { SpriteSheet } from '../core/SpriteSheet';
import { SelectionManager } from '../core/SelectionManager';
import { AnimationStore } from '../core/Animation';
import { PlaybackController } from '../core/PlaybackController';
import { FrameAnalyzer } from '../core/FrameAnalyzer';
import { OverridesRegistry } from '../core/FrameOverridesStore';
import { SliceStore } from '../core/Slices';

interface LoadedSheet { sheet: SpriteSheet; image: HTMLImageElement; }

interface SheetContext { sheet: SpriteSheet; image: HTMLImageElement; selection: SelectionManager; }
const animationStore = new AnimationStore();
const playback = new PlaybackController();
// Analyzer caches: per sheet path -> { pixelData, width, height, frameCache: Map<frameIndex,{trim:any,pivot:any}> }
const sheetAnalysisCache: Record<string, { pixels: Uint8ClampedArray; width: number; height: number; frameCache: Map<number,{trim:any,pivot:any}> }> = {};
const overrides = new OverridesRegistry();
const sliceStore = new SliceStore();
// Simple Command pattern scaffold for undo/redo
interface Command { label: string; do(): void; undo(): void; }
class CommandStack {
  private done: Command[] = [];
  private undone: Command[] = [];
  push(cmd: Command) { cmd.do(); this.done.push(cmd); this.undone = []; }
  undo() { const c = this.done.pop(); if (c) { c.undo(); this.undone.push(c); } }
  redo() { const c = this.undone.pop(); if (c) { c.do(); this.done.push(c); } }
  clear() { this.done = []; this.undone = []; }
  counts() { return { done: this.done.length, undone: this.undone.length }; }
}
const commandStack = new CommandStack();
class ZoomManager {
  scale = 1;
  min = 0.25;
  max = 6;
  offsetX = 0; // panning
  offsetY = 0;
  zoom(delta: number, pivotX: number, pivotY: number) {
    const prev = this.scale;
    this.scale = Math.min(this.max, Math.max(this.min, this.scale * delta));
    const factor = this.scale / prev;
    // Adjust offsets so that the point under pivot stays in place
    this.offsetX = pivotX - (pivotX - this.offsetX) * factor;
    this.offsetY = pivotY - (pivotY - this.offsetY) * factor;
  }
  pan(dx: number, dy: number) { this.offsetX += dx; this.offsetY += dy; }
  reset() { this.scale = 1; this.offsetX = 0; this.offsetY = 0; }
}
const zoomMgr = new ZoomManager();

function App() {
  const [sheets, setSheets] = useState<SheetContext[]>([]);
  const [activeSheetPath, setActiveSheetPath] = useState<string | null>(null);
  const [hasAnySheetLoaded, setHasAnySheetLoaded] = useState(false);
  const [showTrim, setShowTrim] = useState(false);
  const [showPivot, setShowPivot] = useState(false);
  const [showSlices, setShowSlices] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string>('');
  const [pivotStrategy, setPivotStrategy] = useState('bottom-center');
  const [version, setVersion] = useState<number>(0);
  const [animVersion, setAnimVersion] = useState<number>(0);
  const [activeSliceId, setActiveSliceId] = useState<string | null>(null);
  const sliceDragRef = useRef<{ id:string; mode:'move'|'resize'; handle?:string; startRect:{x:number;y:number;w:number;h:number}; startMouse:{x:number;y:number} } | null>(null);
  const [newAnimName, setNewAnimName] = useState('anim1');
  const [activeAnimName, setActiveAnimName] = useState<string | null>(null);
  const [playbackTick, setPlaybackTick] = useState(0); // force re-render
  const lastTsRef = useRef<number | null>(null);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const isPanningRef = useRef(false);
  const lastPosRef = useRef<{x:number;y:number}>({x:0,y:0});
  const draggingPivotRef = useRef<{ frameIndex: number; } | null>(null);
  const trimDragRef = useRef<{
    frameIndex: number;
    mode: 'create' | 'resize' | 'move';
    handle?: string; // nw,ne,sw,se
    startRect?: { x:number;y:number;w:number;h:number };
    startMouse?: { x:number;y:number };
  } | null>(null);

  useEffect(() => {
    console.log('[renderer] startup: window.api present?', !!(window as any).api);
    try { window.api.send('debug:log', 'startup', { api: !!(window as any).api }); } catch {}
    window.onerror = (msg, src, line, col, err) => {
      try { window.api.send('debug:log', 'error', { msg, src, line, col, stack: err && (err as any).stack }); } catch {}
      return false;
    };
    function attach() {
      if (!(window as any).api) {
        setTimeout(attach, 50);
        return;
      }
      (window as any).api.openSheetListener(async ({ path }: { path: string }) => {
        console.log('[renderer] sheet:open received', path);
        const img = new Image();
        try {
          const arrayBuffer = await window.api.invoke('file:readBinary', path);
          const blob = new Blob([arrayBuffer], { type: 'image/png' });
          const objectUrl = URL.createObjectURL(blob);
          img.src = objectUrl;
          await img.decode();
        } catch (e) {
          console.error('[renderer] failed to load image binary', e);
        }
  const existing = sheets.find((s:SheetContext) => s.sheet.path === path);
      if (existing) { setActiveSheetPath(path); return; }
      const sheet = new SpriteSheet(path, img.width || 512, img.height || 512, {});
      const ctx: SheetContext = { sheet, image: img, selection: new SelectionManager() };
  setSheets((prev:SheetContext[]) => [...prev, ctx]);
      setActiveSheetPath(path);
      // Reset analysis cache for this sheet if stale
      delete sheetAnalysisCache[path];
      setHasAnySheetLoaded(true);
      console.log('[renderer] sheet loaded dimensions', img.width, img.height);
      });
    }
    attach();

    async function loadPivotStrategy() {
      try {
  const v = await window.api.invoke('prefs:getPivotStrategy');
        if (typeof v === 'string') setPivotStrategy(v);
      } catch {}
    }
    async function loadOverrides() {
      try {
  const raw = await window.api.invoke('overrides:getAll');
        if (!raw || typeof raw !== 'object') return;
        const version = (raw as any).__version;
        if (version != null && version !== 1) {
          // Version mismatch: ignore legacy file (opt-in migration could be added later)
          return;
        }
        const sheetsObj = (raw as any).sheets && typeof (raw as any).sheets === 'object' ? (raw as any).sheets : raw;
        Object.keys(sheetsObj).forEach(sheetPath => {
          if (sheetPath === '__version') return;
          const sheetStore = overrides.getSheet(sheetPath);
          const frames = sheetsObj[sheetPath];
          if (frames && typeof frames === 'object') {
            Object.keys(frames).forEach(idxStr => {
              const idx = parseInt(idxStr);
              if (!Number.isNaN(idx)) {
                const entry = frames[idxStr];
                if (entry?.pivot) sheetStore.setPivot(idx, entry.pivot);
                if (entry?.trim) sheetStore.setTrim(idx, entry.trim);
              }
            });
          }
        });
        // Pruning stub example: ensure no negative coordinates (defensive)
        // overrides.sheets not exposed; iterate current sheets snapshot
        // (Future enhancement could expose a registry-level prune)
      } catch {}
    }
    loadPivotStrategy();
    loadOverrides();

    function onKey(e: KeyboardEvent) {
      const active = sheets.find((s:SheetContext)=>s.sheet.path===activeSheetPath);
      if (!active) return;
      if (e.ctrlKey && (e.key === 'a' || e.key === 'A')) { e.preventDefault(); active.selection.selectAll(active.sheet.frameCount()); setVersion((v:number) => v + 1); }
      else if (e.ctrlKey && (e.key === 'd' || e.key === 'D')) { e.preventDefault(); active.selection.clear(); setVersion((v:number) => v + 1); }
      else if (e.ctrlKey && (e.key === '=' || e.key === '+')) { e.preventDefault(); zoomMgr.zoom(1.1, 0, 0); setVersion((v:number)=>v+1); }
      else if (e.ctrlKey && (e.key === '-' )) { e.preventDefault(); zoomMgr.zoom(1/1.1, 0, 0); setVersion((v:number)=>v+1); }
      else if (e.ctrlKey && e.key === '0') { e.preventDefault(); zoomMgr.reset(); setVersion((v:number)=>v+1); }
      else if (!e.ctrlKey && (e.key === 't' || e.key === 'T')) { e.preventDefault(); setShowTrim((v:boolean)=>!v); }
      else if (!e.ctrlKey && (e.key === 'p' || e.key === 'P')) { e.preventDefault(); setShowPivot((v:boolean)=>!v); }
      else if (!e.ctrlKey && (e.key === 'h' || e.key === 'H')) { e.preventDefault(); const next = !(showTrim||showPivot||showSlices); setShowTrim(next); setShowPivot(next); setShowSlices(next); }
      else if (e.key === 'Escape') { draggingPivotRef.current = null; trimDragRef.current = null; setStatusMsg(''); }
      else if (!e.ctrlKey && ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) {
        const activeCtx = sheets.find((s:SheetContext)=>s.sheet.path===activeSheetPath);
        if (!activeCtx) return;
        const total = activeCtx.sheet.frameCount(); if (total===0) return;
        let focus = activeCtx.selection.order[activeCtx.selection.order.length-1];
        if (focus==null) focus = 0;
        const cols = Math.floor(activeCtx.sheet.width / activeCtx.sheet.params.tileWidth);
        if (e.key==='ArrowLeft') focus = Math.max(0, focus - 1);
        else if (e.key==='ArrowRight') focus = Math.min(total-1, focus + 1);
        else if (e.key==='ArrowUp') focus = Math.max(0, focus - cols);
        else if (e.key==='ArrowDown') focus = Math.min(total-1, focus + cols);
        if (e.shiftKey) {
          activeCtx.selection.click(focus, { shift:true, ctrl:true });
        } else {
          activeCtx.selection.clear(); activeCtx.selection.click(focus, { });
        }
        setVersion((v:number)=>v+1);
      }
  else if (e.ctrlKey && (e.key === 'z' || e.key === 'Z')) { e.preventDefault(); commandStack.undo(); setVersion((v:number)=>v+1); }
      else if (e.ctrlKey && (e.key === 'y' || e.key === 'Y')) { e.preventDefault(); commandStack.redo(); setVersion((v:number)=>v+1); }
  else if (e.key === 'F5') { e.preventDefault(); setAnimVersion((a:number)=>a+1); }
  else if (e.key === 'Delete' && activeSliceId) {
    const snapshot = sliceStore.get(activeSliceId);
    if (snapshot) {
      commandStack.push({ label:'Delete Slice', do:()=>{ sliceStore.delete(activeSliceId); setActiveSliceId(null); }, undo:()=>{ sliceStore.restore(snapshot); } });
      setVersion((v:number)=>v+1); setStatusMsg('Slice deleted');
    }
  }
    }
  window.addEventListener('keydown', onKey);
    function onWheel(e: WheelEvent) {
  if (!hasAnySheetLoaded || !gridRef.current || !e.ctrlKey) return; // require Ctrl for zoom to prevent accidental scroll
      e.preventDefault();
      const rect = gridRef.current.getBoundingClientRect();
      const pivotX = e.clientX - rect.left - zoomMgr.offsetX;
      const pivotY = e.clientY - rect.top - zoomMgr.offsetY;
      const delta = e.deltaY < 0 ? 1.1 : 1/1.1;
  zoomMgr.zoom(delta, pivotX, pivotY);
  setVersion((v:number)=>v+1);
    }
    window.addEventListener('wheel', onWheel, { passive: false });
    function onMouseDown(e: MouseEvent) {
      if (!gridRef.current) return;
      if (e.button === 1 || (e.button === 0 && e.altKey)) { // middle click or Alt+Left drag
        isPanningRef.current = true;
        lastPosRef.current = { x: e.clientX, y: e.clientY };
      }
    }
    function onMouseMove(e: MouseEvent) {
      if (draggingPivotRef.current && gridRef.current && activeSheetCtx) {
        const sheetCtx = activeSheetCtx;
        const rect = gridRef.current.getBoundingClientRect();
        const xInCanvas = (e.clientX - rect.left - zoomMgr.offsetX) / zoomMgr.scale;
        const yInCanvas = (e.clientY - rect.top - zoomMgr.offsetY) / zoomMgr.scale;
        const frameIndex = draggingPivotRef.current.frameIndex;
        // Clamp inside sheet bounds
        const clampedX = Math.max(0, Math.min(sheetCtx.sheet.width, xInCanvas));
        const clampedY = Math.max(0, Math.min(sheetCtx.sheet.height, yInCanvas));
  overrides.getSheet(sheetCtx.sheet.path).setPivot(frameIndex, { x: clampedX, y: clampedY });
  setStatusMsg(`Pivot (${Math.round(clampedX)},${Math.round(clampedY)})`);
  setVersion((v:number)=>v+1);
        return;
      }
      if (trimDragRef.current && gridRef.current && activeSheetCtx) {
        const sheetCtx = activeSheetCtx;
        const rect = gridRef.current.getBoundingClientRect();
        const x = (e.clientX - rect.left - zoomMgr.offsetX) / zoomMgr.scale;
        const y = (e.clientY - rect.top - zoomMgr.offsetY) / zoomMgr.scale;
        const sheetStore = overrides.getSheet(sheetCtx.sheet.path);
        const drag = trimDragRef.current;
        const original = drag.startRect!;
        const dx = x - drag.startMouse!.x;
        const dy = y - drag.startMouse!.y;
        let nx = original.x, ny = original.y, nw = original.w, nh = original.h;
        if (drag.mode === 'resize') {
          if (drag.handle?.includes('e')) nw = Math.max(1, original.w + dx);
          if (drag.handle?.includes('s')) nh = Math.max(1, original.h + dy);
          if (drag.handle?.includes('w')) { nx = Math.min(original.x + original.w - 1, original.x + dx); nw = original.w - dx; if (nw < 1) { nx = nx + nw - 1; nw = 1; } }
          if (drag.handle?.includes('n')) { ny = Math.min(original.y + original.h - 1, original.y + dy); nh = original.h - dy; if (nh < 1) { ny = ny + nh - 1; nh = 1; } }
        } else if (drag.mode === 'create') {
          // drag from original corner to current mouse, create rect normalized
          const x0 = drag.startMouse!.x; const y0 = drag.startMouse!.y;
          nx = Math.min(x0, x); ny = Math.min(y0, y); nw = Math.max(1, Math.abs(x - x0)); nh = Math.max(1, Math.abs(y - y0));
        } else if (drag.mode === 'move') {
          nx = original.x + dx; ny = original.y + dy;
        }
        // Clamp to sheet bounds
        nx = Math.max(0, Math.min(sheetCtx.sheet.width-1, nx));
        ny = Math.max(0, Math.min(sheetCtx.sheet.height-1, ny));
        if (nx + nw > sheetCtx.sheet.width) nw = sheetCtx.sheet.width - nx;
        if (ny + nh > sheetCtx.sheet.height) nh = sheetCtx.sheet.height - ny;
  sheetStore.setTrim(drag.frameIndex, { x: Math.round(nx), y: Math.round(ny), w: Math.round(nw), h: Math.round(nh) });
  setStatusMsg(`Trim ${drag.mode} x:${Math.round(nx)} y:${Math.round(ny)} w:${Math.round(nw)} h:${Math.round(nh)}`);
  setVersion((v:number)=>v+1);
        return;
      }
      if (isPanningRef.current) {
        const dx = e.clientX - lastPosRef.current.x;
        const dy = e.clientY - lastPosRef.current.y;
        lastPosRef.current = { x: e.clientX, y: e.clientY };
  zoomMgr.pan(dx, dy);
  setVersion((v:number)=>v+1);
      }
    }
    function onMouseUp() {
      isPanningRef.current = false;
      // finalize pivot drag -> wrap last state in command for undo
      if (draggingPivotRef.current && activeSheetCtx) {
        const frameIndex = draggingPivotRef.current.frameIndex;
        const sheetPath = activeSheetCtx.sheet.path;
        const store = overrides.getSheet(sheetPath);
        const after = store.getPivot(frameIndex);
        if (after) {
          const before = null; // we don't track original yet; future: capture on mousedown
          commandStack.push({ label:'Set Pivot', do:()=>store.setPivot(frameIndex, after), undo:()=>{ if (before) store.setPivot(frameIndex, before as any); else store.setPivot(frameIndex, undefined as any); } });
        }
      }
      if (trimDragRef.current && activeSheetCtx) {
        const frameIndex = trimDragRef.current.frameIndex;
        const sheetPath = activeSheetCtx.sheet.path;
        const store = overrides.getSheet(sheetPath);
        const after = store.getTrim(frameIndex);
        if (after) {
          const before = null; // placeholder until we capture initial rect
          commandStack.push({ label:'Set Trim', do:()=>store.setTrim(frameIndex, after), undo:()=>{ if (before) store.setTrim(frameIndex, before as any); else store.setTrim(frameIndex, undefined as any); } });
        }
      }
  draggingPivotRef.current = null; trimDragRef.current = null; setStatusMsg(''); setVersion((v:number)=>v+1);
    }
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // playback loop
  useEffect(() => {
    function frame(ts: number) {
      if (lastTsRef.current == null) lastTsRef.current = ts;
      const delta = ts - lastTsRef.current;
      lastTsRef.current = ts;
      playback.update(delta);
  if (playback.isPlaying()) setPlaybackTick((t:number) => t + 1);
      requestAnimationFrame(frame);
    }
    const id = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(id);
  }, []);

  const activeSheetCtx: SheetContext | null = sheets.find((s:SheetContext)=>s.sheet.path===activeSheetPath) || null;
  const currentSheet = (): SheetContext | null => activeSheetCtx;

  // Slice dragging interactions (move/resize)
  useEffect(()=>{
    function onMove(e:MouseEvent){
      if (!sliceDragRef.current) return;
      const sheetCtx = activeSheetCtx; if (!sheetCtx) return;
      const fi = sheetCtx.selection.order[0]; if (fi==null) return;
      const d = sliceDragRef.current;
      const dx = (e.clientX - d.startMouse.x) / zoomMgr.scale;
      const dy = (e.clientY - d.startMouse.y) / zoomMgr.scale;
      let { x, y, w, h } = d.startRect;
      if (d.mode==='move') { x = Math.round(d.startRect.x + dx); y = Math.round(d.startRect.y + dy); }
      else if (d.mode==='resize') {
        if (d.handle?.includes('e')) w = Math.max(1, Math.round(d.startRect.w + dx));
        if (d.handle?.includes('s')) h = Math.max(1, Math.round(d.startRect.h + dy));
        if (d.handle?.includes('w')) { const nx = Math.round(d.startRect.x + dx); w = w + (x - nx); x = nx; }
        if (d.handle?.includes('n')) { const ny = Math.round(d.startRect.y + dy); h = h + (y - ny); y = ny; }
      }
      sliceStore.setKey(d.id, fi, { x, y, w, h });
      setVersion((v:number)=>v+1);
    }
    function onUp(){
      if (sliceDragRef.current) {
        const d = sliceDragRef.current;
        const sheetCtx = activeSheetCtx; if (sheetCtx) {
          const fi = sheetCtx.selection.order[0];
          if (fi!=null) {
            const orig = (d as any).originalRect;
            const finalRect = sliceStore.getRectAt(d.id, fi);
            if (orig && finalRect && (orig.x!==finalRect.x || orig.y!==finalRect.y || orig.w!==finalRect.w || orig.h!==finalRect.h)) {
              const before = { ...orig };
              const after = { ...finalRect };
              commandStack.push({
                label: d.mode==='move' ? 'Move Slice' : 'Resize Slice',
                do: ()=>{ sliceStore.setKey(d.id, fi, { ...after }); },
                undo: ()=>{ sliceStore.setKey(d.id, fi, { ...before }); },
              });
            }
          }
        }
        sliceDragRef.current = null; setStatusMsg('');
      }
    }
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return ()=>{ window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, [activeSheetCtx]);

  function startPlayback(name: string) {
    const anim = animationStore.all().find((a:any) => a.name === name) || null;
    playback.load(anim || null);
    if (anim) playback.play();
    setActiveAnimName(anim ? anim.name : null);
    setPlaybackTick((t:number)=>t+1);
  }

  function togglePlayPause() {
    playback.toggle();
    setPlaybackTick((t:number)=>t+1);
  }

  function toggleSelect(index: number, e: React.MouseEvent) {
    const active = activeSheetCtx; if (!active) return;
    active.selection.click(index, { ctrl: e.ctrlKey, shift: e.shiftKey });
    setVersion((v:number) => v + 1);
  }

  function renderGrid() {
  const active = activeSheetCtx;
  if (!active) return null;
    const rects = active.sheet.allFrameRects();

    // Ensure sheet pixel data cached
    if (showTrim || showPivot) {
      if (!sheetAnalysisCache[active.sheet.path]) {
        try {
          const canvas = document.createElement('canvas');
          canvas.width = active.sheet.width; canvas.height = active.sheet.height;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(active.image, 0, 0);
            const imgData = ctx.getImageData(0,0,canvas.width, canvas.height);
            sheetAnalysisCache[active.sheet.path] = { pixels: imgData.data, width: canvas.width, height: canvas.height, frameCache: new Map() };
          }
        } catch {}
      }
    }

    function getFrameAnalysis(frameIndex: number, frameRect: any) {
      if (!active) return null;
      const sheetCache = sheetAnalysisCache[active.sheet.path];
      if (!sheetCache) return null;
      if (!sheetCache.frameCache.has(frameIndex)) {
        const trim = FrameAnalyzer.computeTrim(sheetCache.pixels, frameRect.w, frameRect.h, sheetCache.width, frameRect.x, frameRect.y, 1);
        const pivot = FrameAnalyzer.computePivot(trim, pivotStrategy as any, frameRect);
        sheetCache.frameCache.set(frameIndex, { trim, pivot });
      }
      return sheetCache.frameCache.get(frameIndex);
    }
    return (
   <div className="grid-canvas" ref={gridRef}
     style={{ transform:`translate(${zoomMgr.offsetX}px,${zoomMgr.offsetY}px) scale(${zoomMgr.scale})`, transformOrigin:'0 0', backgroundImage:`url(${active.image.src})`, backgroundRepeat:'no-repeat', width: active.sheet.width, height: active.sheet.height }}>
        {rects.map((r:any) => (
          <div key={r.index} className={"frame-rect" + (active.selection.isSelected(r.index) ? ' frame-selected' : '')}
               style={{ left:r.x, top:r.y, width:r.w, height:r.h }} onClick={(e:React.MouseEvent<HTMLDivElement>)=>toggleSelect(r.index,e)}>
            {active.selection.isSelected(r.index) && <span className="order-badge">{active.selection.order.indexOf(r.index)+1}</span>}
          </div>
        ))}
        {showTrim && rects.map(r => {
          const analysis = getFrameAnalysis(r.index, r);
          const sheetOverrides = overrides.getSheet(active.sheet.path);
          const oTrim = sheetOverrides.getTrim(r.index);
          const autoTrim = analysis?.trim;
          if (!oTrim && !autoTrim) return null;
          const renderAuto = autoTrim && oTrim; // show auto dashed beneath if override exists
          return <React.Fragment key={'trimwrap-'+r.index}>
            {renderAuto && <div style={{position:'absolute', left:autoTrim.x, top:autoTrim.y, width:autoTrim.w, height:autoTrim.h, border:'1px dashed rgba(0,255,255,0.4)', pointerEvents:'none'}}/>}
            <div
              key={'trim-'+r.index}
              onMouseDown={(e:React.MouseEvent<HTMLDivElement>)=>{
                if (e.button!==0) return;
                e.stopPropagation();
                const rectDom = (gridRef.current as HTMLDivElement).getBoundingClientRect();
                const canvasX = (e.clientX - rectDom.left - zoomMgr.offsetX) / zoomMgr.scale;
                const canvasY = (e.clientY - rectDom.top - zoomMgr.offsetY) / zoomMgr.scale;
                if (!oTrim && autoTrim && e.ctrlKey) {
                  // create override from auto trim
                  sheetOverrides.setTrim(r.index, { ...autoTrim });
                  trimDragRef.current = { frameIndex: r.index, mode:'resize', handle: 'se', startRect: { ...autoTrim }, startMouse: { x: canvasX, y: canvasY } };
                  setVersion((v:number)=>v+1);
                  return;
                }
                if (oTrim && !e.ctrlKey) {
                  // begin move drag inside existing override
                  trimDragRef.current = { frameIndex: r.index, mode:'move', startRect: { ...oTrim }, startMouse: { x: canvasX, y: canvasY } };
                  return;
                }
              }}
              style={{position:'absolute', left:(oTrim||autoTrim!).x, top:(oTrim||autoTrim!).y, width:(oTrim||autoTrim!).w, height:(oTrim||autoTrim!).h, border:'1px solid '+(oTrim? '#ffa500':'cyan'), background:oTrim? 'rgba(255,165,0,0.05)':'transparent', cursor:oTrim? 'move':'pointer'}}
            >
              {oTrim && ['nw','ne','sw','se'].map(h => {
                const size = 6; const half = size/2;
                const box = oTrim;
                const hx = h.includes('w')? box.x : box.x + box.w;
                const hy = h.includes('n')? box.y : box.y + box.h;
                return <div key={h}
                  onMouseDown={(e:React.MouseEvent<HTMLDivElement>)=>{ e.stopPropagation(); if (e.button!==0) return; trimDragRef.current = { frameIndex: r.index, mode:'resize', handle:h, startRect:{...box}, startMouse:{ x: hx, y: hy } }; }}
                  style={{position:'absolute', left: hx - (h.includes('w')?0:size), top: hy - (h.includes('n')?0:size), width:size, height:size, background:'#ffa500', border:'1px solid #000', boxSizing:'border-box', cursor: h+'-resize'}}/>;
              })}
            </div>
          </React.Fragment>;
        })}
        {showPivot && rects.map(r => {
          const analysis = getFrameAnalysis(r.index, r);
          const sheetOverrides = overrides.getSheet(active.sheet.path);
          const oPivot = sheetOverrides.getPivot(r.index);
          const pivotToShow = oPivot || (analysis && analysis.pivot);
          if (!pivotToShow) return null;
          const size = 7;
          return <div
            key={'pivot-'+r.index}
            onMouseDown={(e:React.MouseEvent<HTMLDivElement>)=>{
              e.stopPropagation();
              if (e.button!==0) return; // left only
              draggingPivotRef.current = { frameIndex: r.index };
            }}
            style={{position:'absolute', left:pivotToShow.x - size/2, top:pivotToShow.y - size/2, width:size, height:size, background: oPivot? '#fa0':'#ff0', border:'1px solid #000', borderRadius:'50%', cursor: draggingPivotRef.current? 'grabbing':'grab', boxShadow:'0 0 2px #000'}}
            title={oPivot? 'Pivot (override)':'Pivot (auto)'}
          />;
        })}
        {showSlices && (()=>{
          const firstFrame = active.selection.order[0];
          if (firstFrame==null) return null;
          return sliceStore.all().map(slc => {
            const rect = (slc as any).getRectAt ? (slc as any).getRectAt(firstFrame) : undefined;
            if (!rect) return null;
            const selected = activeSliceId === slc.id;
            return <div key={slc.id}
              onMouseDown={(e:React.MouseEvent<HTMLDivElement>)=>{ e.stopPropagation(); if (e.button!==0) return; setActiveSliceId(slc.id); sliceDragRef.current = { id:slc.id, mode:'move', startRect:{...rect}, startMouse:{x:e.clientX,y:e.clientY} } as any; (sliceDragRef.current as any).originalRect = {...rect}; setStatusMsg('Slice move'); }}
              style={{position:'absolute', left:rect.x, top:rect.y, width:rect.w, height:rect.h, border: selected? '2px solid #ff0':'1px solid '+slc.color, background:selected? 'rgba(255,255,0,0.08)':'transparent', cursor:selected? (sliceDragRef.current? 'grabbing':'grab'):'pointer'}} title={slc.name}>
              {selected && ['nw','ne','sw','se'].map(h=>{
                const hx = h.includes('w')? rect.x : rect.x + rect.w;
                const hy = h.includes('n')? rect.y : rect.y + rect.h;
                return <div key={h} onMouseDown={(e:React.MouseEvent<HTMLDivElement>)=>{ e.stopPropagation(); if (e.button!==0) return; sliceDragRef.current = { id:slc.id, mode:'resize', handle:h, startRect:{...rect}, startMouse:{x:e.clientX,y:e.clientY} } as any; (sliceDragRef.current as any).originalRect = {...rect}; setStatusMsg('Slice resize'); }} style={{position:'absolute', left: hx-4, top: hy-4, width:8, height:8, background:'#ff0', border:'1px solid #000', cursor: h==='nw'||h==='se'? 'nwse-resize':'nesw-resize'}}/>;
              })}
            </div>;
          });
        })()}
      </div>
    );
  }

  function updateParam(field: 'tileWidth'|'tileHeight'|'margin'|'spacing', value: number) {
    const active = activeSheetCtx; if (!active) return;
  active.sheet.setParams({ [field]: value });
  // Invalidate per-frame analysis cache because frame rects changed
  const cache = sheetAnalysisCache[active.sheet.path];
  if (cache) cache.frameCache.clear();
    setSheets((prev:SheetContext[]) => prev.map((s:SheetContext) => s.sheet.path===active.sheet.path ? active : s));
    setVersion((v:number)=>v+1);
  }

  // Persist overrides when they change (simple timer flush)
  const persistTimerRef = useRef<any>(null);
  useEffect(()=>{
    if (!showPivot) return; // only start watching when pivot UI engaged
    if (persistTimerRef.current) clearInterval(persistTimerRef.current);
    persistTimerRef.current = setInterval(()=>{
  const payload = overrides.toJSON();
  window.api.send('overrides:setAll', payload);
    }, 1500);
    return ()=> { if (persistTimerRef.current) clearInterval(persistTimerRef.current); };
  }, [showPivot]);

  function createAnimation() {
    const active = activeSheetCtx; if (!active) return; if (!newAnimName.trim()) return;
    animationStore.createFromSelection(newAnimName.trim(), active.sheet.path, active.selection.order);
  setAnimVersion((v:number)=>v+1);
  setNewAnimName((prev:string) => prev==='anim1' ? 'anim2' : prev + '_copy');
  }

  function animationsForActiveSheet() {
    const active = activeSheetCtx; if (!active) return [];
    return animationStore.all().filter(a => a.sheetPath === active.sheet.path);
  }

  return (
    <div className="layout">
      <div className="panel" style={{background:'#1e1e1e', color:'#ccc'}}>
        <strong>Animations</strong>
        <div style={{fontSize:12, marginTop:8}}>
          <div style={{display:'flex', gap:4}}>
            <input style={{flex:1}} value={newAnimName} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>setNewAnimName(e.target.value)} placeholder="name" />
            <button disabled={!currentSheet() || currentSheet()!.selection.order.length===0} onClick={createAnimation}>Create</button>
          </div>
          <ul style={{marginTop:8, paddingLeft:16}}>
            {animationsForActiveSheet().map(a => <li key={a.name} style={{cursor:'pointer', color: a.name===activeAnimName? '#6cf':'#ccc'}} onClick={()=>startPlayback(a.name)}>{a.name} {a.loop?'' : '(once)'} ({a.frames.length}f, {a.totalDuration()}ms)</li>)}
          </ul>
          <div style={{marginTop:8}}>
            <button disabled={!activeAnimName} onClick={togglePlayPause}>{playback.isPlaying()? 'Pause':'Play'}</button>
            <span style={{marginLeft:8}}>Frame: {playback.currentFrameNumberInAnimation()}</span>
            {activeAnimName && (()=>{ const a = animationStore.all().find(x=>x.name===activeAnimName); if(!a) return null; return <label style={{marginLeft:8, fontSize:11}}><input type="checkbox" checked={a.loop} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>{ a.loop = e.target.checked; setAnimVersion((v:number)=>v+1); }} /> Loop</label>; })()}
          </div>
          {activeAnimName && (()=>{
            const anim = animationStore.all().find(a=>a.name===activeAnimName); if (!anim) return null;
            return <div style={{marginTop:8, maxHeight:120, overflow:'auto', border:'1px solid #333', padding:4}}>
              <table style={{width:'100%', fontSize:11, borderCollapse:'collapse'}}>
                <thead><tr><th style={{textAlign:'left'}}>#</th><th>Frame</th><th>Dur(ms)</th></tr></thead>
                <tbody>
                  {anim.frames.map((f,idx)=><tr key={idx} style={{background: idx===playback.currentFrameNumberInAnimation()? '#222':'transparent'}}>
                    <td>{idx}</td>
                    <td>{f.frameIndex}</td>
                    <td><input style={{width:60}} type="number" value={f.durationMs} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>{ f.durationMs = Math.max(1, parseInt(e.target.value)||1); setAnimVersion((v:number)=>v+1); }} /></td>
                  </tr>)}
                </tbody>
              </table>
            </div>;
          })()}
          <div style={{marginTop:8, border:'1px solid #333', height:120, display:'flex', alignItems:'center', justifyContent:'center', background:'#111', position:'relative'}}>
            {/* Simple preview: show current frame rectangle outline using sheet image as background clipped */}
            {activeSheetCtx && activeAnimName && (()=>{
              const sheetCtx = activeSheetCtx;
              const globalIndex = playback.currentFrameGlobalIndex();
              if (!sheetCtx || globalIndex==null) return null;
              if (sheetCtx.sheet.path !== (animationStore.all().find(a=>a.name===activeAnimName)?.sheetPath)) return null; // ensure matching sheet
              const rect = sheetCtx.sheet.frameRect(globalIndex);
              if(!rect) return null;
              const bgPos = `-${rect.x}px -${rect.y}px`;
              return <div style={{width:rect.w, height:rect.h, backgroundImage:`url(${sheetCtx.image.src})`, backgroundPosition:bgPos, imageRendering:'pixelated', outline:'1px solid #6cf'}}/>;
            })()}
          </div>
        </div>
      </div>
      <div className="panel" style={{background:'#181818', color:'#ccc', position:'relative'}}>
        <strong>Grid</strong>
        {/* Tabs */}
        <div style={{display:'flex', gap:4, marginTop:4, flexWrap:'wrap'}}>
          {sheets.map((s:SheetContext) => (
            <div key={s.sheet.path} onClick={()=>{ setActiveSheetPath(s.sheet.path); window.api.send('prefs:setLastActiveSheet', s.sheet.path); setVersion((v:number)=>v+1); }}
                 style={{padding:'2px 6px', background: s.sheet.path===activeSheetPath? '#333':'#222', border:'1px solid #444', cursor:'pointer', fontSize:11}}>
              {s.sheet.path.split(/[/\\]/).pop()}
            </div>
          ))}
        </div>
        {/* Overlay Toggles */}
        <div style={{display:'flex', gap:4, margin:'4px 0'}}>
          <button style={{fontSize:11}} title="T" onClick={()=>setShowTrim((v:boolean)=>!v)}>{showTrim? 'Trim ON':'Trim OFF'}</button>
          <button style={{fontSize:11}} title="P" onClick={()=>setShowPivot((v:boolean)=>!v)}>{showPivot? 'Pivot ON':'Pivot OFF'}</button>
          <button style={{fontSize:11}} onClick={()=>setShowSlices((v:boolean)=>!v)}>{showSlices? 'Slices ON':'Slices OFF'}</button>
          <select style={{fontSize:11}} value={pivotStrategy} onChange={e=>{
            const val = e.target.value;
            setPivotStrategy(val);
            window.api.send('prefs:setPivotStrategy', val);
            // Invalidate only pivot values for all sheets
            Object.values(sheetAnalysisCache).forEach(c => c.frameCache.forEach((v,k)=>{ c.frameCache.set(k,{ trim: v.trim, pivot: null }); }));
          }} title="Pivot Strategy">
            <option value="bottom-center">bottom-center</option>
            <option value="center">center</option>
            <option value="top-left">top-left</option>
            <option value="top-right">top-right</option>
          </select>
        </div>
        <div onClick={(e)=>{
          if (!showSlices) return;
          if (!activeSheetCtx) return;
          // Simple create: Shift+Click creates a 16x16 slice at mouse position for first selected frame
          if (e.shiftKey) {
            const rectDom = (gridRef.current as HTMLDivElement).getBoundingClientRect();
            const x = Math.round((e.clientX - rectDom.left - zoomMgr.offsetX) / zoomMgr.scale);
            const y = Math.round((e.clientY - rectDom.top - zoomMgr.offsetY) / zoomMgr.scale);
            const frame = activeSheetCtx.selection.order[0]; if (frame==null) return;
            sliceStore.create('slice'+(sliceStore.all().length+1), 'custom', frame, { x, y, w:16, h:16 }, '#6cf');
            setVersion((v:number)=>v+1);
          }
        }} style={{position:'relative', width:'100%', height:'100%'}}>
          {renderGrid()}
        </div>
      </div>
      <div className="panel" style={{background:'#202020', color:'#ccc'}}>
        <strong>Properties</strong>
        {activeSheetCtx && <div style={{fontSize:12, marginTop:8}}>
          <div>File: {activeSheetCtx.sheet.path}</div>
            <div>Size: {activeSheetCtx.sheet.width}x{activeSheetCtx.sheet.height}</div>
            <div>Frames: {activeSheetCtx.sheet.frameCount()}</div>
            <div>Selection: {activeSheetCtx.selection.order.join(', ') || 'None'}</div>
            <div style={{marginTop:8}}><em>Grid Parameters</em></div>
            <div style={{display:'grid', gridTemplateColumns:'80px 1fr', gap:4}}>
              <label>Tile W</label><input type="number" value={activeSheetCtx.sheet.params.tileWidth} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>updateParam('tileWidth', parseInt(e.target.value)||0)} />
              <label>Tile H</label><input type="number" value={activeSheetCtx.sheet.params.tileHeight} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>updateParam('tileHeight', parseInt(e.target.value)||0)} />
              <label>Margin</label><input type="number" value={activeSheetCtx.sheet.params.margin} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>updateParam('margin', parseInt(e.target.value)||0)} />
              <label>Spacing</label><input type="number" value={activeSheetCtx.sheet.params.spacing} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>updateParam('spacing', parseInt(e.target.value)||0)} />
            </div>
            {showPivot && (()=>{
              const sel = activeSheetCtx.selection.order[0]; if (sel==null) return null;
              const store = overrides.getSheet(activeSheetCtx.sheet.path);
              const frameRect = activeSheetCtx.sheet.frameRect(sel);
              if(!frameRect) return null;
              const cache = sheetAnalysisCache[activeSheetCtx.sheet.path];
              if (cache && !cache.frameCache.has(sel)) {
                const trim = FrameAnalyzer.computeTrim(cache.pixels, frameRect.w, frameRect.h, cache.width, frameRect.x, frameRect.y, 1);
                const pivot = FrameAnalyzer.computePivot(trim, pivotStrategy as any, frameRect);
                cache.frameCache.set(sel,{trim,pivot});
              }
              const analysis = sheetAnalysisCache[activeSheetCtx.sheet.path]?.frameCache.get(sel);
              const autoPivot = analysis?.pivot;
              const current = store.getPivot(sel) || autoPivot;
              if (!current) return null;
              return <div style={{marginTop:12}}>
                <em>Pivot Override</em>
                <div style={{display:'grid', gridTemplateColumns:'50px 1fr 1fr', gap:4, marginTop:4}}>
                  <label>X</label>
                  <input type="number" value={Math.round(current.x)} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>{ const x = parseInt(e.target.value)||0; store.setPivot(sel,{x,y:current.y}); setVersion((v:number)=>v+1); }} />
                  <button style={{fontSize:10}} onClick={()=>{ if(autoPivot){ store.setPivot(sel,{...autoPivot}); setVersion((v:number)=>v+1);} }}>Auto</button>
                  <label>Y</label>
                  <input type="number" value={Math.round(current.y)} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>{ const y = parseInt(e.target.value)||0; store.setPivot(sel,{x:current.x,y}); setVersion((v:number)=>v+1); }} />
                  <button style={{fontSize:10}} onClick={()=>{ store.setPivot(sel, undefined as any); setVersion((v:number)=>v+1); }}>Clear</button>
                </div>
              </div>;
            })()}
            {showTrim && activeSheetCtx.selection.order.length>0 && <div style={{marginTop:12}}>
              <button style={{fontSize:11}} onClick={()=>{
                const sheetPath = activeSheetCtx.sheet.path;
                const sheetCache = sheetAnalysisCache[sheetPath]; if (!sheetCache) return;
                activeSheetCtx.selection.order.forEach(fi=>{
                  const rect = activeSheetCtx.sheet.frameRect(fi);
                  if(!rect) return;
                  if (!sheetCache.frameCache.has(fi)) {
                    const trim = FrameAnalyzer.computeTrim(sheetCache.pixels, rect.w, rect.h, sheetCache.width, rect.x, rect.y, 1);
                    const pivot = FrameAnalyzer.computePivot(trim, pivotStrategy as any, rect);
                    sheetCache.frameCache.set(fi,{trim,pivot});
                  }
                  const data = sheetCache.frameCache.get(fi);
                  if (data?.trim) overrides.getSheet(sheetPath).setTrim(fi,{...data.trim});
                  if (data?.pivot) overrides.getSheet(sheetPath).setPivot(fi,{...data.pivot});
                });
                setVersion((v:number)=>v+1);
              }}>Auto Trim+Pivot (Selection)</button>
            </div>}
        </div>}
      </div>
      <div className="status">{statusMsg || (activeSheetCtx ? `${activeSheetCtx.sheet.path} | ${activeSheetCtx.selection.order.length} selected` : 'No sheet loaded')} | Anims: {animationsForActiveSheet().length}</div>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
