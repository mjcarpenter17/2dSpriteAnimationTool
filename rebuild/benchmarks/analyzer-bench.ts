import { FrameAnalyzer } from '../src/core/FrameAnalyzer';

// Simple micro-benchmark for trim & pivot computations.
// Generates synthetic frames with random opaque blobs to simulate work.
// Outputs: iterations, total ms, avg/frame, trims found %, pivot strategy timings.

interface Result { label: string; ms: number; }

function now() { return performance.now(); }

function run(label: string, fn: () => void): Result {
  const start = now();
  fn();
  return { label, ms: now() - start };
}

function synthSheet(width: number, height: number): Uint8ClampedArray {
  const arr = new Uint8ClampedArray(width * height * 4);
  // Fill with full transparency
  for (let i=0;i<arr.length;i+=4) { arr[i]=0; arr[i+1]=0; arr[i+2]=0; arr[i+3]=0; }
  // Add a few random opaque rectangles
  const rects = 40;
  for (let r=0;r<rects;r++) {
    const rw = 4 + Math.floor(Math.random()*32);
    const rh = 4 + Math.floor(Math.random()*32);
    const rx = Math.floor(Math.random()*(width-rw));
    const ry = Math.floor(Math.random()*(height-rh));
    for (let y=0;y<rh;y++) {
      for (let x=0;x<rw;x++) {
        const gx = rx + x, gy = ry + y;
        const idx = (gy*width+gx)*4;
        arr[idx] = 255; arr[idx+1]=255; arr[idx+2]=255; arr[idx+3]=255;
      }
    }
  }
  return arr;
}

function bench(framesAcross=20, framesDown=10, tileW=32, tileH=32) {
  const sheetW = framesAcross*tileW;
  const sheetH = framesDown*tileH;
  const pixels = synthSheet(sheetW, sheetH);

  const totalFrames = framesAcross*framesDown;
  const trims: (ReturnType<typeof FrameAnalyzer.computeTrim>)[] = new Array(totalFrames);

  const trimTiming = run('trim', () => {
    for (let fy=0; fy<framesDown; fy++) {
      for (let fx=0; fx<framesAcross; fx++) {
        const idx = fy*framesAcross + fx;
        trims[idx] = FrameAnalyzer.computeTrim(pixels, tileW, tileH, sheetW, fx*tileW, fy*tileH, 1);
      }
    }
  });

  const strategies = ['bottom-center','center','top-left','top-right'] as const;
  const pivotTiming = run('pivot', () => {
    for (const strat of strategies) {
      for (let i=0;i<totalFrames;i++) {
        const frame = { x: (i%framesAcross)*tileW, y: Math.floor(i/framesAcross)*tileH, w: tileW, h: tileH };
        FrameAnalyzer.computePivot(trims[i], strat as any, frame);
      }
    }
  });

  const nonNull = trims.filter(t=>t).length;
  const report = {
    sheet: `${sheetW}x${sheetH}`,
    frames: totalFrames,
    trim_ms: trimTiming.ms,
    trim_avg_ms: trimTiming.ms/totalFrames,
    pivot_ms: pivotTiming.ms,
    pivot_avg_ms: pivotTiming.ms/(totalFrames*strategies.length),
    trims_found_pct: (nonNull/totalFrames)*100
  };
  console.log(JSON.stringify(report, null, 2));
}

bench();
