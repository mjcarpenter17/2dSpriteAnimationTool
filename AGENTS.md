# AGENT INSTRUCTIONS: AnimationViewer Project Rebuild

This document provides essential context and instructions for AI agents working on the AnimationViewer project.

---

## 🔑 Quick Start (Agent Onboarding < 5 Minutes)

1. Skim sections 1–6 below (deep dive later).
2. Open `Documentation\REBUILD_TASKLIST.md`; identify current phase.
3. Select target stack (log in `Documentation\DECISIONS.md`).
4. Scaffold window + three panel placeholders (Animations | Grid | Properties).
5. Implement first vertical slice: Open PNG → Grid visible → Manual grid edits live → Frame selection works.
6. Smoke checklist:
  - App opens/closes cleanly
  - Preferences file written & window size persists
  - Recent files updated after open
  - Grid recalculates immediately on edits
7. Commit: `chore(init): bootstrap shell + grid slice`.
8. Begin first unchecked acceptance in current phase.

> If blocked >15 min: add entry to `BLOCKERS.md` (problem, hypothesis, attempts, next step).

## 1. Project Brief & Status

- **Mission**: Rebuild the AnimationViewer tool from scratch into a professional-grade application for 2D game development.
- **Current Status**: **COMPLETE REBUILD PHASE**. The project is ready for implementation in a new, modern language/framework.
- **Legacy Code**: The existing Python/Pygame codebase (Archive)is a **functional reference ONLY**. It contains critical flaws (`Archive\AnimationViewer\ui\main_window.py`) and **should not be fixed or extended**.

---

## 2. Key Documentation (READ FIRST)

Your first action should be to thoroughly review these documents to understand the project scope.

1.  **`Documentation\COMPREHENSIVE_PROJECT_OVERVIEW.md`**: The "source of truth" for all technical specifications, architecture, and feature requirements.
2.  **`Documentation\REBUILD_TASKLIST.md`**: The language-agnostic, step-by-step implementation plan. **Follow the phases outlined in this document.**
3.  **`Documentation\SHORTCUTS_AND_MENUS.md`**: A cheatsheet for all required UI interactions and keyboard shortcuts.

---

## 3. Development Workflow & Environment

### Environment Setup
- **Language/Framework**: Choose a modern, cross-platform UI framework (e.g., Qt for C++, Avalonia for C#, Electron for TypeScript). Avoid using Python/Pygame for the new implementation.
- **Initial Setup**: Create a new project, add a 2D graphics library, and ensure a blank window can be rendered. This corresponds to **Phase 0** in the `REBUILD_TASKLIST.md`.

### Development Approach
- **Follow the Tasklist**: The `REBUILD_TASKLIST.md` contains a 6-phase plan. Implement features in the order specified.
- **Reference Implementation**: Use the Python code in `Archive\AnimationViewer\core`, `Archive\AnimationViewer\ui`, and `Archive\AnimationViewer\utils` to understand algorithms and data structures.
  - **Example**: To understand the trim/pivot logic, review `Archive\AnimationViewer\core\frame_analyzer.py`.
  - **Example**: To understand the data model, review `Archive\AnimationViewer\core\spritesheet.py` and `Archive\AnimationViewer\core\animation.py`.
- **Getting Started**:
  1. Read the key documents.
  2. Set up your development environment.
  3. Begin with **Phase 1** of `REBUILD_TASKLIST.md`: Create the main application window and UI skeleton.

---

## 4. Code & Architecture Guidelines

### Architecture Patterns
- **Modular Design**: Strictly separate core logic (data models, analysis) from the UI.
- **Plugin System**: Implement the `IAnimationSource` interface to support different data sources (manual creation, Aseprite files).
- **Command Pattern**: Use this for all user actions (grid changes, pivot edits, etc.) to enable a robust Undo/Redo system.
- **Observer Pattern**: Use for UI updates when preferences or data models change.

### Data Formats
- **Aseprite Ingestion**: Your parser must handle `meta` (pixelRatio), `frames` (duration), `frameTags` (animations), `slices`, and layer data from frame names.
- **JSON Export**: The application's primary output is a rich JSON file. The target schema is defined in `COMPREHENSIVE_PROJECT_OVERVIEW.md`. Ensure your exported files match this schema.

### UI/UX Requirements
- **Layout**: Implement the three-panel layout (Animations, Frame Grid, Properties) with a menu bar and status bar as defined in the overview document.
- **Key Interactions**:
  - Manual grid parameter editing (`tile size`, `margin`, `spacing`) must provide a real-time preview.
  - Pivot points and trim boxes must be editable via direct manipulation (drag-and-drop, resizing handles).
  - All shortcuts from `SHORTCUTS_AND_MENUS.md` must be implemented.

---

## 5. Testing & Validation Strategy

### Testing Guidelines
- **Unit Tests**: Core algorithms like trim analysis, pivot calculation, and JSON parsing must have dedicated unit tests.
- **Integration Tests**: Create tests for end-to-end workflows, such as:
  1. Loading an Aseprite file (`.json` + `.png`).
  2. Displaying its animations and slices.
  3. Exporting one of the animations to the internal JSON format.
  4. Verifying the exported file's integrity.
- **UI/UX Validation**: Manually verify that all UI interactions feel responsive and match the specifications (e.g., manual grid editing, slice manipulation, undo/redo).

### Success Indicators
The rebuild is successful when a user can:
- Import any sprite sheet and visually adjust the grid to match it.
- Load Aseprite files and see all associated data (animations, slices, layers).
- Browse animations from different sprite sheets, with the app automatically switching tabs.
- Manually override pivot points and trim boxes on a per-frame basis.
- Export animations to a game-engine-ready JSON format that includes all metadata.
- Use professional tools like undo/redo, onion skinning, and batch processing.

---

## 6. Critical Reminders & Common Pitfalls



## 7. Key Technologies and Dependencies

### Recommended Frameworks
- **Minimal Dependencies**: Prefer lightweight, widely-used libraries to keep the application portable.

- **`/ui`**: UI components (note: `main_window.py` is deprecated and should not be used).

### Recommended New Structure
- **Modular Architecture**: Separate concerns into modules like `DataModels`, `UI`, `CoreLogic`, `Plugins`.
- **Plugin Directory**: Implement a `Plugins` folder for animation sources (Manual, Aseprite).
- **Tests Directory**: Include a dedicated `Tests` folder for unit and integration tests.

---

## 9. Performance Considerations

### Handling Large Assets
- **Memory Management**: Implement efficient loading for large sprite sheets; consider lazy loading or streaming for very large files.
- **Rendering Optimization**: Use hardware acceleration where possible; cache rendered frames to avoid recomputation.
- **UI Responsiveness**: Ensure real-time previews for grid editing don't block the main thread; use background threads for heavy computations.

### Scalability
- **Frame Rate**: Target smooth 60 FPS for animation playback.
- **Large Projects**: Support projects with hundreds of frames and multiple sprite sheets without performance degradation.

---

## 10. Deployment and Distribution

### Build Process
- **Cross-Platform Builds**: Set up CI/CD pipelines for Windows, macOS, and Linux builds.
- **Packaging**: Use tools like Inno Setup (Windows), DMG (macOS), or AppImage (Linux) for distribution.

### Distribution Channels
- **Standalone Executable**: Package the app as a single executable with all dependencies bundled.
- **Web Version**: If using Electron, consider web deployment for broader accessibility.
- **Version Control**: Use Git with semantic versioning; tag releases appropriately.

---

## 11. Collaboration and Version Control

### Git Workflow
- **Branching Strategy**: Use feature branches for new implementations; merge via pull requests.
- **Commit Messages**: Write clear, descriptive commit messages following conventional commits.

### Documentation Updates
- **Keep Docs in Sync**: Update the `.md` files as the project evolves to maintain accuracy.
- **Code Comments**: Include inline comments for complex algorithms, referencing the overview documents.

---

## 12. Troubleshooting and Support

## 12. Data Model Quick Reference (Authoritative Shapes)

### Frame (internal)
```jsonc
{
  "id": 42,                // Stable identifier within sheet
  "sheetId": "player_run", // Parent spritesheet logical id
  "grid": { "row": 3, "col": 5 },
  "rect": { "x": 160, "y": 96, "w": 32, "h": 32 },      // Raw cell
  "trim": { "x": 164, "y": 100, "w": 24, "h": 26 },     // Tight bounds
  "pivot": { "x": 12, "y": 25, "origin": "bottom-center", "overridden": true },
  "durationMs": 83,
  "layers": ["Base", "Weapon"],
  "slices": [
    { "name": "hitbox", "type": "hit", "rect": { "x": 6, "y": 4, "w": 12, "h": 18 } }
  ],
  "custom": { }
}
```

### Animation (internal)
```jsonc
{
  "name": "run",
  "source": "manual|aseprite",
  "sheetId": "player_run",
  "tags": ["movement"],
  "loop": true,
  "playback": { "mode": "forward", "speedScale": 1.0 },
  "frames": [
    { "frameId": 40, "durationMs": 83 },
    { "frameId": 41, "durationMs": 83 }
  ],
  "slices": { /* optional aggregated slice timelines */ },
  "layers": ["Base", "Weapon"],
  "meta": { "createdWith": "AnimationViewer" }
}
```

### Export Schema (simplified)
```jsonc
{
  "version": "1.0",
  "sheet": {
    "id": "player_run",
    "image": "player_run.png",
    "size": { "w": 512, "h": 256 },
    "tile": { "w": 32, "h": 32, "margin": 0, "spacing": 0 },
    "pixelRatio": { "x": 1, "y": 1 }
  },
  "animations": [ { "name": "run", "loop": true, "frames": [
      { "rect": { "x":160,"y":96,"w":32,"h":32 },
        "trim": { "x":164,"y":100,"w":24,"h":26 },
        "pivot": { "x":12,"y":25 },
        "duration":83,
        "slices": [ { "name":"hitbox", "rect": {"x":170,"y":104,"w":12,"h":18} } ]
      }
    ] }
  ],
  "slices": [ /* optional global slice timelines */ ],
  "layers": ["Base","Weapon"],
  "meta": { "exportedAt": "2025-09-12T10:00:00Z" }
}
```

Consistency Rules:
1. `frameId` indirection allows animation reuse across multiple animations referencing same base frame.
2. Export must resolve all indirections into concrete numeric / string values (no internal ids leaked unless documented).
3. Keep numeric durations in milliseconds; never mix seconds.
4. Omit empty objects/arrays unless required by consumer contract.
5. Maintain stable key ordering for diffs: `version, sheet, animations, slices, layers, meta`.

---

## 13. Definition of Done (DoD)

### Global DoD Checklist (ALL FEATURES)
- Requirements traced to `COMPREHENSIVE_PROJECT_OVERVIEW.md` section.
- Acceptance criteria in `REBUILD_TASKLIST.md` satisfied & demonstrable.
- Unit tests: new logic ≥ 80% branch coverage (core & parsing modules).
- No TODO/FIXME without linked issue id.
- Export format unchanged or schema version incremented + documented.
- Performance budgets respected (see Section 14 when added).
- Undo/Redo integration for any user-modifying action.
- Preferences persisted (if user-configurable behavior added).
- Logs free of uncaught exceptions during smoke test.
- Added/updated entry in `DECISIONS.md` if architecture affected.

### Phase Completion Gate (Minimum Evidence)
| Phase | Evidence Artifacts |
|-------|--------------------|
| 1 | Screenshot of shell + grid edit; prefs file diff; decision log entry |
| 2 | Unit tests for analyzer; manual override demo gif; pivot strategy test cases |
| 3 | Parsed Aseprite sample JSON diff; log summary of tags/slices/layers |
| 4 | Playback timing test (simulated durations) + preview latency <16ms avg |
| 5 | Export diff vs golden; batch export of ≥2 animations |
| 6 | Slice overlay screenshot; layer filter toggle log; non-square pixel ratio render proof |

### Pull Request Template Snippet
```
Summary:

Linked Tasks / Sections:

Evidence:
- [ ] Screenshots / GIFs
- [ ] Analyzer tests updated
- [ ] Export schema unaffected OR version bumped

Risks / Mitigations:

Checklist:
- [ ] DoD global items
- [ ] Performance budgets
- [ ] Undo/Redo covered
```

---

## 14. Performance & Quality Budgets

| Category | Budget | Measurement Method | Notes |
|----------|--------|--------------------|-------|
| UI Thread Idle | ≥ 40% frame time free | Profiling / instrumentation | Avoid long GC / allocations |
| Playback FPS | 60 target / never < 55 sustained | Animated preview timing harness | With 200 frames cached |
| Grid Zoom Latency | < 50 ms to redraw after zoom | Timestamp before & after render | At 4K sheet 20x20 cells |
| Initial PNG Load | < 1.0 s for 4096x4096 | Wall clock (cold) | Excludes disk caching |
| Aseprite JSON Parse | < 150 ms for 2k frames | Unit perf test | Single thread |
| Memory Overhead / Frame | ≤ 128 bytes metadata avg | Heap snapshot diff / frame count | Excluding image pixel data |
| Undo Command Creation | < 0.5 ms typical | Micro-benchmark | Use object pooling if exceeded |
| Export Large Set (50 anims) | < 8 s | Timed end‑to‑end | Parallelize safe parts |

Performance Enforcement Workflow:
1. Add micro benchmark (or timing assertion) when a budget is newly threatened.
2. If exceeding: create issue, label `perf`, attach profile flamegraph.
3. Optimize with measurable hypothesis; re-run baseline script.
4. Update budget only with explicit justification in `DECISIONS.md`.

Instrumentation Hooks (suggested):
- `Perf.mark(name)` / `Perf.measure(section)` lightweight wrapper.
- Central frame timing aggregator to surface worst 1% frame durations.

Caching Guidelines:
- Cache pure function outputs keyed by `sheetId + frameId + variant`.
- Invalidate on: grid parameter change, trim override, slice edit, layer visibility change.
- Avoid caching large RGBA surfaces unless reused within < 3 frames.

Memory Guardrails:
- Cap in‑memory decoded sheets to N (configurable, default 6). LRU discard least recently viewed.
- Support lazy slice overlay computation (only when visible toggle is on).

---

## 15. Extension Points & Plugin Contract

### Animation Source Interface (Authoritative)
```ts
interface AnimationSource {
  id(): string;                 // stable unique id (e.g. 'aseprite:<path-hash>')
  kind(): 'manual' | 'aseprite' | string; // allow future custom kinds
  listAnimations(): AnimationDescriptor[]; // lightweight descriptors
  loadAnimation(name: string): Animation | ErrorResult; // full object
  refresh(): boolean;           // returns true if underlying data changed
  isReadOnly(): boolean;        // manual=false, aseprite=true
  dispose?(): void;             // optional cleanup
}
```

### Loader Registration
```pseudo
AnimationSourceRegistry.register(factory: (context) -> AnimationSource)
```

### Expected Descriptor Shape
```jsonc
{
  "name": "run",
  "sheetId": "player_run",
  "frameCount": 12,
  "durationMsTotal": 996,
  "tags": ["movement"],
  "sourceKind": "aseprite",
  "readOnly": true
}
```

### Events / Observer Signals
- `sourceAdded(sourceId)`
- `sourceRemoved(sourceId)`
- `animationsChanged(sourceId)`
- `frameDataChanged(sheetId, frameId)` (triggers cache invalidation)

### Versioning & Compatibility
- Increment minor plugin API version only when adding *backwards compatible* optional methods.
- Increment major when removing or altering method signatures; gate by `pluginApiVersion` constant.

### Error Handling Policy
- No thrown exceptions across plugin boundary: return `ErrorResult { code, message, recoverable }`.
- UI surfaces friendly message + optional remediation hint.

### Determinism Guarantees
- `listAnimations()` ordering must be stable for identical underlying data.
- Frame durations must match exported representation bit‑for‑bit.

### Security Considerations
- Disallow plugin file system access outside allowed root (if sandbox available).
- Validate JSON before trusting frame counts / indices.

---

## 16. Agent Execution Workflow

### Core Loop (Each Work Session)
1. Sync context: Read open PRs / `DECISIONS.md` delta since last commit.
2. Identify current phase & next unfulfilled acceptance item.
3. Draft micro-plan (3–5 bullet tasks) → append to PR description or scratch buffer.
4. Execute smallest vertical slice; run unit tests; run smoke scenario.
5. Update decision log if an architectural or schema choice was made.
6. Benchmark if touching performance-sensitive path (see Section 14).
7. Commit with semantic prefix; push; request review if crossing phase boundary.

### Decision Log Entry Template
```
## 2025-09-12 Grid Model Refactor
Context: Need faster invalidation when spacing changes.
Options Considered: (A) Recompute all frame rects; (B) Store param struct + compute lazily.
Decision: Adopt (B); lazily compute on access; cache with generation counter.
Rejected Because: (A) O(n) invalidation per minor tweak caused visible stutter.
Impact: Frame accessor updated; analyzer unchanged.
Follow-Up: Add micro-benchmark for access pattern.
```

### When to Open an Issue
- Any blocker > 30 minutes without progress.
- Performance budget exceeded with reproducible profile.
- Export schema change required.
- Cross-cutting refactor touching >3 modules.

### Communication Signals (Lightweight)
- `// NOTE(agent): reason` inline for temporary compromises (must link task id).
- `BLOCKERS.md` ephemeral; entries removed once resolved & captured in issue if needed.

### Quality Gates Before Merging
- All new/changed public methods documented.
- No failing or skipped tests without justification.
- Lint / formatting passes clean (if tooling configured in stack).

---

## 17. Testing & PR Instructions

### Local Test Tiers
- `fast`: Pure logic (frame analyzer, pivot strategies, JSON parser) – run every save if watch mode available.
- `core`: Adds export + plugin registry tests – run before each commit.
- `full`: Adds playback timing & perf smoke – run before PR.

### Suggested Commands (Adapt per Stack)
```bash
# Fast unit subset
npm run test:fast                 # or dotnet test --filter Category=Fast

# Full suite
npm test                          # or pytest -m "not slow" && pytest -m slow

# Lint & type check
npm run lint && npm run typecheck
```

### Writing Tests Guidelines
- One assertion concept per test; descriptive name: `analyzer_trims_tightly_transparent_border()`.
- Use golden JSON fixtures for export—store in `tests/fixtures/exports/`.
- Provide corruption fixtures (missing frames, malformed slices) for negative parsing tests.
- Avoid testing UI pixels; test model state after simulated commands.

### Pull Request Checklist
- [ ] Title: `[phase-x] concise summary`
- [ ] Linked acceptance items enumerated
- [ ] Evidence artifacts (screens, timing output) attached
- [ ] Schema changes documented & version bumped
- [ ] Performance budgets respected (Section 14)
- [ ] Added / updated tests
- [ ] No console spam / debug logging

### Continuous Integration (Target)
- Jobs: `lint`, `test-fast`, `test-full`, `package`.
- Artifacts: Export sample JSONs, coverage report, packaged build if Phase ≥4.
- Failing budget thresholds mark PR with `needs-performance-review` label.

---

## 18. Troubleshooting Quick Reference

| Symptom | Likely Cause | Fast Check | Resolution |
|---------|--------------|------------|------------|
| Grid misaligned | Margin/spacing misapplied order | Log current params | Recompute frame rect order: margin → spacing |
| Choppy playback | Time accumulator drift | Log delta accumulation | Use fixed-step accumulator; clamp overshoot |
| Missing slices | JSON path mismatch | Inspect raw JSON `meta.slices` | Validate loader slice key paths |
| Pivot override ignored | Command not registered with undo | Check command stack entry | Wrap pivot change in Command pattern |
| High memory usage | Surfaces never released | Heap snapshot diff after sheet close | Implement LRU & call dispose() |
| Export diff unstable | Non-deterministic key iteration | Compare two exports | Enforce sorted key serialization |
| UI freeze on open | Synchronous large PNG decode | Profile main thread | Move decode to worker / async task |
| Layer filter no-op | Visibility flag not propagated | Inspect layer model state | Emit change event & invalidate cache |

Escalation Path:
1. Reproduce with minimal asset.
2. Open issue: label (`bug` + area label `grid|playback|export|parser|perf`).
3. Attach logs (timestamps + subsystem tag) & profiler output if perf.
4. Draft fix hypothesis; get review before large refactor.

Logging Guidelines:
- Structured: `[{timestamp}] {subsystem}:{level}:{message}`.
- Avoid verbose debug in hot loops; guard with debug flag.

---

## 19. Licensing, Attribution & Asset Usage

### Code Licensing
- Confirm intended project license (add `LICENSE` file if missing—MIT recommended for tooling unless otherwise specified).
- All third-party libraries must have permissive licenses (MIT/BSD/Apache) or compatible equivalents; record in `THIRD_PARTY.md`.

### Asset Policy
- Example sprite sheets used for testing must be either:
  - Created in-house (place in `assets/examples/` with `AUTHOR` note), or
  - From permissive public domain / CC0 sources (record source URL & license snippet).
- Do not commit proprietary or licensed game assets.

### Aseprite CLI Usage
- If invoking Aseprite externally, ensure user provides path via preferences.
- Do not bundle Aseprite binaries (proprietary). Detect presence gracefully.

### Exported JSON
- Generated JSON is user-owned output; avoid embedding telemetry or PII.
- Include `"tool": "AnimationViewer", "version": "<semver>"` in meta only.

### Security Notes
- Treat loaded JSON as untrusted: validate numeric ranges (non-negative, bounds ≤ sheet size).
- Avoid executing or evaluating any strings from JSON.

### Attribution Template
```
AnimationViewer
Copyright (c) 2025 <Owner>

Includes third-party components listed in THIRD_PARTY.md
```


### Common Issues
- **Aseprite Parsing Errors**: Verify JSON schema compliance; handle edge cases like missing slices or layers.
- **UI Layout Problems**: Ensure responsive design for different screen sizes.
- **Performance Bottlenecks**: Profile the application to identify slow operations.

### Getting Help
- **Refer to Documentation**: Most issues are covered in `COMPREHENSIVE_PROJECT_OVERVIEW.md` and `REBUILD_TASKLIST.md`.
- **Community Resources**: Consult framework-specific forums or documentation for implementation details.