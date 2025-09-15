# Cache Invalidation Policy

This document describes the caching strategy and invalidation rules for AnimationViewer's analysis cache system.

## Cache Architecture

### Layered Cache Structure
1. **Sheet-level Pixel Buffer**: Raw RGBA data extracted once per sheet
2. **Per-frame Analysis Cache**: Maps `frameIndex -> {trim, pivot}` computed lazily
3. **Override Registry**: Manual user edits take precedence over auto-computed values

### Cache Keys
- **Pixel Buffer**: Keyed by `sheetPath` (full file path)
- **Frame Analysis**: Keyed by `sheetPath + frameIndex`
- **Overrides**: Keyed by `sheetPath + frameIndex + overrideType`

## Invalidation Rules

### Automatic Invalidation Triggers

| Trigger | What Gets Invalidated | Reason |
|---------|----------------------|---------|
| **Grid Parameter Change** | All frame analysis for affected sheet | Frame rectangles shift, making cached analysis invalid |
| **Pivot Strategy Change** | Only pivot values (trim preserved) | Trim bounds stay the same, but pivot calculation method changes |
| **Sheet Reload/Open** | Entire cache for that sheet path | New image data requires fresh analysis |
| **App Restart** | All in-memory caches | Cache is not persisted between sessions |

### Selective Invalidation

**Grid Parameter Changes:**
```typescript
// When tile size, margin, or spacing changes
activeSheet.sheet.setParams({ tileWidth: newValue });
appState.cache.invalidateSheet(sheetPath); // Clear all frame analysis
appState.overrides.getSheet(sheetPath).pruneInvalid(idx => idx < newFrameCount);
```

**Pivot Strategy Changes:**
```typescript
// When user selects different pivot strategy
appState.cache.invalidatePivots(sheetPath); // Keep trim, clear pivot only
```

### Manual Override Behavior

Manual overrides **never invalidate** auto-computed values:
- Auto values remain cached for fallback
- Precedence system chooses override when present
- Clearing override reveals auto value without recomputation

## Performance Characteristics

### Cache Hit Scenarios
- ✅ **Overlay Toggle**: Switching trim/pivot overlays on/off (reads cached values)
- ✅ **Frame Navigation**: Moving selection within same sheet
- ✅ **Undo/Redo Override**: Manual edit operations reference cached auto values

### Cache Miss Scenarios  
- ❌ **First Overlay Request**: Initial analysis computation required
- ❌ **Post-Grid-Change**: Analysis invalid after parameter modification
- ❌ **New Sheet Load**: No prior analysis exists

## Memory Management

### Eviction Policy
- **No LRU eviction** currently implemented (acceptable for typical sheet counts)
- **Sheet removal** clears associated cache entries
- **App restart** clears all caches (no persistence)

### Size Estimation
- **Pixel Buffer**: ~4 bytes/pixel (RGBA)
  - 1024×1024 sheet = ~4MB
- **Frame Analysis**: ~32 bytes/frame (trim + pivot objects)
  - 100 frames = ~3KB
- **Total for large project**: ~25MB for 5 sheets with analysis

## Future Improvements

### Planned Optimizations
1. **Visible-frame-only analysis**: Only analyze frames currently in viewport
2. **Persistence layer**: Save analysis results to avoid recomputation between sessions
3. **Memory limits**: Implement LRU eviction when cache exceeds threshold
4. **Background analysis**: Pre-compute analysis for likely-to-be-accessed frames

### Performance Monitoring
Use `npm run benchmark` to validate cache performance against budgets:
- Trim analysis: <0.5ms per frame
- Pivot calculation: <0.1ms per frame  
- Cache operations: <0.01ms per access

## Implementation Notes

### Thread Safety
- All cache operations occur on main thread (Electron renderer)
- No synchronization required for current architecture

### Error Handling
- Invalid pixel data results in null trim (graceful fallback)
- Missing cache entries trigger on-demand computation
- Corrupted cache state clears affected sheet automatically

### Debugging
Enable performance monitoring:
```typescript
import { perfMonitor } from '../core/PerformanceMonitor';
perfMonitor.setEnabled(true);
// ... perform operations ...
perfMonitor.logStats(); // View cache hit rates and timing
```