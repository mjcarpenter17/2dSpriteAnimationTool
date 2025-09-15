/**
 * Simple performance monitoring utility for AnimationViewer
 * Tracks operation timing and cache hit rates
 */

interface PerfEntry {
  operation: string;
  startTime: number;
  duration?: number;
}

interface CacheStats {
  hits: number;
  misses: number;
  invalidations: number;
}

export class PerformanceMonitor {
  private entries: Map<string, PerfEntry> = new Map();
  private completedOps: { operation: string; duration: number; timestamp: number }[] = [];
  private cacheStats: Map<string, CacheStats> = new Map();
  private enabled = false;

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  startOperation(operation: string): void {
    if (!this.enabled) return;
    this.entries.set(operation, {
      operation,
      startTime: performance.now()
    });
  }

  endOperation(operation: string): number {
    if (!this.enabled) return 0;
    
    const entry = this.entries.get(operation);
    if (!entry) return 0;

    const duration = performance.now() - entry.startTime;
    entry.duration = duration;
    
    this.completedOps.push({
      operation,
      duration,
      timestamp: Date.now()
    });

    // Keep only last 1000 operations to prevent memory growth
    if (this.completedOps.length > 1000) {
      this.completedOps = this.completedOps.slice(-500);
    }

    this.entries.delete(operation);
    return duration;
  }

  recordCacheHit(cacheType: string): void {
    if (!this.enabled) return;
    
    const stats = this.cacheStats.get(cacheType) || { hits: 0, misses: 0, invalidations: 0 };
    stats.hits++;
    this.cacheStats.set(cacheType, stats);
  }

  recordCacheMiss(cacheType: string): void {
    if (!this.enabled) return;
    
    const stats = this.cacheStats.get(cacheType) || { hits: 0, misses: 0, invalidations: 0 };
    stats.misses++;
    this.cacheStats.set(cacheType, stats);
  }

  recordCacheInvalidation(cacheType: string): void {
    if (!this.enabled) return;
    
    const stats = this.cacheStats.get(cacheType) || { hits: 0, misses: 0, invalidations: 0 };
    stats.invalidations++;
    this.cacheStats.set(cacheType, stats);
  }

  getOperationStats(operation: string): { count: number; avgDuration: number; maxDuration: number } {
    const ops = this.completedOps.filter(op => op.operation === operation);
    if (ops.length === 0) return { count: 0, avgDuration: 0, maxDuration: 0 };

    const durations = ops.map(op => op.duration);
    return {
      count: ops.length,
      avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
      maxDuration: Math.max(...durations)
    };
  }

  getCacheStats(cacheType: string): CacheStats | null {
    return this.cacheStats.get(cacheType) || null;
  }

  getAllStats(): { operations: any[]; caches: any[] } {
    const operations = Array.from(new Set(this.completedOps.map(op => op.operation)))
      .map(op => ({ operation: op, ...this.getOperationStats(op) }));

    const caches = Array.from(this.cacheStats.entries())
      .map(([type, stats]) => ({
        type,
        ...stats,
        hitRate: stats.hits + stats.misses > 0 ? stats.hits / (stats.hits + stats.misses) : 0
      }));

    return { operations, caches };
  }

  reset(): void {
    this.entries.clear();
    this.completedOps = [];
    this.cacheStats.clear();
  }

  /**
   * Log current performance stats to console
   */
  logStats(): void {
    if (!this.enabled) {
      console.log('[Perf] Performance monitoring disabled');
      return;
    }

    const { operations, caches } = this.getAllStats();
    
    console.group('[Perf] Performance Statistics');
    
    if (operations.length > 0) {
      console.log('Operations:');
      operations.forEach(op => {
        console.log(`  ${op.operation}: ${op.count} calls, avg ${op.avgDuration.toFixed(2)}ms, max ${op.maxDuration.toFixed(2)}ms`);
      });
    }

    if (caches.length > 0) {
      console.log('Cache Performance:');
      caches.forEach(cache => {
        console.log(`  ${cache.type}: ${(cache.hitRate * 100).toFixed(1)}% hit rate (${cache.hits}/${cache.hits + cache.misses}), ${cache.invalidations} invalidations`);
      });
    }

    console.groupEnd();
  }
}

// Global instance
export const perfMonitor = new PerformanceMonitor();

/**
 * Convenience decorator for timing functions
 */
export function timed(operation: string) {
  return function<T extends (...args: any[]) => any>(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = function(...args: any[]) {
      perfMonitor.startOperation(operation);
      try {
        const result = originalMethod.apply(this, args);
        return result;
      } finally {
        perfMonitor.endOperation(operation);
      }
    };
    
    return descriptor;
  };
}