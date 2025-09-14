I want to create a professional sprite animation tool based on the project plan documents. Please start by reviewing these documents to understand the scope and architecture:

1. **Review Project Overview**: Read `\AnimationViewer\ProjectPlan\sprite_animation_tool_overview.md` to understand the complete project vision, technical architecture, and goals.

2. **Review Phase 1 Tasks**: Study `\AnimationViewer\ProjectPlan\phase1_sprite_animation_checklist.md` to understand the specific Phase 1 implementation requirements.

3. **Reference Current Code**: Examine the existing `viewer.py` script to understand the current functionality, but DO NOT use it as the starting point. Use it only as reference for understanding:
   - Current sprite sheet loading and frame selection logic
   - Existing trim analysis and pivot detection system
   - Current export format (JSON/Python generation)
   - UI patterns and user interaction flows

**Your Task**: Create a completely new codebase for the sprite animation tool in the `.\AnimationViewer\` directory. Start with Phase 1, Section 1.1 Architecture Refactoring:

**Immediate Implementation Steps:**
1. **Remove hardcoded dependencies** - Create dynamic sprite sheet loading system
2. **Create proper class architecture** - Design SpriteSheet, SpriteSheetManager, and main application classes
3. **Implement multi-spritesheet data structures** - Build foundation for loading multiple sprite sheets

**File Structure to Create:**
.\AnimationViewer
├── main.py                 # Application entry point
├── core
│   ├── init.py
│   ├── spritesheet.py     # SpriteSheet class
│   ├── animation.py       # Animation management
│   └── project.py         # Project management
├── ui
│   ├── init.py
│   └── main_window.py     # Main application window
└── utils
│   ├── init.py
│   └── file_manager.py    # File operations

**Key Requirements:**
- Use pygame for graphics (maintain compatibility with existing code)
- Preserve all current functionality (frame selection, trim analysis, export)
- Create clean, modular architecture ready for Phase 1's professional UI
- Follow the data structures defined in the project overview
- Implement proper error handling and validation

**Start with**: Section 1.1 tasks - focus on removing the hardcoded ASSET_PATH and creating the SpriteSheet and SpriteSheetManager classes as defined in the checklist.

Please begin implementation and let me know when you've completed the initial architecture refactoring.