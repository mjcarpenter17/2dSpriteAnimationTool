### 2025-09-13 Overrides Versioning & Pruning Stub
Status: accepted
Tags: data, persistence, safety
Context:
Manual pivot/trim overrides persisted in preferences could silently break if the on-disk shape drifts (e.g., adding slices, future per-frame meta, renaming keys). Needed a forward-compat barrier and place to later insert pruning (e.g., dropping invalid or stale frame indices after grid param changes dramatically reduce frame count).
Options Considered:
1. Leave unversioned; attempt best-effort parse forever.
2. Embed per-entry version numbers.
3. Single top-level `__version` with skip-on-mismatch (chosen).
Decision:
Emit `{ __version: <number>, sheets: { path -> frameOverrides } }`. On load, if `__version` exists and mismatches current `OVERRIDES_VERSION`, ignore the file (fail-safe). Maintain legacy compatibility by accepting unversioned objects (treated as legacy v0) until first write after upgrade, at which point new structure overwrites.
Rejected Because:
- (1) Risks misinterpreting fields after schema evolution; silent corruption.
- (2) Higher overhead & noise; per-record version not needed for current atomic replace strategy.
Consequences:
+ Safe evolution path; future schema bump only requires incrementing constant and optional migration logic.
+ Clean JSON surface; old clients won’t misread new nested shapes (they will just ignore due to mismatch if implemented similarly).
- Existing legacy data is discarded on version mismatch (user may lose overrides if manual migration omitted; acceptable early-phase tradeoff).
Follow-Up:
- Add migration function when bumping beyond v1 (e.g., mapping old `pivot` format variants).
- Implement actual pruning heuristics (e.g., remove overrides whose frameIndex >= new frameCount after grid param change) using the provided `pruneInvalid` hook.
Related:
`core/FrameOverridesStore.ts` (`OVERRIDES_VERSION`, `pruneInvalid`), renderer `loadOverrides()` logic.

### 2025-09-13 Persistence Safety Notes (Overrides)
Status: accepted
Tags: data, persistence, migration
Context:
Need explicit stance on how override data survives schema evolution & grid param changes that can invalidate frame indices. Early users prioritize stability over partial automatic migrations; silent partial loads risk subtle corruption (wrong pivot applied to shifted frame).
Policy:
1. Fail-safe over partial migration: version mismatch results in skip, not best-effort parse.
2. Legacy (unversioned) data treated as v0 and upgraded automatically on first successful save (writes v1 shape).
3. Pruning hook (`FrameOverridesStore.pruneInvalid`) reserved for: (a) dropping frame indices >= current frameCount; (b) removing overrides with obviously invalid geometry (negative size or coords outside sheet bounds after param change).
4. No automatic rect remapping when grid param changes alter frame layout (user must re-derive overrides manually via auto-trim or re-edit). Complex coordinate re-projection deferred until demonstrated need.
5. Corruption Guard: Loader validates numeric fields; non-numeric or structurally invalid entries are discarded silently (logged in future once logging subsystem added).
6. Data Minimization: Empty stores (no pivot/trim entries) are elided from serialization on future optimization pass (not yet implemented) to keep prefs small.
Options Considered:
1. Automatic coordinate remap on tile size change.
2. Soft warning + partial load.
3. Hard skip + explicit version boundary (chosen).
Decision:
Choose predictable all-or-nothing load with explicit version gating to prevent subtle frame-to-frame pivot drift after schema changes.
Rejected Because:
- (1) Requires historical grid param snapshot & complex math; high risk of incorrect mapping early.
- (2) Partial loads create hidden disparity (some frames override, others silently reset) harming trust.
Consequences:
+ Users immediately see loss (no overrides) rather than latent visual misalignment.
+ Simplifies future migrations (add dedicated migration path when needed).
- Potential user frustration on early schema bumps; documented mitigation: limit bumps, batch changes.
Follow-Up:
- Implement logging of skipped/mismatched version with guidance to reapply overrides.
- Add optional export tool to snapshot & re-import overrides for manual migration if schema bump major.
Related:
Overrides Versioning decision above; `FrameOverridesStore.pruneInvalid` future use.

### 2025-09-13 Undo/Redo Initial Scaffold
Status: accepted
Tags: ui, undo, workflow
Context:
Need reversible user actions (pivot/trim edits) early to avoid retrofitting complex history later. Full Phase 6 spec requires grouping, stack limits, and multi-action commands, but Phase 2 only needs simple linear undo for pivot & trim overrides.
Options Considered:
1. Defer all undo until Phase 6.
2. Implement full-featured command system now.
3. Minimal CommandStack (chosen): push simple do/undo objects on mouse-up events.
Decision:
Adopt lightweight in-memory CommandStack with arrays for done/undone. Each finalize of pivot or trim drag pushes a command capturing resulting state. Original state capture deferred (current undo reverts to clearing override when no prior state) until richer diff tracking added.
Rejected Because:
- (1) Would force invasive refactors once slices/durations rely on consistent API.
- (2) Adds premature complexity (grouping, memory policy) not yet required.
Consequences:
+ Immediate user confidence (Ctrl+Z/Y) while editing pivots/trims.
+ Clear extension seam for later slice/duration commands.
- Current undo cannot restore previous non-existent vs modified distinction for future multi-step drags (will evolve).
Follow-Up:
Capture initial value on mousedown to allow perfect restoration; add stack size policy decision in Phase 6.
Related:
renderer `CommandStack` implementation (index.tsx).

### 2025-09-13 Slice Store Foundation
Status: accepted
Tags: data, ui
Context:
Need minimal slice timeline model to begin user creation before Aseprite ingestion and advanced editing. Must be sparse & export-friendly.
Options Considered:
1. Extend OverridesRegistry to also hold slices.
2. Independent `SliceStore` module with its own serialization (chosen).
3. Inline per-frame slice arrays inside SpriteSheet.
Decision:
Implemented `SliceStore` with Map<sliceId, SliceData{keys: Map<frame,rect>}>. Creation seeds a key at current frame, retrieval uses nearest-previous lookup. Persistence integration deferred until export & preferences schema update.
Rejected Because:
- (1) Would conflate override semantics (single-value precedence) with timeline evolutionary data.
- (3) Wastes memory; awkward for sparse modifications.
Consequences:
+ Clean separation; straightforward future plugin ingestion mapping to Aseprite slices.
+ Efficient sparse memory footprint.
- Lacks persistence until preferences/export integration—slices currently volatile.
Follow-Up:
Add persistence path & decision entry for storage location (prefs vs project file). Add slice editing (resize/move/delete) and delete shortcuts.
Related:
`core/Slices.ts`, renderer slice overlay provisional creation (Shift+Click).

### 2025-09-12 Manual Pivot/Trim Override Storage
Status: accepted
Tags: data, ui, undo
Context:
Need a lightweight, per-frame persistence mechanism for user overrides (pivot & future trim) without bloating core SpriteSheet model or recomputation paths. Must allow quick lookup during overlay rendering and survive app restarts.
Options Considered:
1. Embed overrides directly into SpriteSheet in-memory object and serialize entire sheet state.
2. Maintain global overrides registry keyed by sheet path, store inside preferences (chosen).
3. Separate JSON sidecar files per sheet.
Decision:
Use an in-memory `OverridesRegistry` mapping sheet path -> `FrameOverridesStore` (frameIndex -> {pivot, trim}). Persist the aggregated structure in preferences under `overrides` key via periodic (1.5s) debounced flush IPC.
Rejected Because:
- (1) Couples volatile UI edits with core model; complicates reuse & plugin ingestion.
- (3) Adds file management complexity and potential orphaned sidecars; harder atomic updates.
Consequences:
+ Fast O(1) retrieval; minimal coupling; easy future undo integration (wrap setPivot/setTrim in command objects later).
+ Centralized serialization piggybacks on existing prefs persistence.
- Preferences file may grow with very large sheets (mitigate with sparse structure & future pruning strategy).
Follow-Up:
Add trim override drag/resize integration; introduce undo/redo command wrappers; consider compression or diff strategy if prefs size exceeds threshold.
Related:
FrameOverridesStore.ts; renderer pivot drag implementation.

### 2025-09-12 Analysis Cache & Invalidation Strategy
Status: accepted
Tags: perf, data
Context:
Need efficient recomputation avoidance for trim/pivot analysis while supporting dynamic grid param edits and manual overrides (pivot & upcoming trim). Uncontrolled recompute on every render risks >50ms stalls on large sheets.
Options Considered:
1. Recompute trim/pivot on every frame render.
2. Cache per-frame analysis forever; full clear on any grid or strategy change.
3. Layered cache: sheet-level pixel buffer + per-frame entries with selective invalidation (chosen).
Decision:
Adopt layered cache. Store per-sheet RGBA buffer once (on first overlay request) and Map<frameIndex,{trim,pivot}> entries computed lazily. On pivot strategy change: only invalidate pivot (retain trim). On grid parameter change: clear frame cache (frame rects shift). On pivot/trim manual overrides: do not invalidate auto values, but precedence layer chooses override when present.
Rejected Because:
- (1) Incurred O(n * pixelCount) cost each overlay toggle.
- (2) Excessive invalidation after minor pivot strategy tweak wastes trim computations.
Consequences:
+ Minimizes redundant trim scanning; pivot recompute cheap.
+ Predictable invalidation semantics documented.
- Requires explicit precedence logic for overrides vs cached auto.
Follow-Up:
Introduce generation counters if future multi-threaded analyzer added; add micro-benchmark after trim override implementation.
Related:
Renderer `sheetAnalysisCache`, FrameAnalyzer, upcoming trim override handling.

### 2025-09-12 Slice Model Initial Design (Planned)
Status: proposed
Tags: data, ui, export
Context:
Need a flexible slice representation supporting Aseprite-imported timelines and manual creation/editing with minimal overhead and export friendliness.
Options Considered:
1. Store slices as simple per-frame arrays keyed by frameIndex.
2. Timeline objects: Slice{id,name,type, keys: Map<frameIndex, Rect>} (chosen).
3. Dense 2D matrix (sliceIndex x frameIndex) of rects.
Decision:
Use timeline model: Each Slice holds sparse key map (only frames with changes). For frames without explicit key, last prior key value is considered active. Manual creation starts with current frame key; propagation uses copy shortcuts. Keeps memory proportional to actual edits and matches Aseprite conceptual model.
Rejected Because:
- (1) Hard to represent persistence across frames efficiently (duplication) & costly export filtering.
- (3) Wastes memory on large sheets with few edited frames; complicates insertion deletion.
Consequences:
+ Sparse efficient storage, natural for keyframe editing, easy export expansion.
+ Simplifies interpolation extension (future) if needed.
- Requires lookup logic for nearest previous key during overlay rendering.
Follow-Up:
Implement `Slice`, `SliceKey`, `SliceStore` modules; add decision update upon implementation; integrate into overrides or separate persistence block.
Related:
Phase 2 slice foundation tasks; Phase 3 Aseprite parser mapping.

# DECISIONS.md

Central log of architectural and process decisions. Follow the template. Append new entries at the top (reverse chronological) for fast visibility. Keep entries concise; link to issues or PRs for depth.

---
### 2025-09-15 Advanced Persistence Pruning Strategy
Status: accepted
Tags: data, persistence, memory
Context:
Need comprehensive cleanup strategy for override data that becomes stale due to grid parameter changes, sheet removals, or invalid geometry after user edits. Simple frame count filtering insufficient for production use.
Options Considered:
1. Basic frame index filtering only (existing).
2. Multi-strategy pruning with configureable policies (chosen).
3. Automatic background cleanup with heuristics.
Decision:
Implemented `pruneStaleOverrides()` with multiple strategies: frame range validation, geometry bounds checking, invalid coordinate removal, and empty entry cleanup. Added statistics tracking (`getStats()`, `getGlobalStats()`) for monitoring override memory usage and enabling data-driven cleanup decisions.
Rejected Because:
- (1) Leaves corrupted geometry and orphaned entries after complex editing sessions.
- (3) Automatic cleanup risks removing user intent; explicit triggered cleanup safer.
Consequences:
+ Comprehensive cleanup prevents override corruption and memory bloat.
+ Statistics enable monitoring and optimization decisions.
+ Configurable strategies allow adaptation to different usage patterns.
- Additional complexity in pruning logic requiring validation.
Follow-Up:
Add UI control for manual override cleanup (e.g., "Clean Invalid Overrides" button in Properties panel); implement automatic cleanup trigger after sheet parameter changes exceed threshold.
Related:
Enhanced `FrameOverridesStore.pruneStaleOverrides()`, `getStats()` methods; global registry cleanup via `pruneEmptySheets()`.

### 2025-09-15 Phase 2 UX Polish Implementation
Status: accepted
Tags: ui, ux, tooltips
Context:
Phase 2 closure required UX improvements: tooltips for override vs auto values, slice color legend, and enhanced user feedback for complex interactions.
Options Considered:
1. Minimal tooltips on major controls only.
2. Comprehensive tooltips plus visual legends (chosen).
3. Interactive help overlay system.
Decision:
Added descriptive tooltips to Toolbar controls explaining overlay functions, hotkeys, and auto vs manual precedence. Implemented slice color/type legend showing hit/hurt/attachment/custom types with visual indicators and interaction hints. Enhanced with usage instructions ("Shift+Click to create").
Rejected Because:
- (1) Insufficient for complex pivot strategy and slice type concepts.
- (3) Over-engineered for current scope; tooltip system adequate.
Consequences:
+ Improved discoverability of advanced features.
+ Clearer mental model of override precedence and slice semantics.
+ Reduced learning curve for new users.
- Minor additional maintenance for tooltip accuracy.
Follow-Up:
Add tooltips to Properties panel inputs indicating override vs auto state; implement hover indicators on grid overlays showing value source.
Related:
Toolbar.tsx tooltip enhancements, App.tsx slice legend component.

### 2025-09-15 Performance Monitoring Integration
Status: accepted
Tags: perf, monitoring, testing
Context:
Need systematic performance tracking and budget validation for analysis operations to prevent regression during feature development.
Options Considered:
1. Manual timing code scattered throughout codebase.
2. Centralized monitoring with optional activation (chosen).
3. Always-on performance tracking.
Decision:
Implemented `PerformanceMonitor` class with operation timing, cache hit rate tracking, and performance budget validation. Added micro-benchmark script (`npm run benchmark`) testing trim analysis, pivot calculation, and cache operations against defined budgets. Created cache invalidation policy documentation.
Rejected Because:
- (1) Inconsistent measurement and difficult maintenance.
- (3) Performance overhead in production; monitoring should be opt-in.
Consequences:
+ Systematic performance regression detection.
+ Data-driven optimization with concrete budgets.
+ Documentation of cache invalidation strategy for team alignment.
- Additional instrumentation overhead when enabled.
Follow-Up:
Integrate performance monitoring into CI pipeline for automated budget validation; add runtime performance HUD for development debugging.
Related:
`PerformanceMonitor.ts`, `scripts/benchmark.js`, `docs/cache-invalidation-policy.md`.

### 2025-09-15 Test Coverage Enhancement (Phase 2)
Status: accepted
Tags: test, quality, coverage
Context:
Phase 2 completion required additional test coverage for slice persistence and undo/redo operations to ensure data integrity and user workflow reliability.
Options Considered:
1. Basic smoke tests only.
2. Comprehensive slice and undo round-trip testing (chosen).
3. Full integration testing with UI automation.
Decision:
Added `SlicePersistence.test.ts` covering slice creation, timeline operations, serialization/deserialization, and edge cases. Implemented `UndoRedoRoundTrip.test.ts` testing command stack behavior, state consistency, and multi-operation sequences. Enhanced `FrameOverridesStore` with `clearPivot()`/`clearTrim()` methods for proper undo support.
Rejected Because:
- (1) Insufficient coverage for complex slice timeline and undo edge cases.
- (3) UI automation premature; unit test coverage more valuable at this stage.
Consequences:
+ High confidence in slice data integrity and undo/redo reliability.
+ Enhanced FrameOverridesStore API with proper clear operations.
+ Foundation for future UI testing with established test patterns.
- Increased test maintenance overhead with complex state scenarios.
Follow-Up:
Add integration tests combining slice creation with undo/redo; implement property-based testing for timeline edge cases.
Related:
`SlicePersistence.test.ts`, `UndoRedoRoundTrip.test.ts`, enhanced `FrameOverridesStore` API.

### 2025-09-14 Animations Pane Refresh & Selection Ordering Model
Status: accepted
Tags: ui, data, workflow
Context:
Needed a structured Animations Pane with deterministic ordering and a refresh action (F5) without forcing full window reload. Also required a clear policy for maintaining user selection order when creating animations so resulting animations reflect intentional frame sequencing.
Options Considered:
1. Implicit browser reload on F5 relying on dev tooling (risk: state loss).
2. Internal refresh token increment (chosen) decoupled from global reload.
3. Event bus broadcast to pane component.
Selection Ordering:
1. Sort numerically ascending at animation creation time.
2. Preserve user click order (chosen).
3. Preserve order but dedupe by keeping first occurrence only.
Decision:
Implemented `AnimationsPane` component reading from `AnimationStore`. Pressing F5 intercepts default, increments a local `animVersion` refresh token causing the list to re-render (extensible to sources later). Selection order preserved exactly as captured by `SelectionManager.order` when creating an animation; frames appended in that order with default duration. Read-only badge placeholder added for future Aseprite integration (currently always false) to minimize future diff.
Rejected Because:
- Browser reload (1) would discard unsaved in-memory edits, harming workflow.
- Event bus (3) premature complexity; token suffices for now.
- Numeric sort for selection (selection option 1) erases semantic ordering (e.g., custom non-linear frame sequences).
Consequences:
+ Fast refresh cycle without state loss.
+ Deterministic user‑intent frame sequencing.
+ Minimal architectural footprint; easy to extend to multi-source merging.
- Requires future adaptation when external plugins push animation updates asynchronously.
- Potential duplicate frame indices allowed (intentional flexibility) until a validation layer is added.
Follow-Up:
- Add decision entry for multi-source merge ordering once Aseprite source lands.
- Introduce optional duplicate frame warning in Properties panel.
Related:
`App.tsx` (`animVersion`), `AnimationsPane.tsx`, `SelectionManager` ordering semantics.


### 2025-09-14 CSS Background Property Separation
Status: accepted
Tags: ui, build, fix
Context:
React warned about mixing background shorthand property with specific background properties (backgroundPosition, backgroundSize) in grid rendering, causing console warnings and potential styling conflicts.
Options Considered:
1. Keep background shorthand and remove specific properties.
2. Remove background shorthand and use only specific properties (chosen).
3. Restructure CSS to avoid conflicts.
Decision:
Separated CSS background properties in styles.css, using backgroundImage, backgroundPosition, backgroundSize, and backgroundRepeat instead of the shorthand background property. This eliminates React warnings and provides more explicit control over background styling.
Rejected Because:
- (1) Would lose fine-grained control over background positioning needed for grid alignment.
- (3) Would require more extensive CSS restructuring without clear benefit.
Consequences:
+ Eliminates React console warnings.
+ More explicit and maintainable CSS properties.
+ Better control over individual background aspects.
- Slightly more verbose CSS syntax.
Follow-Up:
Monitor for any other CSS shorthand vs specific property conflicts in future styling work.
Related:
Grid rendering implementation in App.tsx, styles.css background properties.

### 2025-09-14 ES6 Import Migration from CommonJS
Status: accepted
Tags: build, arch, fix
Context:
Runtime error "ReferenceError: require is not defined" occurred when trying to use CommonJS require() syntax in Electron renderer process, which expects ES6 modules by default in the current Vite configuration.
Options Considered:
1. Configure Vite to support CommonJS require() calls.
2. Convert all imports to ES6 import syntax (chosen).
3. Use dynamic import() for conditional loading.
Decision:
Migrated all CommonJS require() calls to ES6 import statements. Changed `require('../core/SelectionManager').SelectionManager` to `import { SelectionManager } from '../core/SelectionManager'` and similar patterns throughout the codebase.
Rejected Because:
- (1) Would add build complexity and go against modern ES6 standards.
- (3) Unnecessary for static imports; adds complexity without benefit.
Consequences:
+ Aligns with modern JavaScript standards and Vite expectations.
+ Eliminates runtime errors in renderer process.
+ Consistent import syntax across the codebase.
+ Better tree-shaking and bundling optimization.
- Required updating multiple import statements across files.
Follow-Up:
Ensure all new code uses ES6 import syntax; add linting rule to prevent CommonJS usage if needed.
Related:
App.tsx imports, SelectionManager integration, Vite build configuration.

### 2025-09-14 Component Extraction Architecture
Status: accepted
Tags: arch, ui, refactor
Context:
The original index.tsx had grown to 706 lines with a monolithic structure containing UI components, state management, and application logic all mixed together, making it difficult to maintain and test.
Options Considered:
1. Keep monolithic structure and just clean up code organization.
2. Extract only the largest components (StatusBar, Toolbar).
3. Full component extraction with centralized state management (chosen).
Decision:
Extracted multiple components (StatusBar, Toolbar, ErrorBoundary) into separate files in a components/ directory and created a centralized AppStateManager for state coordination. Moved main application logic to App.tsx and reduced index.tsx to a simple entry point.
Rejected Because:
- (1) Would not address fundamental maintainability issues and testing complexity.
- (2) Partial extraction would leave significant coupling and maintenance burden.
Consequences:
+ Dramatically improved code maintainability and readability.
+ Enables individual component testing and reuse.
+ Clear separation of concerns between UI, state, and application logic.
+ Reduced file complexity from 706 lines to manageable component sizes.
+ Better TypeScript type safety with component-specific interfaces.
- Required significant refactoring effort and careful state management coordination.
- More files to manage in the project structure.
Follow-Up:
Continue extracting additional components as they grow in complexity; establish component testing patterns.
Related:
AppStateManager.ts creation, components/ directory structure, App.tsx main component.

### 2025-09-14 Centralized State Management Implementation
Status: accepted
Tags: arch, data, refactor
Context:
The monolithic structure had global variables and scattered state management across the large index.tsx file, making it difficult to track state changes and coordinate between different parts of the application.
Options Considered:
1. Keep global variables and add better organization.
2. Use React Context for state management.
3. Create dedicated state management classes (chosen).
Decision:
Implemented AppStateManager.ts with specialized classes (CommandStack, ZoomManager, AnalysisCache) to centralize state management. Created a global appState instance that coordinates sheet management, commands, zoom, and caching operations.
Rejected Because:
- (1) Would not solve coordination and tracking issues inherent in scattered global state.
- (2) React Context would be overkill for this application's state complexity and could impact performance.
Consequences:
+ Clear state ownership and modification patterns.
+ Easier debugging and state tracking.
+ Better separation between UI and business logic.
+ Foundation for future undo/redo and advanced state management features.
+ Type-safe state operations with TypeScript.
- Added complexity in state coordination between manager and components.
- Required careful interface design between state manager and UI components.
Follow-Up:
Expand state management patterns as new features are added; consider state persistence strategies.
Related:
AppStateManager.ts implementation, CommandStack class, ZoomManager class, global appState instance.

### 2025-09-14 Test Suite Fixes and Validation
Status: accepted
Tags: test, fix, validation
Context:
After refactoring, the test suite had failures due to changes in component structure and incorrect test assumptions about frame positioning calculations.
Options Considered:
1. Skip failing tests temporarily.
2. Update tests to match new architecture (chosen).
3. Rewrite entire test suite.
Decision:
Fixed specific test failures by updating SpriteSheetGrid.test.ts to use correct frame height calculations (32px to 64px) and ensured all 17 tests pass after refactoring. Maintained existing test coverage while adapting to new component structure.
Rejected Because:
- (1) Would leave validation gaps and technical debt.
- (3) Would be excessive given that most tests were still valid with minor adjustments.
Consequences:
+ Maintained test coverage and validation confidence.
+ Ensured refactored code meets existing quality standards.
+ Identified and corrected assumptions about frame calculations.
+ 100% test pass rate validates refactoring success.
- Required careful analysis of test failures to determine correct fixes.
Follow-Up:
Add tests for new components (StatusBar, Toolbar, ErrorBoundary); expand test coverage for state management.
Related:
SpriteSheetGrid.test.ts fixes, Jest test suite, frame calculation validation.

---

### 2025-09-12 Rebuild Stack Selection (Electron + TypeScript + React)
Status: accepted
Tags: arch, build, ui
Context:
Need a modern, cross‑platform desktop stack supporting rich UI, rapid iteration, strong ecosystem libraries, and easy integration with image processing while avoiding legacy Python UI constraints.
Options Considered:
1. C++ / Qt
2. C# / Avalonia
3. Electron + TypeScript + React (chosen)
4. Rust + Tauri + React
Decision:
Adopt Electron with TypeScript and React. Leverages mature dev tooling, fast hot‑reload, broad library availability (image parsing, state mgmt), straightforward distribution, and aligns with need for rapid multi‑panel UI prototyping. React chosen for declarative state handling and testability; TypeScript for type safety.
Rejected Because:
- C++/Qt: Higher initial setup complexity, slower iteration for frequent UI changes.
- C#/Avalonia: Strong option but larger runtime + less contributor ubiquity vs web stack.
- Rust/Tauri: Attractive perf & footprint, but ecosystem + build friction slows early velocity.
Consequences:
+ Rapid Phase 1 delivery via web tooling & component reuse.
+ Abundant testing & lint infrastructure (Jest, Vitest, ESLint) lowers defect rate.
+ Easy plugin / future web deployment path.
- Larger memory footprint than native alternatives.
- Must enforce performance discipline (render batching, virtualization) to meet budgets.
Follow-Up:
Re‑evaluate footprint vs Tauri/Rust after Phase 4 (playback + export) for potential migration or hybrid core module in Rust if perf budgets threatened.
Related:
AGENTS.md Sections 3 & 14 (workflow, performance).


## Legend
- Status: `accepted`, `proposed`, `superseded`, `deprecated`
- Impact Tags: `arch`, `perf`, `export`, `ui`, `data`, `build`, `workflow`

---

## Template
```
### YYYY-MM-DD <Short Title>
Status: accepted
Tags: arch, data
Context:
<Brief background; what problem needed solving>
Options Considered:
1. <Option A>
2. <Option B>
Decision:
<Chosen option and why>
Rejected Because:
<Why alternatives were rejected>
Consequences:
<Positive + negative tradeoffs>
Follow-Up:
<Planned future evaluation or tasks>
Related:
#<issue> PR #<id> (optional)
```

---

### 2025-09-12 Decision Log Established
Status: accepted
Tags: workflow
Context:
Need a persistent, auditable place for architectural and process decisions to enable autonomous agent continuity.
Options Considered:
1. Ad-hoc comments in code
2. Git commit messages only
3. Central DECISIONS.md index (chosen)
Decision:
Adopt a single DECISIONS.md with reverse chronological order and structured template for clarity.
Rejected Because:
- Ad-hoc comments scatter rationale
- Commits alone lack cross-cutting narrative
Consequences:
+ Faster onboarding + reduced duplication
+ Easier auditing of evolving architecture
- Adds lightweight documentation overhead
Follow-Up:
Review format after first 10 entries for noise vs value.
Related:
N/A

---

### 2025-09-12 Export Key Ordering Policy
Status: accepted
Tags: export, data
Context:
Need deterministic JSON exports for stable diffs and CI verification.
Options Considered:
1. Natural hash/dict iteration order
2. Alphabetical key sort
3. Explicit canonical ordering list (chosen)
Decision:
Use explicit ordered serialization: `version, sheet, animations, slices, layers, meta`. Nested objects keep logical grouping (e.g., frame: rect, trim, pivot, duration, slices).
Rejected Because:
- Natural order may vary across languages/versions
- Pure alphabetical hurts semantic readability
Consequences:
+ Stable diffs
+ Easier golden fixture comparisons
- Slight manual overhead maintaining order list
Follow-Up:
Add schema version bump rule if ordering must change.
Related:
See AGENTS.md Section 12 Data Model Quick Reference.

---

### 2025-09-12 Performance Budget Framework
Status: accepted
Tags: perf, workflow
Context:
Prevent uncontrolled performance regression during incremental feature build-out.
Options Considered:
1. Post-hoc optimization only
2. Strict perf test gate before each merge
3. Lightweight documented budgets + selective benchmarks (chosen)
Decision:
Adopt documented budgets (AGENTS.md Section 14) with targeted micro-benchmarks for at-risk areas.
Rejected Because:
- Post-hoc leads to expensive rewrites
- Strict full perf gate early is overkill and slows iteration
Consequences:
+ Prevents perf debt accumulation
+ Keeps early velocity acceptable
- Requires discipline to add benchmarks when risk surfaces
Follow-Up:
Introduce automated perf CI job once Feature Phase 3 begins.
Related:
AGENTS.md Section 14.
