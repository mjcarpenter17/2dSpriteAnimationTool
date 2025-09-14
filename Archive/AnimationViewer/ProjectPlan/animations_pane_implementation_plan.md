# Animations Pane - Detailed Implementation Plan for AI Agent

## Implementation Objective

Transform the current single-spritesheet viewer into a multi-project animation management system with a dedicated animations pane that supports folder-based organization, automatic animation discovery, and cross-spritesheet workflow via tabbed interface.

## Technical Architecture Overview

### Core Components Required
1. **AnimationFolder** - Manages folder paths and animation discovery
2. **AnimationEntry** - Represents individual animation metadata
3. **AnimationsPane** - UI panel containing folder/animation management
4. **TabManager** - Handles multiple spritesheet tabs
5. **AnimationFileWatcher** - Auto-discovery of new animations

### Data Structures

```python
class AnimationEntry:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.name = str  # Filename without extension
        self.spritesheet_path = str  # Associated spritesheet
        self.frame_count = int
        self.creation_date = datetime
        self.metadata = dict  # Loaded from JSON file
        self.thumbnail = pygame.Surface  # Optional first frame preview

class AnimationFolder:
    def __init__(self, path: str, name: str = None):
        self.path = path
        self.name = name or os.path.basename(path)
        self.animations = List[AnimationEntry]
        self.is_expanded = bool  # UI state for collapsible folders
        self.color_band = tuple  # RGB color for folder header
        self.last_scan = datetime  # For change detection

class TabManager:
    def __init__(self):
        self.active_tab = int  # Index of current tab
        self.tabs = List[SpritesheetTab]
        self.max_tabs = 8  # Reasonable limit
        
class SpritesheetTab:
    def __init__(self, spritesheet_path: str, name: str):
        self.spritesheet_path = spritesheet_path
        self.name = name  # Display name for tab
        self.spritesheet = SpriteSheet  # Loaded spritesheet object
        self.current_animation = AnimationEntry  # Currently selected
```

## Step-by-Step Implementation Sequence

### Phase 1A: Foundation Architecture (Priority: CRITICAL)

#### Task 1.1: Create Animation Discovery System
```python
# File: animation_manager.py
class AnimationManager:
    def __init__(self):
        self.folders = List[AnimationFolder]
        self.animation_cache = Dict[str, AnimationEntry]  # filepath -> entry
        
    def add_folder(self, folder_path: str) -> AnimationFolder:
        """Add new folder to watch list and scan for animations"""
        # Validate folder exists and is readable
        # Create AnimationFolder instance
        # Scan for .json animation files
        # Return folder object for UI integration
        
    def scan_folder(self, folder: AnimationFolder) -> List[AnimationEntry]:
        """Scan folder for animation files and update folder.animations"""
        # Search for *.json files with animation structure
        # Validate each file has required animation fields
        # Extract metadata (frame count, spritesheet path, etc.)
        # Create AnimationEntry objects
        # Update folder.last_scan timestamp
        
    def remove_folder(self, folder_path: str) -> bool:
        """Remove folder from watch list"""
        
    def get_animation_by_path(self, filepath: str) -> AnimationEntry:
        """Cached retrieval of animation metadata"""
```

#### Task 1.2: Implement Animation File Validation
```python
def validate_animation_file(filepath: str) -> bool:
    """Validate JSON file contains valid animation structure"""
    required_fields = ["animation", "sheet", "frame_size", "frames"]
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return all(field in data for field in required_fields)
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def extract_animation_metadata(filepath: str) -> dict:
    """Extract key metadata without loading full animation"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return {
        'name': data.get('animation', 'Unnamed'),
        'spritesheet_path': data.get('sheet', ''),
        'frame_count': len(data.get('frames', [])),
        'frame_size': data.get('frame_size', [0, 0])
    }
```

### Phase 1B: UI Panel Structure (Priority: HIGH)

#### Task 1.3: Create Animations Pane Layout
```python
# File: ui/animations_pane.py
class AnimationsPane:
    def __init__(self, rect: pygame.Rect, animation_manager: AnimationManager):
        self.rect = rect
        self.animation_manager = animation_manager
        self.scroll_offset = 0
        self.selected_animation = None
        self.font = pygame.font.Font(None, 16)
        self.header_font = pygame.font.Font(None, 18)
        
        # UI Constants
        self.HEADER_HEIGHT = 32
        self.FOLDER_HEADER_HEIGHT = 24
        self.ANIMATION_ITEM_HEIGHT = 20
        self.INDENT_SIZE = 16
        self.ADD_FOLDER_BTN_HEIGHT = 28
        
        # Colors
        self.BACKGROUND_COLOR = (45, 45, 48)
        self.FOLDER_COLORS = [(70, 130, 180), (60, 179, 113), (255, 140, 0), 
                             (147, 112, 219), (220, 20, 60)]  # Rotating folder colors
        
    def render(self, surface: pygame.Surface):
        """Main render function for animations pane"""
        # Clear background
        # Render header with "Animations" title and "+ Add Folder" button
        # Render folder sections with color bands
        # Render animation entries with indentation
        # Handle scrolling if content exceeds pane height
        
    def handle_click(self, pos: tuple) -> str:
        """Handle mouse clicks and return action type"""
        # Check if click is on "+ Add Folder" button -> return "add_folder"
        # Check if click is on folder header -> return "toggle_folder:path"
        # Check if click is on animation entry -> return "select_animation:filepath"
        # Return "none" if no interactive element clicked
```

#### Task 1.4: Implement Folder Display with Color Bands
```python
def render_folder_header(self, surface: pygame.Surface, folder: AnimationFolder, y_pos: int):
    """Render folder header with colored band and expand/collapse icon"""
    # Draw colored background band
    band_rect = pygame.Rect(self.rect.x, y_pos, self.rect.width, self.FOLDER_HEADER_HEIGHT)
    pygame.draw.rect(surface, folder.color_band, band_rect)
    
    # Draw expand/collapse triangle
    triangle_center = (self.rect.x + 10, y_pos + self.FOLDER_HEADER_HEIGHT // 2)
    triangle_points = self.get_triangle_points(triangle_center, folder.is_expanded)
    pygame.draw.polygon(surface, (255, 255, 255), triangle_points)
    
    # Draw folder name
    text_surface = self.header_font.render(folder.name, True, (255, 255, 255))
    surface.blit(text_surface, (self.rect.x + 25, y_pos + 4))
    
    # Draw animation count
    count_text = f"({len(folder.animations)} animations)"
    count_surface = self.font.render(count_text, True, (200, 200, 200))
    surface.blit(count_surface, (self.rect.right - count_surface.get_width() - 5, y_pos + 6))
```

### Phase 1C: Tab Management System (Priority: HIGH)

#### Task 1.5: Implement Tab System
```python
# File: ui/tab_manager.py
class TabManager:
    def __init__(self, tab_bar_rect: pygame.Rect):
        self.tab_bar_rect = tab_bar_rect
        self.tabs = []
        self.active_tab_index = 0
        self.tab_width = 120
        self.tab_height = 30
        
    def add_tab(self, spritesheet_path: str) -> int:
        """Add new tab for spritesheet, return tab index"""
        # Check if spritesheet already has a tab open
        existing_tab = self.find_tab_by_spritesheet(spritesheet_path)
        if existing_tab >= 0:
            self.active_tab_index = existing_tab
            return existing_tab
            
        # Create new tab
        tab_name = os.path.splitext(os.path.basename(spritesheet_path))[0]
        new_tab = SpritesheetTab(spritesheet_path, tab_name)
        self.tabs.append(new_tab)
        self.active_tab_index = len(self.tabs) - 1
        return self.active_tab_index
        
    def close_tab(self, tab_index: int):
        """Close tab and adjust active index"""
        if 0 <= tab_index < len(self.tabs):
            self.tabs.pop(tab_index)
            if self.active_tab_index >= tab_index and self.active_tab_index > 0:
                self.active_tab_index -= 1
                
    def render_tabs(self, surface: pygame.Surface):
        """Render tab bar with clickable tabs"""
        for i, tab in enumerate(self.tabs):
            tab_rect = self.get_tab_rect(i)
            is_active = (i == self.active_tab_index)
            
            # Draw tab background
            color = (60, 60, 60) if is_active else (40, 40, 40)
            pygame.draw.rect(surface, color, tab_rect)
            
            # Draw tab border
            border_color = (100, 100, 100) if is_active else (70, 70, 70)
            pygame.draw.rect(surface, border_color, tab_rect, 1)
            
            # Draw tab text
            text_surface = self.font.render(tab.name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=tab_rect.center)
            surface.blit(text_surface, text_rect)
            
            # Draw close button (small X)
            close_rect = pygame.Rect(tab_rect.right - 16, tab_rect.y + 4, 12, 12)
            self.draw_close_button(surface, close_rect)
```

### Phase 1D: Animation Selection & Cross-Spritesheet Loading (Priority: MEDIUM)

#### Task 1.6: Implement Animation Selection Logic
```python
def handle_animation_selection(self, animation_entry: AnimationEntry):
    """Handle user clicking on animation entry"""
    # Check if animation's spritesheet matches current active tab
    current_tab = self.tab_manager.get_active_tab()
    
    if current_tab and current_tab.spritesheet_path == animation_entry.spritesheet_path:
        # Same spritesheet - just select the animation
        self.load_animation_in_current_tab(animation_entry)
    else:
        # Different spritesheet - create new tab
        new_tab_index = self.tab_manager.add_tab(animation_entry.spritesheet_path)
        self.load_spritesheet_in_tab(new_tab_index, animation_entry.spritesheet_path)
        self.load_animation_in_tab(new_tab_index, animation_entry)

def load_animation_in_tab(self, tab_index: int, animation_entry: AnimationEntry):
    """Load animation data and highlight frames in specified tab"""
    # Load animation JSON data
    # Extract frame indices/coordinates
    # Update tab's current_animation property
    # Refresh spritesheet view to highlight selected frames
```

### Phase 1E: File System Integration (Priority: MEDIUM)

#### Task 1.7: Implement Folder Browser Dialog
```python
def show_add_folder_dialog(self) -> str:
    """Show folder selection dialog using tkinter"""
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    folder_path = filedialog.askdirectory(
        title="Select Animation Folder",
        initialdir=os.getcwd()
    )
    
    root.destroy()
    return folder_path

def auto_discover_on_save(self, animation_filepath: str):
    """When user saves new animation, auto-add its folder to animations pane"""
    folder_path = os.path.dirname(animation_filepath)
    
    # Check if folder is already being watched
    if not self.animation_manager.has_folder(folder_path):
        self.animation_manager.add_folder(folder_path)
        # Trigger UI refresh to show new folder and animation
```

### Phase 1F: UI Polish & Interactions (Priority: LOW)

#### Task 1.8: Add Visual Enhancements
```python
def render_animation_entry(self, surface: pygame.Surface, animation: AnimationEntry, 
                          y_pos: int, is_selected: bool):
    """Render individual animation entry with metadata"""
    # Background highlight for selection
    if is_selected:
        highlight_rect = pygame.Rect(self.rect.x, y_pos, self.rect.width, self.ANIMATION_ITEM_HEIGHT)
        pygame.draw.rect(surface, (70, 70, 120), highlight_rect)
    
    # Animation name
    name_surface = self.font.render(animation.name, True, (255, 255, 255))
    surface.blit(name_surface, (self.rect.x + self.INDENT_SIZE, y_pos + 2))
    
    # Frame count badge
    frame_text = f"{animation.frame_count}f"
    frame_surface = self.font.render(frame_text, True, (180, 180, 180))
    badge_x = self.rect.right - frame_surface.get_width() - 5
    surface.blit(frame_surface, (badge_x, y_pos + 2))
    
    # Optional: Different spritesheet indicator
    current_tab = self.tab_manager.get_active_tab()
    if current_tab and animation.spritesheet_path != current_tab.spritesheet_path:
        # Draw small colored dot to indicate different spritesheet
        dot_center = (self.rect.x + 8, y_pos + self.ANIMATION_ITEM_HEIGHT // 2)
        pygame.draw.circle(surface, (255, 165, 0), dot_center, 3)
```

## Integration Points with Existing System

### Required Modifications to Main Application

#### Task 1.9: Update Main Application Structure
```python
# File: main.py (or existing viewer.py)
class SpriteAnimationTool:
    def __init__(self):
        # Existing initialization
        self.animation_manager = AnimationManager()
        self.animations_pane = AnimationsPane(animations_rect, self.animation_manager)
        self.tab_manager = TabManager(tab_bar_rect)
        
    def handle_events(self, event):
        # Route events to appropriate components
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if click is in animations pane
            if self.animations_pane.rect.collidepoint(event.pos):
                action = self.animations_pane.handle_click(event.pos)
                self.process_animations_pane_action(action)
            
            # Check if click is on tab bar
            elif self.tab_manager.tab_bar_rect.collidepoint(event.pos):
                tab_action = self.tab_manager.handle_click(event.pos)
                self.process_tab_action(tab_action)
```

## Testing Criteria

### Unit Tests Required
1. **AnimationManager.scan_folder()** - Verify correct JSON file discovery
2. **validate_animation_file()** - Test with valid/invalid animation files  
3. **TabManager.add_tab()** - Verify duplicate prevention and proper indexing
4. **AnimationsPane.handle_click()** - Test click detection accuracy

### Integration Tests
1. **Cross-spritesheet loading** - Select animation from different spritesheet, verify new tab creation
2. **Folder management** - Add folder, verify animations appear in pane
3. **Auto-discovery** - Save new animation, verify automatic folder addition

### User Experience Tests
1. **Performance** - Test with 50+ animations across multiple folders
2. **UI responsiveness** - Verify smooth scrolling and click feedback
3. **Error handling** - Test with corrupted animation files and missing spritesheets

## Implementation Notes for AI Agent

- **File Structure**: Create new files as indicated rather than modifying existing viewer.py initially
- **Error Handling**: Always include try/catch blocks for file operations and JSON parsing
- **Performance**: Use lazy loading for animation metadata and spritesheet textures
- **UI Consistency**: Match existing color scheme and font choices from current viewer
- **Code Organization**: Keep UI rendering separate from data management logic

## Success Criteria

✅ User can add multiple animation folders via "+ Add Folder" button  
✅ Animation list displays all animations grouped by folder with color-coded headers  
✅ Clicking animation from different spritesheet opens new tab automatically  
✅ Tab system allows switching between multiple spritesheets  
✅ Animations pane shows frame count and spritesheet source for each animation  
✅ Auto-discovery adds folders when user saves new animations  
✅ UI maintains 60fps performance with large animation libraries