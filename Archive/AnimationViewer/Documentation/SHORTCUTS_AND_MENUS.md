# AnimationViewer — Shortcuts & Menus Cheatsheet

Version: 1.0 (2025-09-12)
Scope: Derived from `ui/main_window.py` and `ui/main_window_temp.py` current bindings. Keep consistent when rebuilding `main_window.py`.

---

## Keyboard Shortcuts

- File
  - Ctrl+N: New Project
  - Ctrl+O: Open Sprite Sheet…
  - Ctrl+S: Save Animation
  - Ctrl+Shift+S: Save Animation As…
  - Ctrl+Q: Exit

- Edit / Selection
  - Ctrl+A: Select All Frames
  - Ctrl+D: Clear Selection

- View
  - G: Toggle Grid
  - H: Toggle Helpers/Overlays
  - T: Toggle Trim Analysis Mode
  - Ctrl++: Zoom In
  - Ctrl+-: Zoom Out

- Tools / Library
  - F5: Refresh Animation List
  - F1: Keyboard Shortcuts (placeholder dialog)

- Navigation
  - Arrow Keys: Move selection focus
  - Esc: Cancel/close contextual operations
  - Space: Reserved for preview controls (planned)

---

## Menu Structure (Current)

- File
  - New Project (Ctrl+N)
  - Open Sprite Sheet… (Ctrl+O)
  - Save Animation (Ctrl+S)
  - Save Animation As… (Ctrl+Shift+S)
  - Exit (Ctrl+Q)

- Edit
  - Select All Frames (Ctrl+A)
  - Clear Selection (Ctrl+D)
  - Preferences… (Ctrl+,)

- View
  - Toggle Grid (G)
  - Toggle Helpers/Overlays (H)
  - Toggle Trim Analysis (T)
  - Zoom In (Ctrl++)
  - Zoom Out (Ctrl+-)

- Animation
  - Create New Animation (from selection)
  - Refresh Animation List (F5)

- Help
  - Keyboard Shortcuts (F1)

Notes:
- Preferences dialog is under Edit and includes the Aseprite JSON toggle (Advanced tab).
- Keep these bindings stable in the `ui/main_window.py` rebuild to minimize user friction.
