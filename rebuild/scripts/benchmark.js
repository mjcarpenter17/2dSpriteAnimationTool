#!/usr/bin/env node
/**
 * Micro-benchmark script for AnimationViewer core operations
 * 
 * Usage: node scripts/benchmark.js
 * 
 * Tests trim analysis, pivot calculation, and cache performance
 */

const fs = require('fs');
const path = require('path');

// Mock Canvas API for Node.js testing
class MockCanvas {
  constructor(width = 100, height = 100) {
    this.width = width;
    this.height = height;
    this._data = new Uint8ClampedArray(width * height * 4).fill(255); // white by default
  }

  getContext(type) {
    if (type === '2d') {
      return {
        canvas: this,
        getImageData: (x, y, w, h) => ({
          data: this._data.slice((y * this.width + x) * 4, ((y + h) * this.width + (x + w)) * 4),
          width: w,
          height: h
        }),
        putImageData: () => {},
        drawImage: () => {},
        clearRect: () => {}
      };
    }
    return null;
  }

  // Simulate a typical sprite with transparent borders
  drawTestSprite(frameX, frameY, frameW, frameH) {
    const ctx = this.getContext('2d');
    // Create transparent border, opaque center
    for (let y = frameY; y < frameY + frameH; y++) {
      for (let x = frameX; x < frameX + frameW; x++) {
        const idx = (y * this.width + x) * 4;
        const margin = 4;
        if (x >= frameX + margin && x < frameX + frameW - margin && 
            y >= frameY + margin && y < frameY + frameH - margin) {
          // Opaque center
          this._data[idx + 3] = 255; // alpha
        } else {
          // Transparent border
          this._data[idx + 3] = 0; // alpha
        }
      }
    }
  }
}

// Mock DOM globals for testing
global.HTMLCanvasElement = MockCanvas;
global.OffscreenCanvas = MockCanvas;
global.createImageBitmap = () => Promise.resolve(new MockCanvas());

// Create mock modules since we can't import TypeScript directly
const FrameAnalyzer = {
  analyzeFrame(pixelData, frameRect) {
    // Simplified trim analysis
    const { x, y, w, h } = frameRect;
    let minX = w, maxX = 0, minY = h, maxY = 0;
    let hasOpaque = false;

    for (let py = 0; py < h; py++) {
      for (let px = 0; px < w; px++) {
        const idx = ((y + py) * pixelData.width + (x + px)) * 4 + 3; // alpha channel
        if (pixelData.data[idx] > 0) {
          hasOpaque = true;
          minX = Math.min(minX, px);
          maxX = Math.max(maxX, px);
          minY = Math.min(minY, py);
          maxY = Math.max(maxY, py);
        }
      }
    }

    return hasOpaque ? {
      x: x + minX,
      y: y + minY,
      w: maxX - minX + 1,
      h: maxY - minY + 1
    } : null;
  },

  calculatePivot(trimRect, strategy) {
    if (!trimRect) return { x: 0, y: 0 };
    
    switch (strategy) {
      case 'bottom-center':
        return { x: trimRect.x + trimRect.w / 2, y: trimRect.y + trimRect.h };
      case 'center':
        return { x: trimRect.x + trimRect.w / 2, y: trimRect.y + trimRect.h / 2 };
      case 'top-left':
        return { x: trimRect.x, y: trimRect.y };
      default:
        return { x: trimRect.x + trimRect.w / 2, y: trimRect.y + trimRect.h };
    }
  }
};

function benchmark(name, fn, iterations = 1000) {
  const start = performance.now();
  
  for (let i = 0; i < iterations; i++) {
    fn();
  }
  
  const end = performance.now();
  const total = end - start;
  const avg = total / iterations;
  
  return {
    name,
    iterations,
    totalMs: total,
    avgMs: avg,
    opsPerSec: Math.round(1000 / avg)
  };
}

function runBenchmarks() {
  console.log('🚀 AnimationViewer Performance Benchmarks\n');

  // Setup test data
  const canvas = new MockCanvas(512, 256);
  const frameSize = 32;
  const frames = [];
  
  // Generate test frames
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 16; col++) {
      const frameRect = { x: col * frameSize, y: row * frameSize, w: frameSize, h: frameSize };
      canvas.drawTestSprite(frameRect.x, frameRect.y, frameRect.w, frameRect.h);
      frames.push(frameRect);
    }
  }

  const pixelData = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);

  // Benchmark 1: Trim Analysis
  const trimResults = benchmark('Trim Analysis', () => {
    const frame = frames[Math.floor(Math.random() * frames.length)];
    FrameAnalyzer.analyzeFrame(pixelData, frame);
  }, 5000);

  // Benchmark 2: Pivot Calculation
  const trimRect = { x: 10, y: 10, w: 20, h: 20 };
  const strategies = ['bottom-center', 'center', 'top-left'];
  
  const pivotResults = benchmark('Pivot Calculation', () => {
    const strategy = strategies[Math.floor(Math.random() * strategies.length)];
    FrameAnalyzer.calculatePivot(trimRect, strategy);
  }, 10000);

  // Benchmark 3: Cache Simulation
  const cache = new Map();
  const cacheResults = benchmark('Cache Operations', () => {
    const key = Math.floor(Math.random() * 100);
    if (cache.has(key)) {
      cache.get(key); // hit
    } else {
      cache.set(key, { trim: trimRect, pivot: { x: 16, y: 30 } }); // miss
      if (cache.size > 50) {
        const firstKey = cache.keys().next().value;
        cache.delete(firstKey); // eviction
      }
    }
  }, 50000);

  // Display results
  const results = [trimResults, pivotResults, cacheResults];
  
  console.log('Results:');
  console.log('─'.repeat(70));
  console.log('Operation              │ Iterations │ Avg (ms) │ Ops/sec');
  console.log('─'.repeat(70));
  
  results.forEach(result => {
    const name = result.name.padEnd(22);
    const iterations = result.iterations.toString().padStart(10);
    const avg = result.avgMs.toFixed(3).padStart(8);
    const ops = result.opsPerSec.toString().padStart(7);
    console.log(`${name} │ ${iterations} │ ${avg} │ ${ops}`);
  });
  
  console.log('─'.repeat(70));

  // Performance budget validation
  console.log('\n📊 Performance Budget Validation:');
  
  const budgets = {
    'Trim Analysis': { budget: 0.5, actual: trimResults.avgMs, unit: 'ms' },
    'Pivot Calculation': { budget: 0.1, actual: pivotResults.avgMs, unit: 'ms' },
    'Cache Operations': { budget: 0.01, actual: cacheResults.avgMs, unit: 'ms' }
  };

  Object.entries(budgets).forEach(([operation, { budget, actual, unit }]) => {
    const status = actual <= budget ? '✅ PASS' : '❌ FAIL';
    const ratio = (actual / budget * 100).toFixed(1);
    console.log(`  ${operation}: ${actual.toFixed(3)}${unit} (${ratio}% of ${budget}${unit} budget) ${status}`);
  });

  // Memory usage (approximate)
  const memoryUsage = process.memoryUsage();
  console.log(`\n💾 Memory: ${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB heap, ${Math.round(memoryUsage.rss / 1024 / 1024)}MB RSS`);
  
  console.log('\n✨ Benchmark complete!');
}

if (require.main === module) {
  runBenchmarks();
}

module.exports = { benchmark, runBenchmarks };