# KickOff Prompt: AnimationViewer Rebuild
---

## PROMPT TO AGENT
You are an implementation agent tasked with starting the AnimationViewer rebuild (Phase 0→Phase 1) following the repository documentation (`AGENTS.md`, `Documentation/COMPREHENSIVE_PROJECT_OVERVIEW.md`, `Documentation/REBUILD_TASKLIST.md`).

### Objectives
1. Select and record stack: Electron + TypeScript/React (create or append `DECISIONS.md`).
2. Scaffold project structure (directories + config) aligned with docs.
3. Implement minimal runnable shell: main window + three logical panels (left anims placeholder, center grid placeholder, right properties placeholder) + menu bar + status bar.
4. Implement `PreferencesManager` prototype (persist window size + recent files in JSON under user config directory).
5. Implement `SpriteSheet` model (image path, dimensions, tileWidth, tileHeight, margin, spacing).
6. Implement PNG open flow (menu: File > Open / Ctrl+O). Update recent files list.
7. Implement manual grid editing controls (stub UI ok if non-visual stack, but must update internal model & trigger redraw).
8. Implement frame selection logic (multi-select order preservation) with simple highlight rendering.
9. Provide smoke evidence artifacts (log outputs or screenshots path references) proving acceptance criteria for Phase 1.

### Constraints & Quality Gates
- Do NOT copy legacy Python UI logic; treat existing code as reference only.
- Keep modules decoupled: no rendering logic inside data models.
- Provide deterministic ordering for selections & exports (even if export stubbed now).
- Add minimal unit tests (at least: SpriteSheet grid frame rect calculation; selection ordering).
- Provide `README.md` quick start commands.

### Deliverables
- Directory structure.
- Core source files with initial implementation.
- `package.json` / `CMakeLists.txt` / `csproj` (per stack) with dependency pins.
- `DECISIONS.md` initial entry documenting stack choice rationale.
- `tests/` with at least two unit tests passing.
- `scripts/` (optional) helper for running lint/test.
- `README.md` containing setup + run instructions.
- Log file or console output summary of: window init, open PNG (mock path is ok if asset absent), preferences save location.

### Acceptance Checklist (Phase 1)
- [ ] App launches with window + visible placeholder regions.
- [ ] File > Open triggers file selection (or simulated path) and updates recent files.
- [ ] Grid parameters (tileWidth, tileHeight, margin, spacing) editable and reflected internally.
- [ ] Frame selection supports Ctrl+Click (add) and Shift+Click (range) with order memory.
- [ ] Preferences persist between two sequential launches (simulate by re-instantiating app in tests if headless).
- [ ] Unit tests green.
- [ ] Decision log entry created.

### Post-Completion Actions
After success:
1. Output concise summary: performance of basic operations (timestamps optional).
2. Recommend next micro‑plan for Phase 2 (frame analyzer & overlays stubs).
3. Flag any risks or uncertainties encountered.

### Non-Goals (Defer)
- Aseprite parsing
- Slice visualization
- Undo/Redo system
- Animation playback

Execute now and produce only the implementation + evidence. If a blocking issue occurs, emit a BLOCKERS section with context & proposed mitigations.

---

## Suggested Directory Skeleton
```
AnimationViewer/
  src/
    core/
      SpriteSheet.
      Preferences.
      Selection.
    ui/
      App.
      MainWindow.
      Panels/ (placeholders)
  tests/
  assets/examples/ (optional placeholder)
  scripts/
  DECISIONS.md
  README.md
```

---

## Decision Log Initial Template
```
## 2025-09-12 Stack Selection
Stack: Electron + TypeScript/React
Context: Need cross-platform desktop app with performant 2D rendering.
Considered: electron-typescript, qt-cpp, avalonia-csharp.
Decision: Electron + TypeScript/React due to <reason>.
Alternatives Rejected: <brief>.
Impact: Toolchain + dependency set locked for Phase 1–2.
Follow-Up: Reassess after performance profiling in Phase 3.
```

---

## Minimal Test Ideas
- `SpriteSheetGrid.test`: Given sheet 256x128, tile 32x32, margin 0, spacing 0 → expect 8x4 frames.
- `SelectionOrder.test`: Select frames (0, 5, 2 shift-range) → verify order array `[0,5,1,2]` if range expands inclusively.

---

## README Quick Start Snippet Placeholder
Populate in implementation:
```
# AnimationViewer (Rebuild)
Install: <cmd>
Run: <cmd>
Test: <cmd>
```

---

End of KickOff prompt.
