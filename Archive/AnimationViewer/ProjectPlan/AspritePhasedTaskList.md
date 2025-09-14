# Phased Task List – Aseprite Integration & Modernization

This expands the high‑level overview into concrete, testable tasks. Each phase delivers independent value and keeps manual mode functional.

Legend: (P) = Priority, (E) = Estimated complexity (S/M/L), (★) = Success checkpoint

---
## Phase 1 – Parser & Preference Toggle
Goal: Foundational Aseprite JSON ingestion gated by a user preference.

| ID | Task | Details | Done When (Acceptance) |
|----|------|---------|------------------------|
| 1.1 | Create `aseprite_loader.py` | Implement classes & dataclasses described in overview | Running `python aseprite_loader.py <json>` prints summary (★) |
| 1.2 | Validation routines | Bounds checks, missing keys fallback, direction normalization | Malformed JSON logs warning; app does not crash |
| 1.3 | Add preference key | `use_aseprite_json` default false (or true—decide) in `PreferencesManager` | Key persisted; visible in raw prefs file |
| 1.4 | Preferences UI toggle | Checkbox in Preferences dialog + View menu item mirror | Toggling value updates config instantly |
| 1.5 | Auto-detect JSON on PNG load | If enabled & `<basename>.json` exists, schedule parse | Status bar: "Loaded Aseprite metadata" |
| 1.6 | Manual JSON import menu item | File > Import Aseprite JSON... | Selecting file triggers parse & logs summary |
| 1.7 | Logging / status reporting | Consolidated helper: `report_aseprite_summary()` | Summary shows counts: frames, animations, image path |

Dependencies: Basic knowledge of existing preferences and menu frameworks.
Risks: Overwriting existing manual sheet state (avoid—just augment for now).

---
## Phase 2 – Animation Source Adapter & UI Listing
Goal: Surfacing Aseprite animations alongside manual ones (read‑only).

| ID | Task | Details | Acceptance |
|----|------|---------|------------|
| 2.1 | Define `IAnimationSource` protocol | Lightweight interface / abstract base | Two implementations compile (manual, aseprite) |
| 2.2 | Build `AsepriteAnimationSource` | Wrap loader output to produce `AnimationDescriptor` objects | Source exposes list with correct counts |
| 2.3 | Integrate with AnimationsPane | Merge sources; mark Aseprite entries read-only | Aseprite animations appear with [A] tag/icon |
| 2.4 | Selection handling | Selecting Aseprite animation loads correct spritesheet (tab) | Frame highlight triggered for selection |
| 2.5 | Read-only guard | Disable delete/rename on Aseprite entries | Attempting modification shows non-destructive notice |
| 2.6 | Refresh mechanism | Re-parse JSON on user command | Menu action updates modified file instantly |

---
## Phase 3 – Playback Timing & Directions
Goal: Accurate timing and support for forward/reverse/pingpong.

| ID | Task | Details | Acceptance |
|----|------|---------|------------|
| 3.1 | Implement `AnimationPlaybackController` | Time-accumulator architecture | Controller cycles frames exactly per durations |
| 3.2 | Direction strategy | Reverse list or dynamic index; pingpong bounce | Visual test shows correct bounce behavior |
| 3.3 | Hook into preview | Add simple preview panel or repurpose existing area | Preview shows runtime FPS/elapsed info |
| 3.4 | Pause / step controls (optional) | Keyboard shortcuts: Space (pause), Arrow keys (step) | Works without affecting manual workflows |
| 3.5 | Performance test | Long sequence handling (≥200 frames) | No perceptible stutter at 60 FPS |

---
## Phase 4 – Export Conversion Pipeline
Goal: Convert Aseprite animations into internal/game format (JSON + Python).

| ID | Task | Details | Acceptance |
|----|------|---------|------------|
| 4.1 | Define target schema alignment | Map trimming + durations + direction | Documented mapping table in code header |
| 4.2 | Implement converter function | `convert_aseprite_animation(descriptor)` | Returns dict matching internal exporter use |
| 4.3 | Batch export UI | Dialog: select animations to convert | Multiple selections produce N outputs |
| 4.4 | Integrate with existing exporter | Reuse progress dialog | Progress shows cumulative frames exported |
| 4.5 | Verify duration accuracy | Compare sum durations vs input (±1 ms) | Logged check passes (★) |

---
## Phase 5 – Pivot Strategies & Slices
Goal: Add pivot logic & slice (hitbox/pivot) ingestion for richer data.

| ID | Task | Details | Acceptance |
|----|------|---------|------------|
| 5.1 | Pivot strategy enum | CENTER, BOTTOM_CENTER, CUSTOM, SLICE | Preference / dropdown persists |
| 5.2 | Compute default pivots | Based on chosen strategy per animation | Preview overlay shows pivot point |
| 5.3 | Parse slices array | Map named slices; identify pivot slice (e.g., `pivot`) | When slice exists, pivot overrides default |
| 5.4 | Export pivot data | Include pivot (px,py) in exported JSON | Exported file contains pivot fields |
| 5.5 | Fallback logic | Missing slice → fallback strategy | Logged clearly once per load |

---
## Phase 6 – Batch & QoL Enhancements
Goal: Scalability and ergonomics for larger libraries.

| ID | Task | Details | Acceptance |
|----|------|---------|------------|
| 6.1 | Directory scan import | Scan folder tree for `*.json` w/ images | Summary dialog: total sources imported |
| 6.2 | Duplicate name resolution | Namespace or suffix policy | No collisions cause overwrite silently |
| 6.3 | Search/filter UI | Filter animations by name/source/type | Real-time filter response <50ms |
| 6.4 | Live reload (optional) | Poll mtime or FS watch (platform-limited) | Editing JSON and saving refreshes entries |
| 6.5 | Caching layer | Hash JSON to skip reparsing | Repeat import < 5ms |

---
## Phase 7 – Advanced / Stretch Goals
Goal: Deep inspection & productivity boosters.

| ID | Task | Details | Acceptance |
|----|------|---------|------------|
| 7.1 | Trim visualization overlay | Show trimmed vs logical bounds | Toggle key cycles overlay modes |
| 7.2 | Slice visualization | Draw rectangles for hitboxes | Color legend displayed |
| 7.3 | CLI batch mode | Headless conversion tool | `python tools\batch_convert.py <dir>` outputs logs |
| 7.4 | Round-trip exporter (optional) | Export simplified Aseprite-like JSON | File loads cleanly back into tool |
| 7.5 | Analytics / metrics | Frame usage, total time per animation | Summary panel aggregated stats |

---
## Cross-Cutting Concerns
| Concern | Action |
|---------|--------|
| Error Isolation | Never crash UI on parse failure; log & continue |
| Performance | Avoid per-frame allocations in playback controller |
| UX Clarity | Clear badges for Aseprite vs manual sources |
| Accessibility | Keyboard shortcuts for toggle & playback control |
| Testing | Self-test harness for parser + timing accuracy checks |

---
## Risk Mitigation
| Risk | Mitigation |
|------|-----------|
| Pingpong logic off-by-one | Dedicated unit test: ensure endpoints not duplicated unless intended |
| Large JSON lag | Pre-parse in thread (future) or cache hash | 
| Name collisions | Namespace tagging `[A]` + suffix strategy |
| Trimming mismatch vs expectation | Overlay visualization (Phase 7) |

---
## Suggested Implementation Order (Fine-Grained)
1. Phase 1 complete (parser + toggle) – unlocks early validation on real assets.
2. Phase 2 (adapter) – visible user value.
3. Phase 3 (timing/directions) – correctness & fidelity.
4. Phase 4 (export) – integration with existing pipeline.
5. Phase 5 (pivots) – accuracy for gameplay alignment.
6. Phase 6 (batch/QoL) – scalability.
7. Phase 7 (visualization/advanced) – polish & pro tooling.

---
## Completion Definition
Project considered MVP complete at end of Phase 4 (parser + UI + timing + export). Phases 5–7 elevate professional depth.

---
## Maintenance Notes
- Keep Aseprite parsing isolated (single module) for future replacement.
- Document schema assumptions in code comments referencing Aseprite docs version.
- Provide fallback for missing keys to allow partially hand-edited JSON.

---
Generated to align directly with `ProjectOverview.md`. Update both documents together if scope shifts.
