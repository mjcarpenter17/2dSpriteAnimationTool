# 2D Sprite Animation Tool (Rebuild)

This repository contains the in‑progress rebuild of the legacy AnimationViewer tool into a modern, modular Electron + TypeScript + React application.

## Current Status
- Phase 2 mid-progress: pivot & trim overrides, slice editing, undo/redo foundation, animations creation & playback, versioned overrides persistence.
- Dev environment: Vite (renderer) + esbuild (main & preload) + Jest tests.

## Getting Started
```bash
cd rebuild
npm install
npm run dev    # launches Vite + Electron
npm test       # run unit tests
```

## Key Directories
- `rebuild/src/main` – Electron main process (window, IPC, menu, preferences)
- `rebuild/src/preload` – Secure bridge exposing whitelisted IPC methods
- `rebuild/src/renderer` – React UI (Animations | Grid | Properties panels)
- `rebuild/src/core` – Core logic: spritesheets, analysis, overrides, slices, playback
- `rebuild/tests` – Jest unit tests for analyzer, playback, overrides precedence
- `Documentation/` – Architecture, tasklists, decisions, and phase planning
- `Archive/` – Legacy Python reference (do not modify; reference only)

## Implemented Features (Snapshot)
- PNG loading via IPC binary read (Blob URL) with recent sheets persistence
- Grid editing (tile size, margin, spacing) with live recompute
- Frame selection (multi-select ordering, keyboard navigation)
- Zoom/pan controls + overlay toggles (Trim, Pivot, Slices, master Helpers)
- Auto trim + pivot analyzer with strategy switching
- Per-frame trim & pivot manual overrides (drag + numeric inputs) + undo/redo
- Slice creation, move, resize, delete with undo support
- Animation creation from selection + forward playback + per-frame duration edits
- Versioned overrides JSON with safe skip on mismatch
- Tests: playback controller timing, overrides precedence & edge cases

## Roadmap (Condensed)
See `Documentation/REBUILD_TASKLIST.md` for authoritative list.
1. Complete Phase 2 remaining UI polish (F5 refresh, read-only badges)
2. Aseprite JSON integration (Phase 3) via plugin-style source
3. Playback expansion (ping-pong, reverse, onion skin)
4. Export pipeline (deterministic JSON schema)
5. Advanced features (layer filtering, batch export, performance HUD)

## Development Notes
- Electron modules are marked external in esbuild to avoid bundling the stub.
- Renderer loads images through IPC to bypass dev server file:// restrictions.
- Overrides are versioned; pruning stub reserved for future stale clean-up.

## License
(Choose and add a LICENSE file — MIT recommended.)

---
For architectural decisions, consult `Documentation/DECISIONS.md`.
