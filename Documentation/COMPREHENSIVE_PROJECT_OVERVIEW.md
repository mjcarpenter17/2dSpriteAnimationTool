# AnimationViewer - Co## 🚀 Porting Guide & Language-Agnostic Rebuild

This project is slated for a complete rebuild, potentially in a new language or framework. The existing Python/Pygame codebase should be treated as a **functional reference implementation**, not a base for further development.

- **Primary Goal**: Port the application's features and architecture to a modern, maintainable stack.
- **Primary Document**: The `Documentation/REBUILD_TASKLIST.md` contains a detailed, language-agnostic plan for this process.
- **Reference Code**: Use the current `.py` files to understand the logic, algorithms (e.g., `frame_analyzer.py`), and data structures (`Archive\AnimationViewer\core\animation.py`, `Archive\AnimationViewer\core\spritesheet.py`).

**The `Archive\AnimationViewer\ui\main_window.py` file is considered deprecated and should be replaced entirely, not debugged.** Its structural issues are the primary motivation for the rebuild.

## 📋 Current Project Status

### ✅ **What's Completed (Reference Implementation)**
- **Architecture Foundation**: A modular, class-based architecture is in place.
- **Multi-Spritesheet Support**: Dynamic loading and management of multiple sprite sheets.
- **UI Framework Concept**: A panel-based layout with menus, a toolbar, and a status bar.
- **Animation Discovery**: Automatic detection and management of animation files.
- **Frame Analysis System**: Advanced trim detection and pivot point calculation.
- **File Management**: Native dialogs, recent files, and project structure concepts.
- **Export System**: JSON and Python format export with metadata.

### ⚠️ **Legacy Technical State**
- **Core Issue**: The main UI file (`Archive\AnimationViewer\ui\main_window.py`) is unmaintainable due to severe code duplication.
- **Status**: This file prevents the application from launching correctly and is the catalyst for the porting effort.
- **Resolution**: Do not attempt to fix the Python implementation. Proceed directly with the language-agnostic rebuild plan.ject Overview for Future Agents

**Document Version**: 1.0  
**Created**: September 12, 2025  
**Purpose**: Complete technical and functional overview for development continuation  
**Target Audience**: AI Development Agents and Technical Contributors  

---

## 🎯 Project Mission Statement

The **AnimationViewer** is a professional-grade sprite animation creation and management tool for 2D game development. It transforms static sprite sheets into animation sequences with advanced features like automatic frame analysis, pivot point detection, multi-format export, and seamless Aseprite integration.

**Core Value Proposition**: Bridge the gap between sprite creation (especially Aseprite) and game engine integration. Provide a unified workflow for inspecting, creating, and managing 2D sprite animations with professional-grade tools.

---

## � Quick Links
- Shortcuts & Menus Cheatsheet: `Documentation/SHORTCUTS_AND_MENUS.md`
- Rebuild Tasklist: `Documentation/REBUILD_TASKLIST.md`


## �📋 Current Project Status

### ✅ **What's Completed (Phase 1)**
- **Architecture Foundation**: Complete modular class-based architecture replacing monolithic approach
- **Multi-Spritesheet Support**: Dynamic loading and management of multiple sprite sheets
- **Professional UI Framework**: Panel-based layout with menus, toolbar, and status bar
- **Animation Discovery**: Automatic detection and management of animation files
- **Frame Analysis System**: Advanced trim detection and pivot point calculation
- **File Management**: Native dialogs, recent files, project structure
- **Export System**: JSON and Python format export with metadata

### ⚠️ **Current Technical Challenge**
- **Main Window Issues**: `Archive\AnimationViewer\ui\main_window.py` has structural problems from code duplication
- **Status**: Application runs (Exit Code: 0) but has syntax errors preventing import
- **Need**: Clean rebuild of main window using established architecture patterns

### 🎯 **Next Phase Targets (Phase 2)**
- **Animation Preview Engine**: Real-time playback with frame timing
- **Enhanced Creation Tools**: Timeline editor, frame manipulation
- **Aseprite Integration**: Full JSON import/export pipeline
- **Advanced Export Options**: Multiple formats, batch processing

---

## 🏗️ Technical Architecture

### **Core Application Structure**
```
AnimationViewer/
├── main.py                     # Application entry point
├── Archive\AnimationViewer\core\                       # Core business logic
│   ├── animation.py           # Animation class (377 lines)
│   ├── frame_analyzer.py      # Trim analysis and pivot detection
│   ├── project.py             # Project management
│   ├── spritesheet.py         # SpriteSheet class (353 lines)
│   └── sprite_manager.py      # Multi-sheet management
├── Archive\AnimationViewer\ui\                        # User interface components
│   ├── main_window.py         # Main application (⚠️ needs rebuild)
│   ├── animations_pane.py     # Animation library browser (831 lines)
│   ├── analysis_overlay.py    # Visual analysis overlays
│   ├── menu_system.py         # Professional menu bar
│   ├── status_bar.py          # Contextual status display
│   ├── preferences.py         # Settings management
│   └── panels/                # Specialized UI panels
├── Archive\AnimationViewer\utils\                     # Utility modules
│   └── file_manager.py        # File operations with native dialogs
├── animation_manager.py       # High-level animation discovery
├── animation_sources.py       # Plugin architecture for animation sources
└── aseprite_loader.py         # Aseprite JSON parsing (192 lines)
```

#### **Enhanced Data Structures for Advanced Features**

```python
# Core Animation Data
class Frame:
    frame_index: Tuple[int, int]  # (row, col)
    duration: int  # milliseconds
    source_rect: Rect
    trim_rect: Optional[Rect]  # Can be manually overridden
    pivot: Point  # Can be manually overridden
    pivot_strategy: str  # "auto", "manual", "slice-based"
    layers: List[str]
    slices: List[Slice]

class Slice:
    name: str
    bounds: Rect  # Relative to frame
    slice_type: str  # "hitbox", "hurtbox", "pivot", "attachment", "9slice"
    pivot: Optional[Point]
    metadata: Dict[str, Any]  # Custom properties

class Animation:
    name: str
    spritesheet_id: str
    frames: List[Frame]
    direction: str  # "forward", "reverse", "pingpong"
    loop: bool
    source_type: str  # "manual", "aseprite"
    read_only: bool
    layers: List[str]  # All layers present in animation

class SpriteSheet:
    filepath: str
    tile_size: Tuple[int, int]  # Can be edited manually
    margin: int  # Can be edited manually
    spacing: int  # Can be edited manually
    pixel_ratio: Tuple[float, float]  # For non-square pixels
    name: str
    layers: List[str]  # Parsed from Aseprite if available
    
# Animation Sources
class IAnimationSource:
    def list_animations() -> List[AnimationDescriptor]
    def get_animation(descriptor_id: str) -> Animation
    def is_read_only() -> bool
    def refresh() -> bool

class AsepriteAnimationSource(IAnimationSource):
    json_path: str
    sprite_path: str
    frame_tags: List[FrameTag]
    slices: List[AsepriteSlice]
    layers: List[Layer]

# UI Components
class SliceEditor:
    def create_slice(frame: Frame, slice_type: str) -> Slice
    def edit_slice(slice: Slice) -> None
    def delete_slice(slice: Slice) -> None

class UndoRedoManager:
    def execute_command(command: Command) -> None
    def undo() -> bool
    def redo() -> bool
    def clear_history() -> None
```

### **Key Classes and Relationships**
```python
class SpriteAnimationTool:
    # Core Systems
    self.project: AnimationProject
    self.file_manager: FileManager
    self.preferences: PreferencesManager
    self.frame_analyzer: FrameAnalyzer
    
    # UI Components
    self.menu_bar: MenuBar
    self.status_bar: StatusBar
    self.animations_pane: AnimationsPane
    self.analysis_overlay: AnalysisOverlay
    
    # State Management
    self.active_sheet: Optional[SpriteSheet]
    self.selected_frames: List[Tuple[int, int]]
    self.animation_manager: AnimationManager
```

#### **SpriteSheet** (Core Data Structure)
```python
class SpriteSheet:
    # Properties
    filepath: str
    tile_size: Tuple[int, int]
    margin: int, spacing: int
    name: str
    
    # Grid System
    cols: int, rows: int
    total_tiles: int
    
    # Methods
    get_tile_at(row, col) -> pygame.Surface
    analyze_frame(row, col) -> FrameAnalysisResult
    validate() -> bool
```

#### **Animation** (Animation Data Structure)
```python
class Animation:
    name: str
    spritesheet_id: str
    frames: List[Tuple[int, int]]  # (row, col) pairs
    frame_durations: List[int]     # milliseconds per frame
    loop_settings: Dict[str, Any]
    export_settings: Dict[str, Any]
    
    # Methods
    add_frame(row, col, duration)
    get_total_duration() -> int
    to_dict() -> Dict  # For JSON export
```

---

## 🔧 Core Functionality Specifications

### **1. Sprite Sheet Configuration & Management**
- **Dynamic Loading**: Import sprite sheets (`.png`, `.jpg`, etc.) from any source via native file dialogs.
- **Manual Grid Adjustment**: After loading, provide UI controls to interactively edit the sprite sheet's `tile size`, `margin`, and `spacing`. The grid preview should update in real-time.
- **Multi-Sheet Workflow**: Manage multiple open sprite sheets in a tabbed interface. If an animation is opened that belongs to a non-active sheet, the tool will automatically switch to or open the correct sheet in a new tab.

### **2. Frame Selection System**
- **Multi-select**: Ctrl+Click for individual frames, Shift+Click for range selection.
- **Order Preservation**: Maintains sequence for animation creation.
- **Visual Feedback**: Highlighted frames with selection order indicators.
- **Keyboard Navigation**: Arrow keys, selection helpers (Ctrl+A, Ctrl+D).

### **3. Frame Analysis Engine (Automatic & Manual)**
- **Automatic Trim Detection**: Pixel-perfect bounding box calculation on-demand.
- **Automatic Pivot Points**: Default to bottom-center pivot for character animations, but offer other strategies (e.g., center, top-left).
- **Manual Pivot Adjustment**: Allow users to drag-and-drop the pivot point for any individual frame. The new coordinates are stored with the frame's metadata.
- **Manual Trim Adjustment**: Allow users to resize the trim-box for any individual frame.
- **Analysis Overlay**: Visual indicators for trim bounds, pivot points, and frame origins.
- **Caching**: Performance optimization for repeated analysis.

### **4. Animation Discovery System**
- **Automatic Scanning**: Detects existing animation files (`.json`) in specified project directories.
- **Metadata Extraction**: Pre-loads frame count, source sheet, and other details for fast browsing.
- **Cross-Sheet Loading**: As mentioned, opening an animation automatically handles loading its parent sprite sheet.

### **5. Export Pipeline**
- **JSON Format**: Export to a standard, game-engine compatible JSON format that includes all critical metadata.
- **Python Module**: (Optional) Direct integration format for Python games.
- **Metadata Inclusion**: Guarantees inclusion of trim data, pivot points, frame durations, loop settings, and slice data.
- **Batch Processing**: Export multiple selected animations simultaneously.

---

## 🎨 User Interface Specifications

### **Layout System**
```
┌─────────────────────────────────────────────────────────────┐
│                  Menu Bar + Toolbar                        │
├─────────┬─────────────────────────────────────┬─────────────┤
│ Anims   │                                     │ Properties  │
│ Pane    │         Frame Grid Selector         │ Panel       │
│ ├─────┤ │                                     │ ┌─────────┐ │
│ │walk │ │         [Grid of Frames]            │ │Selected:│ │
│ │jump │ │                                     │ │8 frames │ │
│ │idle │ │                                     │ └─────────┘ │
│ └─────┘ │                                     │ Preview     │
│ Controls│                                     │ ┌─────────┐ │
│         │                                     │ │[thumb]  │ │
└─────────┴─────────────────────────────────────┴─────────────┤
│ Status Bar: Sheet info | Selection | Operation status      │
└─────────────────────────────────────────────────────────────┘
```

### **Panel Specifications**

#### **Animations Pane** (Left Panel)
- **Purpose**: Animation library browser and management
- **Features**: 
  - Folder-based organization with color-coded headers
  - Animation metadata display (frame count, source sheet)
  - Cross-spritesheet animation loading
  - External source integration (Aseprite JSON)
- **Interactions**: Click to load, context menus for management

#### **Frame Grid** (Center Panel)
- **Purpose**: Primary sprite sheet viewer and frame selector
- **Features**:
  - Scalable grid display with customizable tile sizes
  - Multi-frame selection with visual feedback
  - Analysis overlay toggle (trim bounds, pivot points)
  - Scroll and zoom support for large sprite sheets

#### **Properties Panel** (Right Panel)
- **Purpose**: Animation details and creation tools
- **Features**:
  - Selected frame information
  - Animation preview area
  - Export configuration
  - Frame timing controls (future)

### **Menu System**
- **File**: New Project, Open Sprite Sheet, Recent Files, Save Animation, Export
- **Edit**: Select All, Clear Selection, Preferences
- **View**: Grid Toggle, Analysis Mode, Panel Visibility, Zoom Controls
- **Animation**: Create Animation, Load Animation, Refresh Library
- **Help**: Keyboard Shortcuts (see `Documentation/SHORTCUTS_AND_MENUS.md`), Documentation

---

## 🔌 Integration Systems

### **Aseprite Integration**
- **JSON Parsing**: Complete Aseprite JSON format support
- **Automatic Import**: Detects and loads Aseprite files alongside sprite sheets
- **Animation Tags**: Imports frameTags as pre-defined animations
- **Frame Timing**: Uses Aseprite duration data for accurate playback
- **Slice Support**: Future support for hitboxes and pivot slices

### **Plugin Architecture** (Animation Sources)
```python
class IAnimationSource:
    def list_descriptors() -> List[AnimationDescriptor]
    def get_animation_data(descriptor_id) -> AnimationData
    def refresh() -> bool
    def is_read_only() -> bool
```

**Current Sources**:
- **ManualAnimationSource**: User-created animations via frame selection
- **AsepriteAnimationSource**: Aseprite JSON file animations

---

## ✨ Advanced Features & Professional Tooling

This section outlines features that elevate the tool from a basic animation creator to a professional-grade utility, drawing heavily on Aseprite's advanced capabilities and common game development needs.

### **1. Advanced Slice Management**
- **Concept**: Slices are named rectangular areas within a frame, used to define hitboxes, hurtboxes, attachment points, or 9-slice scaling regions.
- **Features**:
  - **Parsing**: Ingest slice data from Aseprite JSON, including per-frame slice positions.
  - **Visualization**: Render slices as colored, labeled overlays in the main viewer and preview panel. Add a toggle for slice visibility.
  - **Manual Editing**: Allow users to create, delete, and resize slices directly on a frame.
  - **Data Export**: Include slice data in the final JSON export in a clean, engine-readable format.

### **2. Layer Support**
- **Concept**: Aseprite projects can have multiple layers. This information is often encoded in frame names.
- **Features**:
  - **Layer Parsing**: Extract layer information from Aseprite frame names (e.g., `"Player (Body) 1.ase"`).
  - **Layer Filtering**: Provide UI controls (e.g., checkboxes in the properties panel) to toggle the visibility of specific layers in the animation preview.

### **3. Pixel Aspect Ratio**
- **Concept**: Aseprite supports non-square pixels, which affects rendering.
- **Features**:
  - **Parsing**: Read the `pixelRatio` from the Aseprite JSON `meta` section.
  - **Rendering**: Correctly scale the sprite rendering in the grid and preview panels to reflect the proper aspect ratio.

### **4. Command-Line Interface (CLI) Integration**
- **Concept**: Leverage Aseprite's powerful CLI for batch processing and automation.
- **Potential Features (Future Phase)**:
  - **Batch Export**: A script to watch a folder of `.aseprite` files and automatically export them to `.png` and `.json`.
  - **Validation Tool**: A CLI tool to validate a directory of animation JSONs for consistency or errors.
  - **Conversion Utilities**: Tools to convert between different animation formats.

### **5. Professional Animation Tools**
- **Undo/Redo System**: Comprehensive command pattern implementation covering all user actions (grid changes, pivot adjustments, slice edits).
- **Onion Skinning**: Display ghost images of previous/next frames during animation preview for better animation flow visualization.
- **Timeline Scrubber**: Precise frame navigation control with visual timeline representation.
- **Performance Monitoring**: Real-time display of frame rate, memory usage, and rendering performance.
- **Batch Processing**: Select and process multiple animations simultaneously for export or modification.

### **6. Cross-Sheet Animation Workflow**
- **Concept**: Seamless handling of animations that span multiple sprite sheets.
- **Features**:
  - **Automatic Tab Management**: When loading an animation that references a different sprite sheet, automatically open the required sheet in a new tab.
  - **Tab Switching**: Quick navigation between related sprite sheets.
  - **Animation Library**: Unified view of all animations across all open sprite sheets.

---

## 🎯 Development Priorities & Porting Roadmap

The primary priority is to execute the language-agnostic rebuild as detailed in `Documentation/REBUILD_TASKLIST.md`. The following phases are conceptual stages of the porting process.

### **Phase 1: Core Skeleton & UI Foundation (Critical)**
1.  **Build the Main Application Shell**: Implement the main window, menu bar, status bar, and panel layout.
2.  **Implement Core Systems**: Create the `PreferencesManager` and `FileManager` equivalents.
3.  **Establish Stable Main Loop**: Ensure the application runs, handles events, and renders correctly.

### **Phase 2: Feature Implementation (High Priority)**
1.  **Sprite Sheet Handling**: Implement the `SpriteSheet` data model and the grid view for frame selection.
2.  **Frame Analysis Engine**: Port the logic from `Archive\AnimationViewer\core\frame_analyzer.py` to calculate trim boxes and pivot points.
3.  **Animation Data Model**: Implement the `Animation` class and the basic "Create Animation from Selection" feature.
4.  **Export System**: Implement the JSON export functionality.

### **Phase 3: Advanced Integration & Polish (Medium Priority)**
1.  **Animation Discovery & Management**: Implement the `AnimationsPane` and the logic for discovering existing animation files.
2.  **Aseprite Integration**: Port the `aseprite_loader.py` logic and integrate it via the `IAnimationSource` plugin pattern.
3.  **Advanced Feature Implementation**:
    -   **Slice Visualization**: Render Aseprite slices as overlays.
    -   **Manual Pivot/Trim**: Implement UI for manual adjustment of pivots and trim boxes.
    -   **Sprite Sheet Editing**: Add controls for editing grid properties.
4.  **UI Polish**: Implement visual feedback, overlays, and advanced controls.

### **Phase 4: Professional Tooling (Low Priority)**
1.  **Advanced Slice Editing**: Allow creation, deletion, and modification of slices.
2.  **Layer Filtering**: Implement UI to toggle layer visibility.
3.  **CLI Tools**: Develop batch processing and validation scripts.

---

## 📊 Data Format Specifications

### **Animation JSON Format (Target Schema)**
```json
{
  "animationName": "walk",
  "spritesheet": "character.png",
  "totalDuration": 800,
  "loop": true,
  "direction": "forward",
  "frames": [
    {
      "frame": { "row": 0, "col": 0 },
      "duration": 100,
      "sourceRect": { "x": 0, "y": 0, "w": 90, "h": 37 },
      "trimRect": {"x": 5, "y": 2, "w": 25, "h": 30},
      "pivot": {"x": 12, "y": 29, "strategy": "manual"},
      "layers": ["body", "weapon"],
      "slices": [
        {
          "name": "hitbox",
          "bounds": {"x": 10, "y": 10, "w": 15, "h": 20},
          "type": "hitbox",
          "pivot": {"x": 17, "y": 20},
          "metadata": {"damage": 10, "knockback": 5}
        },
        {
          "name": "attachment_point",
          "bounds": {"x": 20, "y": 5, "w": 2, "h": 2},
          "type": "attachment",
          "pivot": {"x": 21, "y": 6}
        }
      ]
    }
  ],
  "pixelRatio": {"x": 1, "y": 1},
  "meta": {
    "tool": "AnimationViewer",
    "version": "2.0",
    "exported": "2025-09-12T12:00:00Z",
    "source": "aseprite",
    "originalFile": "character.aseprite"
  }
}
```

### **Aseprite JSON Support**
- **Meta Section**: `image` path, `size`, `format`, and `pixelRatio`.
- **Frames Object**: Frame coordinates (`frame`), trim data (`spriteSourceSize`, `sourceSize`), and `duration`.
- **Frame Tags**: Animation definitions (`name`, `from`, `to`, `direction`).
- **Slices Array**: Per-frame slice definitions (`name`, `keys`, `data`). This is critical for hitboxes and advanced pivots.

---

## 🔍 Quality Metrics and Standards

### **Code Quality**
- **Type Hints**: Full type annotation throughout codebase
- **Documentation**: Comprehensive docstrings for all classes and methods
- **Error Handling**: Graceful failure with user-friendly error messages
- **Testing**: Unit tests for core functionality, integration tests for workflows

### **Performance Targets**
- **Startup Time**: < 2 seconds for typical projects
- **Frame Selection**: < 50ms response time for large sprite sheets
- **Export Speed**: < 1 second per animation for typical frame counts
- **Memory Usage**: Efficient caching and lazy loading for large assets

### **User Experience Standards**
- **Keyboard Accessibility**: All features accessible via keyboard shortcuts
- **Visual Feedback**: Clear indication of current state and operations
- **Error Prevention**: Validation and confirmation for destructive operations
- **Undo Support**: Comprehensive undo/redo for all user actions

---

## 🛠️ Development Environment

### **Technology Stack**
- **Python**: 3.7+ (typing support, dataclasses)
- **Pygame**: 2.0+ (graphics, input handling, file operations)
- **Standard Library**: json, os, sys, datetime, typing

### **Dependencies**
- **Core**: pygame, typing_extensions (if Python < 3.8)
- **Optional**: tkinter (file dialogs), PIL (advanced image processing)

### **Development Tools**
- **Code Style**: PEP 8 compliance
- **Type Checking**: mypy compatibility
- **Documentation**: Standard Python docstring format

---

## 📈 Future Roadmap

### **Phase 4: Advanced Animation Features**
- **Onion Skinning**: Ghost frame visualization
- **Frame Interpolation**: Smooth animation preview
- **Advanced Timeline**: Multi-track editing, nested animations

### **Phase 5: Workflow Integration**
- **Version Control**: Git integration for animation assets
- **Collaboration**: Multi-user project support
- **Asset Pipeline**: Integration with common game development workflows

### **Phase 6: Platform Integration**
- **Game Engine Plugins**: Direct export to Unity, Godot, Unreal
- **Format Support**: Additional import/export formats (GIF, WebP, texture atlases)
- **Performance Optimization**: Hardware acceleration, parallel processing

---

## 🚀 Quick Start for New Agents (Porting Reference)

### **Understanding the Reference Codebase**
1. **Start with**: `main.py` - Understand the application entry point and initialization sequence.
2. **Core Logic**: `Archive\AnimationViewer\core\` directory - This contains the essential business logic and data structures (`SpriteSheet`, `Animation`, `FrameAnalyzer`). This logic should be ported.
3. **UI Components**: `Archive\AnimationViewer\ui\` directory - Use these files as a reference for the features and layout of the UI components that need to be rebuilt.
4. **Key Algorithms**: Pay close attention to `Archive\AnimationViewer\core\frame_analyzer.py` for the trim and pivot calculation logic, which is a critical feature to preserve.

### **Porting Approach**
1. **Follow the Tasklist**: The primary guide for the rebuild is `Documentation/REBUILD_TASKLIST.md`.
2. **Architecture First**: Re-implement the modular design patterns in the target language/framework.
3. **Incremental Development**: Build and test components independently, using the reference implementation to validate behavior.
4. **User Experience Focus**: Prioritize usability and workflow efficiency, preserving the UX outlined in this document.

### **Testing Strategy**
1. **Reference Comparison**: Use the existing Python application (once the `main_window.py` is stubbed out to allow it to run) to compare behavior.
2. **Unit Testing**: Write unit tests for core logic (e.g., frame analysis, data models) as you port it.
3. **Integration Testing**: Test complete workflows (e.g., load sheet -> select frames -> create animation -> export) end-to-end.
4. **Asset Validation**: Use the provided sprite sheet assets for validation.

---

## 📞 Context and Historical Notes

### **Project Evolution**
- **Original**: Single-file viewer.py script with hardcoded limitations
- **Phase 1**: Complete architecture refactoring with professional UI
- **Current**: Multi-spritesheet tool with advanced animation management
- **Future**: Professional animation pipeline integration tool

### **Design Decisions**
- **Pygame Choice**: Provides low-level control needed for pixel-perfect frame analysis
- **Modular Architecture**: Enables easy extension and maintenance
- **Plugin System**: Supports multiple animation sources (manual, Aseprite, future tools)
- **Data Format**: JSON-based for game engine compatibility

### **Known Technical Debt**
- **Main Window Duplication**: Current main_window.py has structural issues
- **Error Handling**: Some edge cases need better user feedback
- **Performance**: Large sprite sheet loading could be optimized
- **Testing Coverage**: Needs comprehensive test suite

---

## 🚪 Startup & Entry Points

- Entry: `AnimationViewer/main.py` initializes pygame, loads preferences, and starts `ui.main_window.SpriteAnimationTool`.
- UI boot: Menu bar, toolbar, panels, and status bar are constructed during `SpriteAnimationTool.__init__`.
- Preferences load before UI build to honor initial layout and toggles.

---

## 🛠️ Quick Start & Setup

On Windows PowerShell, from the project root:
```
cd "c:\Users\Michael\Documents\Test Games\Walk_GhCp_Test\AnimationViewer"
python -m venv ..\.venv
..\.venv\Scripts\Activate
pip install -r ..\requirements.txt
python main.py
```
Notes:
- First run creates `%APPDATA%/SpriteAnimationTool/preferences.json`.
- The sample spritesheet lives at `Assests/Sword Master Sprite Sheet 90x37.png`.

---

## ⚙️ Preferences Reference (from `Archive\AnimationViewer\ui\preferences.py`)

- `general.default_export_dir`: string path (Documents/Animations default)
- `general.animation_naming_pattern`: string (e.g., `{sheet_name}_{animation_type}`)
- `general.auto_save_interval`: seconds (int)
- `general.recent_files_limit`: int
- `general.remember_window_state`: bool
- `general.show_tooltips`: bool

- `display.grid_color`: hex string
- `display.grid_opacity`: 0..1
- `display.selection_color`: hex string
- `display.selection_opacity`: 0..1
- `display.background_color`: hex string
- `display.ui_theme`: `default|dark|light`
- `display.show_frame_numbers`: bool
- `display.show_tile_info`: bool

- `file_management.last_sprite_dir`: path
- `file_management.last_export_dir`: path
- `file_management.recent_sprite_sheets`: list of paths
- `file_management.auto_cleanup_orphaned`: bool
- `file_management.backup_animations`: bool

- `layout.window_width|height|x|y`: ints (`-1` centers)
- `layout.left_panel_width`: int
- `layout.right_panel_width`: int
- `layout.animation_panel_height`: int

- `advanced.memory_limit_mb`: int
- `advanced.enable_debug_logging`: bool
- `advanced.max_undo_levels`: int
- `advanced.tile_cache_size`: int
- `advanced.background_processing`: bool
- `advanced.use_aseprite_json`: bool (Aseprite mode toggle)

Persistence: `%APPDATA%/SpriteAnimationTool/preferences.json` (Windows). Use `PreferencesManager.get/set`, and `add_observer` for live updates.

---

## ⌨️ Keyboard Shortcuts Matrix

- File: `Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`, `Ctrl+Q`
- Edit: `Ctrl+A` (Select All), `Ctrl+D` (Clear Selection)
- View: `G` (Grid), `H` (Helpers/Overlays), `T` (Trim Analysis), `Ctrl++`, `Ctrl+-`
- Tools: `F5` (Refresh Animations), `F1` (Shortcuts — placeholder)
- Navigation: Arrow Keys; `Esc` cancel/contextual; `Space` reserved for preview controls

These bindings exist in `Archive\AnimationViewer\ui\main_window.py` and `Archive\AnimationViewer\ui\main_window_temp.py`; keep them for continuity in the rebuild.

---

## 📄 Data & JSON Schemas

Internal animation JSON (typical):
```json
{
  "animation": "walk",
  "spritesheet": "Sword Master Sprite Sheet 90x37.png",
  "frames": [
    { "x": 0, "y": 0, "w": 90, "h": 37, "duration": 100, "trim": {"x": 2, "y": 0, "w": 86, "h": 37}, "pivot": {"x": 43, "y": 36} }
  ],
  "loop": true,
  "meta": { "created": "ISO8601", "tool": "AnimationViewer" }
}
```

Aseprite JSON ingestion:
- `meta.image`: spritesheet path; `frames` entries include `frame` rect, `duration`, `spriteSourceSize`, `sourceSize`.
- `meta.frameTags`: `{ name, from, to, direction }` define animations.
- Optional `meta.slices`: per-frame slice keys (hitbox, pivot, center) — future.

Mapping strategy:
- Build `AnimationDescriptor` per tag with ordered frames and durations.
- Use `spriteSourceSize`/`sourceSize` for trim/pivot derivation; normalize direction for playback.

---

## 🧪 Testing & Verification

- Syntax: `python -m py_compile` on edited modules.
- Launch: `python main.py`, open the sample PNG, verify grid/selection.
- Preferences: toggle Aseprite JSON usage (Advanced tab); ensure persistence.
- Aseprite: when enabled, if `<image>.json` exists beside `<image>.png`, report summary after load.
- Export: create a small animation, save, and verify frames, durations, and metadata.

---

## 🧯 Troubleshooting

- Import errors in `Archive\AnimationViewer\ui\main_window.py`: caused by duplicated `else/elif` and block copies — archive and rebuild per plan.
- Pygame window not opening: activate venv and ensure `pygame` installed from `requirements.txt`.
- Corrupted preferences: delete `%APPDATA%/SpriteAnimationTool/preferences.json` to regenerate defaults.
- Aseprite JSON not detected: set `advanced.use_aseprite_json` true and ensure matching basename `.json` and `.png` paths.

---

## 🧩 Aseprite Slices, Layers, Pixel Ratio (Planned)

- Slices: Parse `meta.slices` with per-frame keys for hitboxes, hurtboxes, pivots, and 9-slice center; overlay in viewer; export to game format.
- Layers: Extract layer info from frame names; add layer filters and multi-layer preview; support layer-based pivot strategies.
- Pixel Aspect: Honor `meta.pixelRatio` for non-square pixels during preview and export scaling.

See `ProjectPlan/ASpriteProjectOverview.md` and `ProjectPlan/AspritePhasedTaskList.md` for phased work and acceptance criteria.

---

*This document serves as the definitive guide for continuing development of the AnimationViewer project. It provides all necessary context for agents to understand the current state, technical architecture, and development priorities.*