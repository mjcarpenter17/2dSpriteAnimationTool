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
