import React, { useEffect, useState, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import { SpriteSheet } from '../core/SpriteSheet';
import { SelectionManager } from '../core/SelectionManager';
import { FrameAnalyzer } from '../core/FrameAnalyzer';
import { AppStateManager, SheetContext } from './AppStateManager';
import { ErrorBoundary } from './components/ErrorBoundary';
import { StatusBar } from './components/StatusBar';
import { Toolbar } from './components/Toolbar';
import { AnimationsPane } from './components/AnimationsPane';
import { SliceLegend } from './components/SliceLegend';
import './styles.css';

// Global app state instance
const appState = new AppStateManager();

function App() {
  // UI State
  const [showTrim, setShowTrim] = useState(false);
  const [showPivot, setShowPivot] = useState(false);
  const [showSlices, setShowSlices] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string>('');
  const [pivotStrategy, setPivotStrategy] = useState('bottom-center');
  const [version, setVersion] = useState<number>(0);
  const [animVersion, setAnimVersion] = useState<number>(0);
  const [activeSliceId, setActiveSliceId] = useState<string | null>(null);
  const [newAnimName, setNewAnimName] = useState('anim1');
  const [activeAnimName, setActiveAnimName] = useState<string | null>(null);
  const [durationEditVersion, setDurationEditVersion] = useState(0);
  const [playbackTick, setPlaybackTick] = useState(0);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Refs
  const gridRef = useRef<HTMLDivElement | null>(null);
  const lastTsRef = useRef<number | null>(null);
  const isPanningRef = useRef(false);
  const lastPosRef = useRef<{x:number;y:number}>({x:0,y:0});
  const draggingPivotRef = useRef<{ frameIndex: number; } | null>(null);
  const sliceDragRef = useRef<{ 
    id:string; 
    mode:'move'|'resize'; 
    handle?:string; 
    startRect:{x:number;y:number;w:number;h:number}; 
    startMouse:{x:number;y:number} 
  } | null>(null);
  const trimDragRef = useRef<{
    frameIndex: number;
    mode: 'create' | 'resize' | 'move';
    handle?: string;
    startRect?: { x:number;y:number;w:number;h:number };
    startMouse?: { x:number;y:number };
  } | null>(null);

  // Force re-render helper
  const forceUpdate = useCallback(() => setVersion(v => v + 1), []);

  // Initialize app
  useEffect(() => {
    console.log('[renderer] startup: window.api present?', !!(window as any).api);
    
    // Setup error handling
    window.onerror = (msg, src, line, col, err) => {
      try { 
        window.api.send('debug:log', 'error', { 
          msg, src, line, col, 
          stack: err && (err as any).stack 
        }); 
      } catch {}
      return false;
    };

    // Setup sheet loader
    const setupSheetLoader = () => {
      if (!(window as any).api) {
        setTimeout(setupSheetLoader, 50);
        return;
      }

      (window as any).api.openSheetListener(async ({ path }: { path: string }) => {
        try {
          console.log('[renderer] sheet:open received', path);
          await loadSheet(path);
        } catch (error) {
          console.error('Failed to load sheet:', error);
          setStatusMsg(`Failed to load sheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      });
    };

    setupSheetLoader();
    loadPreferences();
    // Theme initial load + listener
    (async () => {
      try {
        const th = await (window as any).api.invoke('theme:get');
        if (th === 'dark' || th === 'light') setTheme(th);
      } catch {}
      if ((window as any).api?.onThemeChanged) {
        (window as any).api.onThemeChanged((t: 'light' | 'dark') => setTheme(t));
      }
    })();
    setupKeyboardHandlers();
    setupMouseHandlers();

    return () => {
      // Cleanup event listeners would go here
    };
  }, []);

  const loadSheet = async (path: string) => {
    const img = new Image();
    try {
      const arrayBuffer = await window.api.invoke('file:readBinary', path);
      const blob = new Blob([arrayBuffer], { type: 'image/png' });
      const objectUrl = URL.createObjectURL(blob);
      img.src = objectUrl;
      await img.decode();

      const sheet = new SpriteSheet(path, img.naturalWidth, img.naturalHeight);
      const context: SheetContext = {
        sheet,
        image: img,
        selection: new SelectionManager()
      };

      appState.addSheet(context);
      setStatusMsg(`Loaded: ${path} (${img.naturalWidth}×${img.naturalHeight})`);
      forceUpdate();

      // Cache analysis data
      if (!appState.sheetAnalysisCache[path]) {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d')!;
        ctx.drawImage(img, 0, 0);
        const pixels = ctx.getImageData(0, 0, img.naturalWidth, img.naturalHeight).data;
        
        appState.sheetAnalysisCache[path] = {
          pixels,
          width: img.naturalWidth,
          height: img.naturalHeight,
          frameCache: new Map()
        };
      }
    } catch (error) {
      console.error('Error loading sheet:', error);
      throw error;
    }
  };

  const loadPreferences = () => {
    // Load pivot strategy and overrides from preferences
    // Implementation would go here
  };

  const requireThemeListener = () => {};

  const setupKeyboardHandlers = () => {
    const onKey = (e: KeyboardEvent) => {
      const active = appState.getActiveSheet();
      if (!active) return;

      // Handle various keyboard shortcuts
      if (e.ctrlKey && (e.key === 'a' || e.key === 'A')) {
        e.preventDefault();
        active.selection.selectAll(active.sheet.frameCount());
        forceUpdate();
      } else if (e.ctrlKey && (e.key === 'd' || e.key === 'D')) {
        e.preventDefault();
        active.selection.clear();
        forceUpdate();
      } else if (e.ctrlKey && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault();
        appState.commandStack.undo();
        forceUpdate();
      } else if (e.ctrlKey && (e.key === 'y' || e.key === 'Y')) {
        e.preventDefault();
        appState.commandStack.redo();
        forceUpdate();
      } else if (!e.ctrlKey && (e.key === 't' || e.key === 'T')) {
        e.preventDefault();
        setShowTrim(v => !v);
      } else if (!e.ctrlKey && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault();
        setShowPivot(v => !v);
      } else if (e.key === 'F5') {
        e.preventDefault();
        setAnimVersion(a => a + 1); // triggers animations list refresh re-render
      }
      // Add more keyboard shortcuts as needed
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  };

  const setupMouseHandlers = () => {
    const onWheel = (e: WheelEvent) => {
      if (!appState.getActiveSheet() || !gridRef.current || !e.ctrlKey) return;
      e.preventDefault();
      const container = gridRef.current as HTMLElement;
      const rect = container.getBoundingClientRect();
      const pivotX = e.clientX - rect.left + container.scrollLeft;
      const pivotY = e.clientY - rect.top + container.scrollTop;
      const oldScale = appState.zoomMgr.scale;
      const delta = e.deltaY > 0 ? 1/1.1 : 1.1;
      appState.zoomMgr.zoom(delta, pivotX / oldScale, pivotY / oldScale); // zoom manager still expects sheet-space pivot
      const newScale = appState.zoomMgr.scale;
      // Maintain pivot focus: compute new scroll so that sheet-space pivot stays under cursor
      const scaleRatio = newScale / oldScale;
      container.scrollLeft = pivotX * scaleRatio - (e.clientX - rect.left);
      container.scrollTop = pivotY * scaleRatio - (e.clientY - rect.top);
      forceUpdate();
    };

    window.addEventListener('wheel', onWheel, { passive: false });
    return () => window.removeEventListener('wheel', onWheel);
  };

  // Event handlers
  const handleUndo = () => {
    appState.commandStack.undo();
    forceUpdate();
  };

  const handleRedo = () => {
    appState.commandStack.redo();
    forceUpdate();
  };

  const handleZoomReset = () => {
    appState.zoomMgr.reset();
    forceUpdate();
  };

  const handlePivotStrategyChange = (strategy: string) => {
    setPivotStrategy(strategy);
    // Save to preferences and trigger re-analysis if needed
  };

  // Grid rendering function (returns frame rectangles only; outer wrapper handles transform)
  const renderGrid = (sheetContext: SheetContext) => {
    const rects = sheetContext.sheet.allFrameRects();
    const toggleSelect = (index: number, e: React.MouseEvent) => {
      sheetContext.selection.click(index, { ctrl: e.ctrlKey, shift: e.shiftKey });
      forceUpdate();
    };
    return (
      <>
        {rects.map(rect => {
          const ov = appState.overrides.getSheet(sheetContext.sheet.path);
            const hasPivot = !!ov.getPivot(rect.index);
            const hasTrim = !!ov.getTrim(rect.index);
            const title = hasPivot || hasTrim ? `Overrides: ${[hasPivot? 'pivot': null, hasTrim? 'trim': null].filter(Boolean).join(', ')}` : undefined;
            return (
              <div
                key={rect.index}
                className={`frame-rect ${sheetContext.selection.isSelected(rect.index) ? 'frame-selected' : ''}`}
                style={{
                  position: 'absolute',
                  left: rect.x,
                  top: rect.y,
                  width: rect.w,
                  height: rect.h,
                  border: sheetContext.selection.isSelected(rect.index) ? '2px solid #00ffff' : '1px solid var(--grid-border)',
                  cursor: 'pointer',
                  pointerEvents: 'all'
                }}
                onClick={(e) => toggleSelect(rect.index, e)}
                title={title}
              >
                {sheetContext.selection.isSelected(rect.index) && (
                  <span className="order-badge" style={{ position: 'absolute', top: -1, left: -1, background: '#00ffff', color: '#000', fontSize: '10px', padding: '1px 4px', borderRadius: '0 0 3px 0', fontWeight: 'bold' }}>
                    {sheetContext.selection.order.indexOf(rect.index) + 1}
                  </span>
                )}
              </div>
          );})}
      </>
    );
  };

  // Get current state for display
  const activeSheet = appState.getActiveSheet();
  const activeAnimation = activeAnimName ? appState.animationStore.all().find(a => a.name === activeAnimName) || null : null;
  const hasAnySheetLoaded = appState.sheets.length > 0;
  const commandCounts = appState.commandStack.counts();

  return (
    <ErrorBoundary>
      <div className={theme === 'dark' ? 'theme-dark' : ''} style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Toolbar
          showTrim={showTrim}
          showPivot={showPivot}
          showSlices={showSlices}
          pivotStrategy={pivotStrategy}
          onToggleTrim={() => setShowTrim(v => !v)}
          onTogglePivot={() => setShowPivot(v => !v)}
          onToggleSlices={() => setShowSlices(v => !v)}
          onPivotStrategyChange={handlePivotStrategyChange}
          onZoomReset={handleZoomReset}
          extraButtons={<button onClick={() => {
            const next = theme === 'dark' ? 'light' : 'dark';
            (window as any).api.send('theme:set', next);
            setTheme(next);
          }}>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</button>}
        />

        <div style={{ flex: 1, display: 'flex' }}>
          {/* Left Panel - Animations */}
          <div style={{ width: '200px', background: 'var(--panel-bg)', borderRight: '1px solid var(--panel-border)', padding: '8px', boxSizing: 'border-box' }}>
            <AnimationsPane
              animations={appState.animationStore.all()}
              activeSheetPath={activeSheet?.sheet.path || null}
              onCreate={(name) => {
                if (!activeSheet) return;
                const selectionOrder = activeSheet.selection.order;
                if (selectionOrder.length === 0) {
                  setStatusMsg('Select frames before creating an animation');
                  return;
                }
                const anim = appState.animationStore.createFromSelection(name, activeSheet.sheet.path, selectionOrder);
                setActiveAnimName(anim.name);
                setNewAnimName(prev => prev === name ? name + '_1' : prev); // simple name progression
                setAnimVersion(a => a + 1); // refresh list
                setStatusMsg(`Created animation '${anim.name}' (${anim.frames.length} frames)`);
              }}
              onSelect={(name) => setActiveAnimName(name)}
              activeAnimation={activeAnimName}
              newAnimName={newAnimName}
              onNewNameChange={setNewAnimName}
              refreshToken={animVersion}
            />
          </div>

          {/* Center Panel - Grid */}
          <div style={{ flex: 1, position: 'relative', overflow: 'auto' }} ref={gridRef as any}>
            {/* Scroll container holds a sized box we scale; scrollbars provide navigation */}
            {!hasAnySheetLoaded && (
              <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: '#666', fontSize: '18px' }}>Open a sprite sheet to get started</div>
            )}
            {hasAnySheetLoaded && activeSheet && (
              <div
                style={{
                  position: 'relative',
                  width: activeSheet.sheet.width * appState.zoomMgr.scale,
                  height: activeSheet.sheet.height * appState.zoomMgr.scale
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    width: activeSheet.sheet.width,
                    height: activeSheet.sheet.height,
                    transform: `scale(${appState.zoomMgr.scale})`,
                    transformOrigin: '0 0'
                  }}
                >
                  <img src={activeSheet.image.src} style={{ position: 'absolute', left:0, top:0, width: activeSheet.sheet.width, height: activeSheet.sheet.height, userSelect:'none', pointerEvents:'none' }} />
                  {renderGrid(activeSheet)}
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Properties */}
          <div style={{ width: '250px', background: 'var(--panel-bg)', borderLeft: '1px solid var(--panel-border)', padding: '8px' }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>Properties</h3>
            
            {activeSheet && (
              <div style={{ fontSize: '12px' }}>
                <div><strong>Sheet:</strong> {activeSheet.sheet.width}×{activeSheet.sheet.height}</div>
                <div><strong>Tile:</strong> {activeSheet.sheet.params.tileWidth}×{activeSheet.sheet.params.tileHeight}</div>
                <div><strong>Frames:</strong> {activeSheet.sheet.frameCount()}</div>
                <div><strong>Selected:</strong> {activeSheet.selection.order.length}</div>
              </div>
            )}

            <div style={{ marginTop: '16px' }}>
              <h4 style={{ margin: '0 0 4px 0', fontSize: '12px' }}>Grid Parameters</h4>
              {activeSheet && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '11px' }}>
                  <label>Width:</label>
                  <input 
                    type="number" 
                    value={activeSheet.sheet.params.tileWidth} 
                    onChange={(e) => {
                      activeSheet.sheet.setParams({ tileWidth: parseInt(e.target.value) || 32 });
                      // Prune overrides invalidated by reduced frame count
                      const count = activeSheet.sheet.frameCount();
                      appState.overrides.getSheet(activeSheet.sheet.path).pruneInvalid((idx)=> idx < count);
                      forceUpdate();
                    }}
                  />
                  <label>Height:</label>
                  <input 
                    type="number" 
                    value={activeSheet.sheet.params.tileHeight} 
                    onChange={(e) => {
                      activeSheet.sheet.setParams({ tileHeight: parseInt(e.target.value) || 32 });
                      const count = activeSheet.sheet.frameCount();
                      appState.overrides.getSheet(activeSheet.sheet.path).pruneInvalid((idx)=> idx < count);
                      forceUpdate();
                    }}
                  />
                  <label>Margin:</label>
                  <input 
                    type="number" 
                    value={activeSheet.sheet.params.margin} 
                    onChange={(e) => {
                      activeSheet.sheet.setParams({ margin: parseInt(e.target.value) || 0 });
                      const count = activeSheet.sheet.frameCount();
                      appState.overrides.getSheet(activeSheet.sheet.path).pruneInvalid((idx)=> idx < count);
                      forceUpdate();
                    }}
                  />
                  <label>Spacing:</label>
                  <input 
                    type="number" 
                    value={activeSheet.sheet.params.spacing} 
                    onChange={(e) => {
                      activeSheet.sheet.setParams({ spacing: parseInt(e.target.value) || 0 });
                      const count = activeSheet.sheet.frameCount();
                      appState.overrides.getSheet(activeSheet.sheet.path).pruneInvalid((idx)=> idx < count);
                      forceUpdate();
                    }}
                  />
                </div>
              )}
            </div>

            {activeAnimation && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '12px' }}>Animation: {activeAnimation.name}</h4>
                <div style={{ fontSize: '11px', marginBottom: 4 }}>Total Duration: {activeAnimation.totalDuration()} ms</div>
                <div style={{ maxHeight: 180, overflowY: 'auto', border: '1px solid #ccc', padding: 4, borderRadius: 4, background:'#fff' }}>
                  {activeAnimation.frames.map((f, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
                      <span style={{ width: 30, textAlign: 'right' }}>#{idx}</span>
                      <span style={{ width: 50 }}>F{f.frameIndex}</span>
                      <input
                        type="number"
                        value={f.durationMs}
                        min={1}
                        style={{ width: 70 }}
                        onChange={(e) => {
                          const raw = parseInt(e.target.value, 10);
                          const newVal = isNaN(raw) ? f.durationMs : Math.max(1, Math.min(10000, raw));
                          if (newVal === f.durationMs) return;
                          // Capture old value for undo
                          const oldVal = f.durationMs;
                          const frameRef = f;
                          appState.commandStack.push({
                            label: 'Set Frame Duration',
                            do() { frameRef.durationMs = newVal; },
                            undo() { frameRef.durationMs = oldVal; }
                          });
                          setDurationEditVersion(v => v + 1);
                          forceUpdate();
                        }}
                      />
                      <span style={{ fontSize: 9, color: '#555' }}>ms</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <SliceLegend visible={showSlices} />
          </div>
        </div>

        <StatusBar
          message={statusMsg}
          undoCount={commandCounts.done}
          redoCount={commandCounts.undone}
          onUndo={handleUndo}
          onRedo={handleRedo}
        />
      </div>
    </ErrorBoundary>
  );
}

export default App;