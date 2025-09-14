# Rebuild Execution Tasklist (Active & Comprehensive)

Derived from `PRIME_TASKLIST.md` + project overview. This is the authoritative implementation checklist with granular tasks, statuses, and exit criteria. Maintain continuously.

## Phase 0 – Environment Setup (DONE)
- Stack selected (Electron + TS + React) – see DECISIONS.md.
- Scaffold running window & tooling (Vite + esbuild) complete.

## Phase 1 – Core Window & UI Skeleton (DONE)
- Main window + three panels + status bar.
- Preferences persistence (window size, recent sheets, last active sheet, pivot strategy).
- File open dialog (PNG) + recent list.
- Grid rendering with live parameter edits (tile size, margin, spacing).
- Frame selection (Ctrl+Click, Shift+Click) with order + Ctrl+A / Ctrl+D.

Evidence: Working renderer layout, selection visuals, persisted prefs file.

## Phase 2 – Core Logic & View Integration (IN PROGRESS)

### Completed (Current State)
- FrameAnalyzer (auto trim + pivot strategies: bottom-center, center, top-left, top-right)
- Zoom & pan (Ctrl+Wheel / +/- / 0, middle drag / Alt+Left drag)
- Animation creation from selection + forward looping playback preview
- Multi-sheet tabs + last active sheet restore (prefs)
- Analysis overlays (Trim / Pivot) with lazy per-sheet cache
- Pivot strategy selector + selective pivot cache invalidation & persistence
- Manual pivot overrides: drag + numeric inputs (X/Y, Auto, Clear) with persistence
- Trim overrides: create (Ctrl+Click), move, resize handles, visual diff (amber), persistence
- Auto Trim+Pivot batch action (selection)
- Undo/Redo scaffold: pivot + trim + slice ops (Ctrl+Z / Ctrl+Y)
- Helpers master toggle (H), Esc cancel active drag, arrow key navigation (with Shift range select)
- Slice system: SliceStore model, create (Shift+Click), select/move/resize/delete, color placeholder, undo coverage
- Status bar feedback + cursor differentiation for interaction modes
- Overrides versioned persistence (`__version`) + skip-on-mismatch safety + decision log entries
- Tests: pivot precedence, trim override vs auto, transparent frame null trim edge case
- Strict null safety adjustments in renderer hot paths (frameRect guards)

### Remaining for Phase 2 Closure
1. Animations Pane enhancements: Refresh (F5), read-only badge placeholder, grouping stub
2. Playback refinements: non-loop stop behavior, per-frame duration editing UI polish (list present but finalize UX) 
3. Performance / caching: document cache invalidation policy + optional micro-benchmark script
4. Persistence pruning strategy implementation (stale sheet overrides) – stub exists
5. Additional tests: slice persistence & basic undo round‑trip (optional stretch)
6. Minor UX polish: tooltips for overridden vs auto values, slice color/type legend stub

### Exit Criteria (Tracked)
- [x] Manual pivot + trim overrides stable & persisted
- [x] Slice model + manual slice creation/edit/delete + rendering
- [ ] Animations pane refresh & read-only badge functional
- [ ] Adjustable per-frame durations & non-loop stop behavior
- [x] Shortcut parity (Ctrl+A/D, T, P, H, zoom, arrows, Esc) (F5 pending)
- [x] Tests: analyzer / overrides precedence / transparent frame edge
- [ ] Slice basic test (persist + undo) (optional before final sign‑off)

### Phase 2 Interim Summary (Evidence)
Implemented end-to-end editing vertical slices for pivot, trim, and slices with undo/redo and persistent, versioned overrides. Established analysis cache invalidation pattern (pivot strategy switch) and added automated tests confirming override precedence and null-trim edge behavior. Remaining closure items are UI affordances (refresh, badges), playback refinement (non-loop stop & duration editor polish), and minor persistence / performance housekeeping. No blocking technical debt; risk of scope creep mitigated by deferring advanced slice coloration & grouping to Phase 6.

## Phase 3 – Aseprite Integration (NOT STARTED)

Tasks:
1. Preferences toggle `advanced.use_aseprite_json`
2. Auto-detect JSON `<basename>.json` when PNG opened (if enabled)
3. Parser Implementation
	- Frames (rect, duration)
	- frameTags → animations
	- slices timeline ingestion
	- layers list & fallback from frame names
	- meta.pixelRatio capture
4. AnimationSource Architecture
	- Define interface & registry (manual + aseprite sources)
	- Read-only enforcement for Aseprite source
5. Animations Pane Integration (merged source list w/ badges)
6. Validation & Error Handling (missing frames, mismatched sizes)
7. Pixel ratio-aware rendering scaling
8. Tests (fixtures: normal, missing slices, corrupt JSON)
9. Decision entry: plugin boundary error policy

Exit Criteria:
- Opening PNG+JSON populates animations, slices, layers, pixel ratio
- Read-only Aseprite animations visually distinguished
- Parser tests & error handling scenarios covered

## Phase 4 – Playback Engine Expansion (PARTIAL)

Existing: Forward loop playback.

Tasks:
1. Playback modes: reverse, ping-pong, once
2. speedScale per animation (playback modifier)
3. Timeline scrubber UI + frame seeking
4. Onion skinning (N previous/next frames, adjustable N & opacity)
5. Spacebar play/pause shortcut
6. Step frame keys (',' and '.')
7. Performance harness (ensure ≥55 FPS worst-case 200 frames)
8. Tests: direction sequences, ping-pong correctness, speed scaling precision
9. Decision entry: onion skin render method (offscreen vs inline)

Exit Criteria:
- All playback modes & scrubber functional
- Onion skin meets performance budget

## Phase 5 – Export Pipeline (NOT STARTED)

Tasks:
1. Export builder (ordered keys per policy)
2. Resolve ids to concrete rect/trim/pivot data
3. Merge overrides precedence (manual over auto)
4. Slice timeline export formatting
5. Layer list + visibility flags output
6. Batch export UI + progress indicator
7. Export settings dialog (output path, naming pattern)
8. Golden fixture tests & deterministic diff verification
9. Performance test (50 animations < 8s)
10. Error messaging & retry options
11. Decision entry: schema versioning changes (if any)

Exit Criteria:
- Single & batch export produce deterministic, validated JSON
- Tests pass & performance within budget

## Phase 6 – Advanced Features (NOT STARTED)

Tasks:
1. Undo/Redo System
	- Command core, stack size policy, grouping
	- Commands: grid params, selection, pivot/trim, slice ops, duration edits
2. Layer Support
	- Visibility toggles & filtering in playback/overlays
	- Layer-specific pivot strategy (optional)
3. Advanced Slice Management
	- Multi-select slice edit & bulk operations
	- Slice type editing + legend panel
	- Copy/paste slices across frames/animations
4. Pixel Aspect Ratio rendering in grid & preview
5. Advanced Export Profiles (engine-specific transforms)
6. Custom metadata injection UI (key-value)
7. UI Polish & Theming (panel resizing, dark/light theme toggle)
8. Timeline enhancements (drag reorder frames, frame duplication)
9. Performance HUD (FPS, cache hit rate, memory) + Perf.mark instrumentation
10. CLI / batch processing (headless export) optional
11. Security: sandbox plugin FS access boundaries
12. Decision entries: undo memory policy, layer filter strategy

Exit Criteria:
- Undo/redo stable across primary edit operations
- Layers & advanced slices fully integrated & exported
- Pixel ratio, performance HUD, theming present

## Cross-Cutting & Continuous Tasks
1. Testing & QA
	- ≥80% branch coverage core + parser
	- Integration workflow tests (open → edit → export)
2. TypeScript Hardening
	- Enable strict; eliminate implicit any in renderer
	- IPC channel typings in `global.d.ts`
3. Lint / Format Automation
	- Pre-commit hook (lint, test:fast)
4. Documentation
	- Keep overview + schema sections updated
	- DECISIONS.md entries for each new architecture choice
	- Add CONTRIBUTING.md, THIRD_PARTY.md, CHANGELOG.md (when releases start)
5. CI/CD
	- GitHub Actions: lint, test-fast, test-full, package build
	- Artifacts: coverage, sample exports
6. Performance Budgets
	- Micro-bench scripts (trim, parse, export)
	- Threshold assertions (fail CI on regression)
7. Error Handling & Logging
	- Central error boundary component
	- Structured logs (timestamp subsystem level message)
8. Asset Management
	- CC0 sample sheets + attribution README
9. Security & Validation
	- JSON schema validation (Aseprite + export)
	- Path sanitization for plugins/resources
10. Release Engineering
	- Packaging scripts (Win/macOS/Linux)
	- Semantic version tags & CHANGELOG
11. Performance Monitoring
	- Idle frame time metric collection & reporting

## Status Overview
| Phase | Status      | Notes |
|-------|-------------|-------|
| 0     | DONE        | Stack & scaffold complete |
| 1     | DONE        | Core shell + selection |
| 2     | IN PROGRESS | Overrides + slices core done; pending F5, badges, non-loop stop, durations UI |
| 3     | NOT STARTED | Awaiting slice foundation |
| 4     | PARTIAL     | Forward playback only |
| 5     | NOT STARTED | Export schema & builder pending |
| 6     | NOT STARTED | Advanced systems pending |

## Immediate Focus Recommendation
Proceed with Trim override interaction → Undo/Redo scaffold → Slice model foundation. Establish solid editing semantics before parser/export complexity.

### Active Decisions To Reflect
See DECISIONS.md: override storage, stack selection, performance budgets, export key ordering.

### Notes
- TypeScript strictness relaxed temporarily; address after trim + slices.
- Add decisions: cache invalidation strategy, slice model design, undo memory policy, onion skin rendering.
- Monitor preferences file size; add compaction if growth exceeds threshold.

## Phase 0 – Environment Setup (DONE)
- Stack selected (Electron + TS + React) – see DECISIONS.md.
- Scaffold running window & tooling (Vite + esbuild) complete.

## Phase 1 – Core Window & UI Skeleton (DONE)
- Main window + three panels + status bar.
- Preferences persistence (window size, recent sheets, last active sheet, pivot strategy).
- File open dialog (PNG) + recent list.
- Grid rendering with live parameter edits (tile size, margin, spacing).
- Frame selection (Ctrl+Click, Shift+Click) with order + Ctrl+A / Ctrl+D.

Evidence: Working renderer layout, selection visuals, persisted prefs file.

## Phase 2 – Core Logic & View Integration (IN PROGRESS)
Completed slices:
- FrameAnalyzer (auto trim + pivot strategies: bottom-center, center, top-left, top-right).
- Zoom & pan (Ctrl+wheel, Ctrl+ +/- / 0, middle drag / Alt+Left drag).
- Animation creation from selection + playback (forward loop) with preview panel.
- Multi-sheet tabs + last active sheet restore.
- Analysis overlays (toggle Trim=T, Pivot=P) with caching.
- Pivot strategy selector with persistence & cache invalidation.
- Manual pivot override vertical slice (drag pivot marker to set per-frame override; persistence via overrides registry in preferences).

Pending in Phase 2:
- Manual trim box override (resize handles) + persistence.
- Slices overlay & model scaffolding.
- Improved animation pane (list refresh shortcut, categorization placeholder).
- Keyboard shortcut parity audit (H helper toggle pending, others later).

Planned next micro-slices:
1. Trim override interaction (create + drag edges, store override, visual diff from auto).
2. Basic undo/redo command scaffold for pivot/trim changes (optional early start).
3. Slice data model stub + overlay toggle integration (no editing yet).

## Phase 3 – Aseprite Integration (NOT STARTED)
- Parser + source adapter pending.

## Phase 4 – Playback Engine Expansion (PARTIAL)
- Forward playback implemented; reverse & ping-pong pending.

## Phase 5 – Export Pipeline (NOT STARTED)

## Phase 6 – Advanced Features (NOT STARTED)

---
### Active Decisions To Reflect
See DECISIONS.md: override storage, stack selection, performance budgets, export key ordering.

### Immediate Focus Recommendation
Implement trim override interaction to complete Phase 2 manual analysis tooling foundation before introducing slices or Aseprite ingestion.

### Notes
- TypeScript strictness temporarily relaxed (implicit any in renderer) – cleanup scheduled after Phase 2 core interactions solidify.
- Performance: Analysis cache remains lazy; consider invalidation micro-benchmark after trim overrides.
