# AnimationViewer Aseprite Integration & Modernization Project Overview

## 1. Vision
Transform AnimationViewer from a manual frame selection utility into a hybrid, standards-aligned animation inspection and conversion tool that natively understands Aseprite exports while preserving a powerful manual mode. The application will seamlessly ingest `.json + .png` pairs exported by Aseprite, auto-populate animations (tags), respect per-frame timing, trimming, and optional future slices/pivots, and allow exporting / converting to the project’s existing or game‑specific formats.

## 2. Core Goals
1. First‑class Aseprite JSON support (frameTags, durations, trimming, directions).
2. Hybrid operation: "Aseprite Mode" (auto) and "Manual Mode" (current workflow) toggleable via Preferences & View/Animation menu.
3. Architecture refactor to introduce a pluggable Animation Source layer (Aseprite, Manual, Future Sources).
4. Playback system upgrade to variable per-frame timing & direction policies (forward, reverse, pingpong).
5. Export / conversion pipeline: Aseprite → Internal JSON/Python format (and potentially reverse for round‑trip compatibility).
6. Enhanced metadata handling: trimming offsets, baseline/pivot strategies, optional slices/hitboxes later.
7. Non-breaking adoption: existing users keep current manual workflows; new users gain immediate value via Aseprite ingestion.

## 3. High-Level Functional Outcomes
| Feature | Before | After |
|---------|--------|-------|
| Animation Discovery | Manual folders | Auto via Aseprite JSON tags + manual fallback |
| Frame Timing | Uniform / implicit | Per-frame duration (ms) |
| Trimming | Proprietary logic only | Native Aseprite trimming + existing analyzer |
| Pivot / Baseline | Heuristic only | Strategy-based (center, baseline, slice-based future) |
| Directions | Implied forward | forward / reverse / pingpong |
| Export | Manual selection only | Auto convert Aseprite tags + manual selection |
| Multi-source | Not formalized | Pluggable animation sources registry |

## 4. Architectural Additions
### 4.1 Animation Source Layer
Introduce interfaces / lightweight protocol so UI consumes unified objects regardless of source.
- `IAnimationSource`: loads, enumerates, invalidates, refreshes animations.
- `AnimationDescriptor`: name, frames[], frame_durations[], direction, source_type, read_only flag.
- `FrameDescriptor`: atlas_rect, source_size, sprite_source_offset, pivot, duration_ms.

Sources Initially:
- `ManualAnimationSource` (wraps existing AnimationManager/folder scanning)
- `AsepriteAnimationSource` (new; parses JSON)

### 4.2 Aseprite Parsing Module
File: `aseprite_loader.py`
Responsibilities:
- Parse JSON safely (validation & error surfaces without crashing UI)
- Normalize frame ordering (preserve deterministic iteration order)
- Build frame index list, tag → frame index spans
- Expand or lazily interpret direction policies (decide at playback layer)
- Provide trimming offsets & atlas rects
- Resolve image path relative to JSON

### 4.3 Playback Engine Enhancement
Enhance (or add) `AnimationPlaybackController`:
- Accept variable frame durations array (ms)
- Time accumulator update model instead of fixed frame step
- Direction handling strategies: generate sequence once (expanded) OR dynamic index walker with bounce state (for pingpong)
- Pause / step / loop flags (future)

### 4.4 Preferences & Mode Toggle
Preference key: `use_aseprite_json` (bool, default true if JSON present on load?).
Menu Integration:
- View → "Use Aseprite JSON Data" (checkbox mirrors preference)
- Animation → "Reload Aseprite Animations" (force re-parse)

### 4.5 UI Integration Changes
Animations Pane:
- Distinguish Aseprite animations (icon, color stripe, or suffix `[A]`).
- Read-only indicator (lock icon) to prevent editing frames in Aseprite mode.
- Tooltip: source, frame count, total duration.
- Mixed listing order: group by source OR configurable grouping (Phase 2+).

Tabs / Multi‑Sheet Behavior:
- Opening an Aseprite JSON auto-creates (or focuses) its associated spritesheet tab.
- If a PNG is opened and a same‑basename JSON exists: optionally prompt, or auto-ingest if preference enabled.

### 4.6 Export / Conversion Pipeline
Command: "Export Aseprite Animation(s) → Game Format".
Export Data Includes:
- Frames with atlas coordinates and/or logical untrimmed references
- Durations array
- Direction policy encoded
- Pivot baseline or slice pivot

Potential Phase 2+: Round-trip partial generation of simplified Aseprite-like JSON for manual animations (optional).

## 5. Incremental Phasing Strategy
Phase 1: Parser & Toggle
- Implement `aseprite_loader.py` + validation
- Preference flag & menu item
- Basic parse log output & console inspection

Phase 2: Adapter & Display
- `AsepriteAnimationSource` delivering descriptors
- Animations Pane shows Aseprite sets (read-only)
- Selecting animation highlights frames in center (if sheet loaded)

Phase 3: Playback Timing + Directions
- Variable timing interpolation
- Support forward, reverse, pingpong (deferred expansion vs dynamic index)
- UI: basic animation preview region (optional) or reuse existing

Phase 4: Export Conversion
- Convert one or all Aseprite animations to internal JSON/Python
- Include trimming offsets and pivot metadata

Phase 5: Pivot Strategies & Slices
- Introduce pivot selection strategies (Center, BottomCenter, Custom Offset)
- Parse `slices` array when present (future assets)
- Provide slice-based pivots/hitboxes in export

Phase 6: Batch & Quality of Life
- Batch import folder scanning for all `*.json` with images
- Conflict resolution (duplicate animation names)
- UI filtering/search

Phase 7: Advanced Tooling (Optional)
- Live reload when JSON changes (mtime watch)
- Frame overlay visualization: trim box vs original bounds
- Performance profiling & caching layer (hash JSON to avoid reparsing)

## 6. Data Model Definitions (Draft)
```text
AnimationDescriptor
  name: str
  frames: list[FrameDescriptor]
  direction: DirectionPolicy (FORWARD|REVERSE|PINGPONG)
  total_duration_ms: int
  source_type: str ("aseprite" | "manual")
  read_only: bool

FrameDescriptor
  atlas_rect: (x,y,w,h)
  source_size: (w,h)
  source_offset: (ox,oy)  # from spriteSourceSize
  duration_ms: int
  pivot: (px,py)
```

## 7. Error Handling & Validation
- JSON parse failures: status bar warning + skip source (keep app functional)
- Missing image file: mark animations disabled (grayed out) until corrected
- Tag index out of bounds: log and skip offending tag
- Duplicate tag names: auto-suffix `_1`, `_2` or warn user

## 8. Performance Considerations
- Parsing is cheap (single JSON). On bulk: implement lazy parse or cache.
- Frame highlight mapping: store (row,col) translation only if sheet grid known; fallback to atlas rect bounding boxes overlay (future enhancement) if gridless.
- Potential memory improvement: store frames once, animations reference by index.

## 9. Backward Compatibility
- Manual mode completely untouched unless toggle enabled.
- Existing animation save/export functions remain valid.
- Aseprite pipeline is additive; no regression for legacy workflows.

## 10. Security / Robustness
- Sanitize file paths, avoid executing arbitrary content
- Graceful handling of malformed numbers (coerce or default)
- Strict type checks when building descriptors

## 11. Testing Strategy
Smoke Tests:
- Load known valid Assassin.json; verify animation count & frame durations
- Toggle preference off: Aseprite animations disappear
- Introduce malformed frameTag index: ensure skip and log
Unit-ish Self Checks (dev mode):
- `aseprite_loader.py` can run standalone and print summary
Playback Tests:
- Verify pingpong sequence length/time vs expected
Export Tests:
- Ensure exported JSON matches expected schema & sums durations

## 12. Future Enhancements (Parking Lot)
- Slice-based hitbox / hurtbox preview overlays
- Blend multiple sources into composite meta-animations
- Auto-detect pivot from silhouette analysis (fallback to Aseprite slice when missing)
- Real-time reload watcher (filesystem events)
- Scriptable batch conversion CLI mode

## 13. Success Criteria
- Load Assassin Aseprite JSON: animations appear instantly without manual selection
- Correct per-frame timing reflected in preview (observable speed differences if varied)
- Pingpong/reverse honored
- Exported internal animation retains trimming offsets & total duration within 1% of Aseprite sum
- Manual workflow unaffected when toggle off

## 14. Glossary
- Atlas Rect: Position/size of trimmed frame in packed spritesheet image.
- Source Size: Original untrimmed logical frame dimensions.
- Source Offset (spriteSourceSize x,y): Placement of trimmed rect within logical space.
- Direction Policy: How frames are iterated (forward/reverse/pingpong).

---
This document guides implementation sequencing and architectural cohesion. See `PhasedTaskList.md` for actionable task breakdown and acceptance criteria.
