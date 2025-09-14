# AnimationViewer Rebuild (Electron + TypeScript + React)

Phase 1 shell for the language-agnostic rebuild. Implements minimal window, menu, status baseline, PreferencesManager prototype, SpriteSheet model, and selection stubs.

## Scripts
```bash
npm install
npm run dev   # start watcher + electron
npm test      # run unit tests
```

## Structure
```
rebuild/
  src/
    main/       # Electron main process
    preload/    # Secure bridge
    renderer/   # React UI (three-panel layout)
    core/       # Core models (preferences, spritesheet, selection)
  tests/        # Jest unit tests
```

## Implemented (Phase 1 slice)
- Stack decision documented in `Documentation/DECISIONS.md`.
- Main window + basic menu (File/Open) + status bar region (bottom row of grid layout).
- Preferences persistence (window size + recent sheets list).
- SpriteSheet grid calculation & frame rect helpers.
- Selection ordering with Ctrl / Shift semantics.
- React layout placeholders: Animations | Grid | Properties.
- Keyboard shortcuts: Ctrl+O (Open via menu), Ctrl+A (Select All), Ctrl+D (Clear Selection).
- Live grid parameter editing (tile width/height, margin, spacing) with real-time reflow.

## Next Steps
- Real image loading (decode via `<img>` now; move to Node image probe for dimensions if needed).
- Grid parameter editing UI (tile size, margin, spacing) with live recompute.
- Keyboard shortcuts & selection range improvements.
- Analysis overlay + zoom (Phase 2).
 - Multi-sheet tab support (Phase 2 early) & selection keyboard navigation.

## Testing
`SpriteSheetGrid.test.ts` validates columns/rows and frame rect math.
`SelectionOrder.test.ts` validates selection ordering behavior.

## Notes
Export / Aseprite integration intentionally deferred until later phases per `PRIME_TASKLIST.md`.
