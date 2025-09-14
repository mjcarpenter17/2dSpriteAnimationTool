# AnimationViewer — Language-Agnostic Rebuild Tasklist

Version: 2.0 (2025-09-12)
Companion: Read with `Documentation/COMPREHENSIVE_PROJECT_OVERVIEW.md` and `Documentation/SHORTCUTS_AND_MENUS.md`

Purpose: Provide a precise, end-to-end checklist to reconstruct the application in **any language or framework**. It uses the existing Python project as a functional reference.

---

## Phase 0 — Conceptual & Environmental Setup

- **Review Core Concepts**:
  - Read `COMPREHENSIVE_PROJECT_OVERVIEW.md` to understand the architecture, data schemas, and feature set.
  - Read `SHORTCUTS_AND_MENUS.md` to understand the required user interactions and key bindings.
  - Skim the Python reference source code (`Archive\AnimationViewer\core\`, `Archive\AnimationViewer\ui\`, `aseprite_loader.py`) to see a working implementation of the concepts.

- **Set Up Target Environment**:
  - Initialize a new project in your chosen language/framework (e.g., C++/Qt, C#/Godot, TypeScript/Electron).
  - Add a graphics library capable of 2D rendering, image loading (.png), and font rendering.
  - **Acceptance**: A blank window can be rendered, and you are ready to start implementing UI and core logic.

---

## Phase 1 — Main Window & Core UI Skeleton (Critical)

- **Archive Legacy Python File**:
  - In the reference project, rename `Archive\AnimationViewer\ui\main_window.py` to `Archive\AnimationViewer\ui\main_window_backup.py` to prevent accidental use.
  - **Acceptance**: The Python reference project is now non-functional, reinforcing that you are building from scratch.

- **Create Main Application Window**:
  - Implement the main application class/entry point.
  - Structure:
    - An `__init__` or constructor to set up the window, graphics context, clock, and load preferences.
    - A main `run()` loop containing `handle_events`, `update`, and `render` calls.
    - `handle_events()`: Process window close events, keyboard shortcuts (from cheatsheet), and mouse input.
    - `update(deltaTime)`: A hook for future time-based logic (can be a no-op initially).
    - `render()`: Clear the screen and draw panel placeholders.
  - **Acceptance**: A blank application window opens, runs in a loop, and can be closed.

- **Wire Minimal UI Subsystems**:
  - Implement placeholders for the main UI panels: a menu bar, a status bar, and a three-panel layout (left, center, right).
  - The menu bar should have the top-level entries: File, Edit, View, Animation, Help.
  - **Acceptance**: The application launches showing the basic panel layout and menu/status bars without crashing.

- **Integrate Preferences System**:
  - Implement a `PreferencesManager` class or equivalent. It must be able to:
    - Load/save settings from a JSON file in a standard user config directory (e.g., `%APPDATA%`).
    - Provide default values if the file is missing or corrupt.
    - See `COMPREHENSIVE_PROJECT_OVERVIEW.md` for the full list of preference keys.
  - **Acceptance**: App settings (like window size, colors) persist between sessions.

- **Implement File Operations**:
  - **Open**: Implement a `File > Open` action (shortcut `Ctrl+O`) that uses a native file dialog to select a `.png` file.
  - **Data Structure**: Create a `SpriteSheet` class/struct to hold the loaded image data, dimensions, and grid properties.
  - **Recent Files**: The `PreferencesManager` should track and persist a list of recently opened files.
  - **Acceptance**: A user can open a PNG spritesheet, and its metadata is loaded into the `SpriteSheet` data structure. The file appears in the "Recent Files" menu.

- **Implement Grid & Selection Logic**:
  - Render a grid of frames in the center panel based on the active `SpriteSheet`'s properties.
  - **Manual Grid Editing**: Implement UI controls (e.g., spinboxes/sliders in the properties panel) to manually edit the `tile size`, `margin`, and `spacing` of the current `SpriteSheet`. The grid view must update in real-time as these values are changed.
  - Implement mouse hit-testing to identify which frame is under the cursor.
  - **Selection**: Support multi-frame selection (e.g., `Ctrl+Click` for individual, `Shift+Click` for ranges) and preserve the selection order with visual numbering.
  - **Visuals**: Draw a visual highlight over selected frames showing selection order.
  - **Shortcuts**: Implement `Ctrl+A` (Select All) and `Ctrl+D` (Clear Selection).
  - **Acceptance**: A user can open a PNG, manually adjust the grid parameters until it aligns perfectly with the sprites, and select/deselect frames with clear visual feedback.

---

## Phase 2 — Core Logic & View Integration

- **Frame Analysis & Overlay (Automatic & Manual)**:
  - Implement a `FrameAnalyzer` module/class.
  - **Automatic Analysis**: It needs methods to calculate the pixel-perfect bounding box (trim box) and pivot point (default: bottom-center of the trim box) for any frame.
  - **Manual Override**: Implement UI controls allowing users to manually drag-and-drop pivot points and resize trim boxes for individual frames. Store these manual overrides with the frame data.
  - **UI**: Create a visual overlay system, toggled by `T` and `H` keys, to draw the trim box, pivot point, and other analysis data on the grid.
  - **Multiple Pivot Strategies**: Support different automatic pivot calculation strategies (center, bottom-center, custom).
  - **Acceptance**: Toggling analysis mode displays accurate automatic trim and pivot visuals. Users can manually override these values per-frame, and the overrides persist when saved.

- **Zoom & View Controls**:
  - Implement zoom functionality (`Ctrl++` / `Ctrl+-`) for the center frame grid.
  - Ensure all overlays (grid, selection, analysis) scale correctly with the zoom level.
  - **Acceptance**: The view zooms in and out smoothly, centered on the mouse or view center.

- **Animations Pane (Read-Only)**:
  - Implement the UI for the left-side "Animations Pane".
  - **Functionality**: It should be ableto display a list of discovered animations (from folders or Aseprite files). Initially, this can be a read-only list.
  - **Action**: Implement a refresh action (`F5`).
  - **Acceptance**: The pane renders a list of items and can be scrolled.

- **Tab/Multi-Sheet Strategy**:
  - Implement a system to manage multiple loaded `SpriteSheet` objects.
  - The UI should display tabs for each loaded sheet, allowing the user to switch between them.
  - **Acceptance**: The user can have multiple sprite sheets open and switch the active view between them.

---

## Phase 3 — Aseprite Integration (Toggleable)

- **Preferences Toggle**:
  - The `PreferencesManager` must have a boolean key (`advanced.use_aseprite_json`) to enable/disable this feature.
  - **Acceptance**: The toggle persists and is checked by the file-loading logic.

- **Auto-Detect Aseprite JSON**:
  - When opening a `.png` file, if Aseprite mode is enabled, check for a matching `<basename>.json` file.
  - **Parser**: Implement an `AsepriteLoader` module to parse the JSON data, extracting frame tags, durations, trim/slice info, layer data, and pixel aspect ratio.
  - **Advanced Features**: Parse slice data (hitboxes, pivots), layer information from frame names, and handle non-square pixel ratios.
  - **Feedback**: Report a comprehensive summary (e.g., "Loaded 5 animations, 12 slices, 3 layers from Aseprite file") to the status bar.
  - **Acceptance**: Loading a PNG with a corresponding JSON correctly populates all animation data structures including slices and layer metadata.

- **Animation Source Adapter**:
  - **Architecture**: Design a pluggable "Animation Source" system (e.g., using an interface or abstract class).
  - **Implementations**: Create two sources: `ManualAnimationSource` (for user-created selections) and `AsepriteAnimationSource`.
  - **UI**: The Animations Pane should consume data from all registered sources, marking Aseprite-derived animations as read-only.
  - **Acceptance**: The Animations Pane displays animations from both manual selections and Aseprite files, visually distinguishing between them.

---

## Phase 4 — Playback & Preview Engine

- **Animation Playback Controller**:
  - Implement a controller that can play an animation sequence.
  - **Features**: It must handle per-frame durations (in ms) and support playback directions (forward, reverse, ping-pong). Use a time-accumulator model for accuracy.
  - **Acceptance**: A given animation data structure plays back with correct timing and direction.

- **Preview UI**:
  - Create a small UI panel to render the currently playing animation frame.
  - Add basic controls like Play/Pause (`Space` key).
  - **Acceptance**: The user can select an animation and see it play back in the preview panel.

---

## Phase 5 — Export & Conversion Pipeline

- **Internal Format Exporter**:
  - Implement a function to convert an `Animation` data structure into the project's standard JSON format (see schema in overview).
  - **Metadata**: Ensure trim data, pivot points, and frame durations are included.
  - **Acceptance**: The exported JSON file is well-formed and contains all required data.

- **Aseprite-to-Internal Converter**:
  - Implement a function to convert animation data parsed from an Aseprite file into the internal `Animation` format.
  - **UI**: Allow batch-export of multiple selected Aseprite animations.
  - **Acceptance**: The converted animations can be played back and exported just like manually created ones.

---

## Phase 6 — Advanced Features (Slices, Layers)

- **Slices Parsing**:
  - Extend the `AsepriteLoader` to parse the `meta.slices` array.
  - **Data Structures**: Create `Slice` and `SliceKey` objects to store per-frame slice data (bounds, pivot).
  - **UI**: Add a visual overlay to render slices (e.g., hitboxes) on the preview and/or grid.
  - **Export**: Include slice data in the final export format.

- **Layers & Naming**:
  - Enhance the `AsepriteLoader` to parse layer information from frame names (e.g., `"Hero (Attack Layer) 1.ase"`).
  - **UI**: Add filtering options to the UI to show/hide specific layers.

- **Pixel Aspect Ratio**:
  - Read the `meta.pixelRatio` from Aseprite files.
  - Apply the correct scaling during rendering in the preview and grid.

---

## Phase 5 — Advanced Slice Management

- **Slice Visualization**:
  - Parse and display Aseprite slices as colored, labeled overlays in the main viewer.
  - **Types**: Support multiple slice types (hitbox, hurtbox, pivot, attachment, 9-slice).
  - **Per-Frame Data**: Handle slices that change position/size per frame.
  - **Toggle**: Add a UI toggle to show/hide slice overlays independently from other analysis modes.
  - **Acceptance**: Aseprite slices are correctly parsed and displayed with appropriate visual styling.

- **Manual Slice Editing**:
  - Implement UI controls to create, delete, and resize slices directly on frames.
  - **Properties**: Allow naming slices and setting their type (hitbox, hurtbox, etc.).
  - **Inheritance**: Provide options to copy slices between frames or animations.
  - **Acceptance**: Users can manually create and edit slices, and the data is preserved during export.

---

## Phase 6 — Professional Enhancement Features

- **Layer Support**:
  - Parse layer information from Aseprite frame names (e.g., "Player (Body) 1.ase").
  - **Filtering**: Implement UI controls (checkboxes) to toggle visibility of specific layers in previews.
  - **Layer-Based Pivots**: Allow different pivot strategies per layer.
  - **Acceptance**: Users can filter animations by layer and see layer-specific metadata.

- **Advanced Export System**:
  - **Rich JSON Schema**: Export animations with all metadata including slices, layers, pixel ratios, and custom properties.
  - **Batch Export**: Allow users to select multiple animations and export them all at once.
  - **Format Options**: Support multiple export formats optimized for different game engines.
  - **Validation**: Validate exported data for completeness and accuracy.
  - **Acceptance**: The export system produces industry-standard JSON that includes all available metadata.

- **Undo/Redo System**:
  - Implement a comprehensive undo/redo system for all user actions.
  - **Actions**: Cover sprite sheet grid changes, manual pivot adjustments, slice edits, and animation modifications.
  - **Performance**: Use efficient command pattern to avoid memory issues with large operations.
  - **Acceptance**: All major user operations can be undone and redone reliably.

- **Professional UI Polish**:
  - **Onion Skinning**: Show ghost images of previous/next frames during animation preview.
  - **Timeline Scrubber**: Add a timeline control for precise frame navigation during playback.
  - **Tooltips and Help**: Comprehensive tooltips and context-sensitive help throughout the interface.
  - **Performance Indicators**: Show frame rate, memory usage, and other performance metrics.
  - **Acceptance**: The UI feels polished and professional, comparable to commercial animation tools.

---

## Cross-Cutting Concerns & Final Checks

- **Keyboard Parity**: Ensure all shortcuts from `SHORTCUTS_AND_MENUS.md` are implemented.
- **Error Handling**: Provide clear, user-friendly error messages for file-not-found, corrupted JSON, etc.
- **Performance**: Ensure the UI remains responsive (>30 FPS) even with large sprite sheets.
- **Final Verification**:
  - **Basic Functionality**: Can you open a PNG? Can you manually adjust grid parameters (tile size, margin, spacing)?
  - **Frame Selection**: Can you select frames and create/save an animation with proper metadata?
  - **Aseprite Integration**: Can you open a PNG+JSON pair and see Aseprite animations with slices and layers?
  - **Manual Overrides**: Can you manually adjust pivot points and trim boxes for individual frames?
  - **Advanced Features**: Can you view and edit slices? Can you filter animations by layer?
  - **Export System**: Can you export animations to rich JSON format with all metadata? Does batch export work?
  - **Cross-Sheet Workflow**: When opening an animation that belongs to a different sprite sheet, does a new tab open automatically?
  - **Professional Polish**: Do undo/redo, onion skinning, and timeline scrubbing work correctly?
  - **Performance**: Does the UI remain responsive with large sprite sheets and many animations?
  - **Shortcuts and Preferences**: Do all keyboard shortcuts and preference settings work as expected?

---

## Reference Implementation Commands (PowerShell)

*These commands are for running the **original Python project** for comparison.*
```pwsh
# Run the Python reference app
cd "c:\Users\Michael\Documents\Test Games\Walk_GhCp_Test\AnimationViewer"
..\.venv\Scripts\Activate
python main.py

# Syntax check a Python module
python -m py_compile ui\main_window.py

# Reset corrupted preferences (Windows)
$pref = Join-Path $env:APPDATA 'SpriteAnimationTool/preferences.json'
Remove-Item $pref -ErrorAction SilentlyContinue
```