"""
Main window for the sprite animation tool with professional UI framework.
This implements the Phase 1.2 Professional UI Framework with panels, menus, and toolbars.
"""
import os
import sys
import json
import time
from typing import List, Tuple, Set, Optional, Dict, Any
import pygame

# Add the parent directory to sys.path to import from core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import AnimationProject
from core.spritesheet import SpriteSheet
from core.frame_analyzer import FrameAnalyzer, FrameAnalysisResult
from utils.file_manager import FileManager

# UI components
from ui.menu_system import MenuBar, Menu, MenuItem
from ui.status_bar import StatusBar

# Additional UI components used later
from ui.tab_manager import TabManager
from ui.panels.sprite_browser import SpriteSheetBrowserPanel
from ui.animations_pane import AnimationsPane
from ui.analysis_overlay import AnalysisOverlay
from ui.preferences import PreferencesManager, show_preferences_dialog
from ui.file_operations import EnhancedFileOperations, ExportProgressDialog
from animation_manager import AnimationManager
from animation_sources import AsepriteAnimationSource


class SpriteAnimationTool:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Sprite Animation Tool")

        # Window and UI metrics
        self.window_size: Tuple[int, int] = (1280, 800)
        self.menu_height = 24
        self.toolbar_height = 0  # toolbar disabled by default per recent changes
        self.status_height = 22
        self.left_panel_width = 320
        self.right_panel_width = 360
        self.splitter_width = 4
        self.disable_toolbar = True

        # Core
        self.clock = pygame.time.Clock()
        self.project = AnimationProject()
        self.file_manager = FileManager()
        self.file_ops = EnhancedFileOperations()

        # Initialize preferences
        self.preferences = PreferencesManager()
        
        # Initialize frame analyzer and analysis overlay
        self.frame_analyzer = FrameAnalyzer()
        self.analysis_overlay = AnalysisOverlay()
        self.current_frame_analysis = None

        # UI flags and state
        self.show_grid = True
        self.analyze_mode = False
        self.scale = 1.0
        self.header_height = 50
        self.show_help = False

        # Splitter state
        self.left_splitter_rect = pygame.Rect(0, 0, 4, 100)
        self.right_splitter_rect = pygame.Rect(0, 0, 4, 100)
        self.left_splitter_hover = False
        self.right_splitter_hover = False
        self.drag_left_splitter = False
        self.drag_right_splitter = False
        self.min_left_width = 200
        self.min_right_width = 250
        self.min_center_width = 400

        # UI scaffolding
        self.menu_bar = MenuBar()
        self.status_bar = StatusBar()
        self.toolbar = None

        # Panels and managers
        self.sprite_browser_panel = None
        self.animation_manager_panel = None
        self.left_splitter = None
        self.right_splitter = None
        self.multi_spritesheet_manager = AnimationManager()
        self.animations_pane = None
        self.tab_manager: Optional[TabManager] = None
        self.use_new_animations_pane = True
        self._aseprite_sources: List[Any] = []

        # Current sprite sheet state
        self.active_sheet: Optional[SpriteSheet] = None
        self.active_sheet_id: Optional[str] = None

        # Selection state
        self.selected_order: List[Tuple[int, int]] = []
        self.selected_set: Set[Tuple[int, int]] = set()
        self.cursor_row, self.cursor_col = 0, 0

        # Viewport & scroll
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        self.dragging_v = False
        self.dragging_h = False
        self.drag_off_x = 0
        self.drag_off_y = 0

        # Save dialog state
        self.save_mode = False
        self.save_prompts = [("Animation name", "walk"), ("Folder", "src/animations/player")]
        self.save_index = 0
        self.save_inputs: List[str] = ["", ""]
        self.current_text = ""

        # Auto-exit for testing
        self.auto_exit = self._get_auto_exit_time()
        self.elapsed_time = 0.0

        # Initial UI setup
        self._setup_menus()
        if not self.disable_toolbar:
            self._setup_toolbar()
        self._setup_panels()

        # Try default sheet
        self._load_default_sprite_sheet()

        # Finalize state
        self._update_ui_state()
    
    def _apply_preferences_to_layout(self):
        """Apply preferences to initial layout configuration."""
        # This method can be expanded to apply more preferences
        pass
    
    def _setup_menus(self):
        """Set up the professional menu system."""
        
        # File Menu
        file_menu = Menu([
            MenuItem("New Project", self._menu_new_project, "Ctrl+N"),
            MenuItem("", separator=True),
            MenuItem("Open Sprite Sheet...", self._menu_open_sprite_sheet, "Ctrl+O"),
            MenuItem("Import Aseprite JSON...", self._menu_import_aseprite_json),
            MenuItem("Reimport Aseprite JSON(s)", self._menu_reimport_aseprite_jsons),
            MenuItem("Recent Sprite Sheets", submenu=self._create_recent_menu()),
            MenuItem("", separator=True),
            MenuItem("Save Animation", self._menu_save_animation, "Ctrl+S"),
            MenuItem("Save Animation As...", self._menu_save_animation_as, "Ctrl+Shift+S"),
            MenuItem("", separator=True),
            MenuItem("Exit", self._menu_exit, "Ctrl+Q")
        ])
        
        # Edit Menu
        edit_menu = Menu([
            MenuItem("Select All Frames", self._menu_select_all, "Ctrl+A"),
            MenuItem("Clear Selection", self._menu_clear_selection, "Ctrl+D"),
            MenuItem("Invert Selection", self._menu_invert_selection),
            MenuItem("Select Row", self._menu_select_row, "R"),
            MenuItem("", separator=True),
            MenuItem("Preferences...", self._menu_preferences, "Ctrl+,")
        ])
        
        # View Menu
        view_menu = Menu([
            MenuItem("Toggle Grid", self._menu_toggle_grid, "G"),
            MenuItem("Toggle Analysis Mode", self._menu_toggle_analysis, "T"),
            MenuItem("", separator=True),
            MenuItem("Zoom In", self._menu_zoom_in, "Ctrl++"),
            MenuItem("Zoom Out", self._menu_zoom_out, "Ctrl+-"),
            MenuItem("Fit to Window", self._menu_fit_window),
            MenuItem("Actual Size", self._menu_actual_size),
            MenuItem("", separator=True),
            MenuItem("Show Animation Panel", self._menu_toggle_animation_panel),
            MenuItem("Show Properties Panel", self._menu_toggle_properties_panel),
            MenuItem("Reset Panel Layout", self._menu_reset_panels)
        ])
        
        # Animation Menu
        animation_menu = Menu([
            MenuItem("Create New Animation", self._menu_create_animation),
            MenuItem("Duplicate Animation", self._menu_duplicate_animation),
            MenuItem("Delete Animation", self._menu_delete_animation),
            MenuItem("", separator=True),
            MenuItem("Refresh Animation List", self._menu_refresh_animations, "F5")
        ])
        
        # Help Menu
        help_menu = Menu([
            MenuItem("Keyboard Shortcuts", self._menu_shortcuts, "F1"),
            MenuItem("Quick Start Guide", self._menu_quick_start),
            MenuItem("Export Format Documentation", self._menu_export_docs),
            MenuItem("", separator=True),
            MenuItem("About", self._menu_about)
        ])
        
        # Add menus to menu bar
        self.menu_bar.add_menu("File", file_menu)
        self.menu_bar.add_menu("Edit", edit_menu)
        self.menu_bar.add_menu("View", view_menu)
        self.menu_bar.add_menu("Animation", animation_menu)
        self.menu_bar.add_menu("Help", help_menu)
    
    def _setup_toolbar(self):
        """Set up the toolbar with icon-based buttons."""
        # File operations section
        self.toolbar.add_button(
            'open', 'Open Sprite Sheet', 
            self._menu_open_sprite_sheet, 'Ctrl+O'
        )
        self.toolbar.add_button(
            'save', 'Save Animation', 
            self._menu_save_animation, 'Ctrl+S'
        )
        self.toolbar.add_button(
            'recent', 'Recent Files', 
            self._toolbar_recent_files
        )
        
        self.toolbar.add_separator()
        
        # Selection tools section
        self.toolbar.add_button(
            'select_all', 'Select All Frames', 
            self._menu_select_all, 'Ctrl+A'
        )
        self.toolbar.add_button(
            'clear', 'Clear Selection', 
            self._menu_clear_selection, 'Ctrl+D'
        )
        self.toolbar.add_button(
            'grid', 'Toggle Grid', 
            self._menu_toggle_grid, 'G', toggle=True
        )
        self.toolbar.add_button(
            'analysis', 'Toggle Analysis Mode', 
            self._menu_toggle_analysis, 'T', toggle=True
        )
        
        self.toolbar.add_separator()
        
        # View/Zoom tools section
        self.toolbar.add_button(
            'zoom_in', 'Zoom In', 
            self._menu_zoom_in, 'Ctrl++'
        )
        self.toolbar.add_button(
            'zoom_out', 'Zoom Out', 
            self._menu_zoom_out, 'Ctrl+-'
        )
        
        self.toolbar.add_separator()
        
        # Animation operations section
        self.toolbar.add_button(
            'new_animation', 'Create New Animation', 
            self._menu_create_animation
        )
        self.toolbar.add_button(
            'refresh', 'Refresh Animation List', 
            self._menu_refresh_animations, 'F5'
        )
        self.toolbar.add_button(
            'import_ase', 'Import Aseprite JSON',
            self._menu_import_aseprite_json
        )
        self.toolbar.add_button(
            'reimport_ase', 'Reimport Aseprite JSON(s)',
            self._menu_reimport_aseprite_jsons
        )
        
        # Set initial button states
        self.toolbar.set_button_state('grid', active=self.show_grid)
        self.toolbar.set_button_state('analysis', active=self.analyze_mode)
    
    def _create_recent_menu(self) -> Menu:
        """Create the recent files submenu."""
        recent_files = self.preferences.get_recent_files()
        if not recent_files:
            return Menu([MenuItem("No recent files", enabled=False)])
        
        menu_items = []
        for file_path in recent_files[:10]:  # Limit to 10 recent files
            filename = os.path.basename(file_path)
            menu_items.append(MenuItem(filename, lambda fp=file_path: self._load_recent_file(fp)))
        
        if menu_items:
            menu_items.append(MenuItem("", separator=True))
            menu_items.append(MenuItem("Clear Recent Files", self._clear_recent_files))
        
        return Menu(menu_items)
    
    def _toolbar_recent_files(self):
        """Show recent files dropdown for toolbar button."""
        recent_files = self.preferences.get_recent_files()
        if recent_files:
            # For now, load the most recent file
            self._load_recent_file(recent_files[0])
        else:
            # Fall back to open dialog
            self._menu_open_sprite_sheet()
    
    def _load_recent_file(self, file_path: str):
        """Load a recent sprite sheet file."""
        if os.path.exists(file_path):
            self._load_sprite_sheet_file(file_path)
        else:
            # File no longer exists, remove from recent files
            recent_files = self.preferences.get_recent_files()
            if file_path in recent_files:
                recent_files.remove(file_path)
                self.preferences.set("file_management", "recent_sprite_sheets", recent_files)
                self.preferences.save_preferences()
            self.status_bar.show_error(f"File not found: {os.path.basename(file_path)}")
    
    def _clear_recent_files(self):
        """Clear the recent files list."""
        self.preferences.set("file_management", "recent_sprite_sheets", [])
        self.preferences.save_preferences()
        self.status_bar.show_info("Recent files list cleared")
    
    def _handle_animations_pane_action(self, action: str):
        """Handle actions from the new animations pane."""
        if action == "add_folder":
            # Process in animations pane
            result = self.animations_pane.process_action(action)
            if result:
                self.status_bar.show_info("Animation folder added successfully")
        
        elif action.startswith("toggle_folder:"):
            # Process in animations pane
            self.animations_pane.process_action(action)
        
        elif action.startswith("select_animation:"):
            # Process animation selection and handle cross-spritesheet loading
            animation_filepath = action[17:]  # Remove "select_animation:" prefix
            animation = self.multi_spritesheet_manager.get_animation_by_path(animation_filepath)
            
            if animation and animation.spritesheet_path:
                # Enhanced spritesheet path resolution with multiple fallback strategies
                animation_spritesheet_abs = self._resolve_spritesheet_path(
                    animation.spritesheet_path, 
                    animation_filepath
                )
                
                print(f"Resolved spritesheet path: {animation_spritesheet_abs}")
                print(f"File exists: {os.path.exists(animation_spritesheet_abs) if animation_spritesheet_abs else False}")
                
                if not animation_spritesheet_abs or not os.path.exists(animation_spritesheet_abs):
                    self.status_bar.show_error(f"Spritesheet not found: {animation.spritesheet_path}")
                    return
                
                # Check if we need to switch or create a new tab
                current_tab = self.tab_manager.get_active_tab()
                
                need_new_tab = True
                if current_tab and hasattr(current_tab, 'spritesheet_path'):
                    if os.path.abspath(current_tab.spritesheet_path) == animation_spritesheet_abs:
                        need_new_tab = False
                
                if need_new_tab:
                    # Need to create new tab or switch to existing tab
                    tab_index = self.tab_manager.add_tab(animation_spritesheet_abs)
                    if tab_index >= 0:
                        # Load the spritesheet in the new tab
                        self._load_spritesheet_in_tab(tab_index, animation_spritesheet_abs)
                
                # Select the animation
                self.animations_pane.process_action(action)
                self._load_animation_frames(animation)
                
                # Set active animation indicator
                if self.animations_pane:
                    self.animations_pane.set_active_animation(animation_filepath)
                
                self.status_bar.show_info(f"Selected animation: {animation.name}")
        else:
                self.status_bar.show_info("Animation has no associated spritesheet")
        
        elif action.startswith("select_external:"):
            descriptor_id = action[len("select_external:"):]

            # Resolve descriptor in sources
            descriptor = None
            source_for_desc = None
            for src in getattr(self, '_aseprite_sources', []):
                try:
                    for d in src.list_descriptors():
                        if d.id == descriptor_id:
                            descriptor = d
                            source_for_desc = src
                            break
                except Exception:
                    continue
                if descriptor:
                    break
            if not descriptor or not source_for_desc:
                self.status_bar.show_error("Aseprite descriptor not found")
                return
            
            # Determine spritesheet path from doc.meta.image
            doc = getattr(source_for_desc, '_doc', None)
            sheet_path = None
            if doc and getattr(doc, 'meta', None):
                image_rel = getattr(doc.meta, 'image', None)
                if image_rel:
                    base_dir = os.path.dirname(source_for_desc.origin_path)
                    candidate = os.path.abspath(os.path.join(base_dir, image_rel))
                    if os.path.exists(candidate):
                        sheet_path = candidate
            
            # Load spritesheet tab if needed
            if sheet_path:
                current_tab = self.tab_manager.get_active_tab() if self.tab_manager else None
                need_load = True
                if current_tab and hasattr(current_tab, 'spritesheet_path'):
                    if os.path.abspath(current_tab.spritesheet_path) == os.path.abspath(sheet_path):
                        need_load = False
                if need_load and self.tab_manager:
                    tab_index = self.tab_manager.add_tab(sheet_path)
                    if tab_index >= 0:
                        self._load_spritesheet_in_tab(tab_index, sheet_path)
            
            # Map frames using actual pixel coordinates from Aseprite
            frames = source_for_desc.get_frames(descriptor.id)
            if not frames:
                self.status_bar.show_info("No frames in Aseprite animation")
                return
            if not self.active_sheet:
                self.status_bar.show_info("Spritesheet not active yet")
                return
            
            self.selected_order.clear(); self.selected_set.clear()
            
            # Get the Aseprite document to access frame pixel coordinates
            doc = getattr(source_for_desc, '_doc', None)
            if not doc or not doc.frames:
                self.status_bar.show_error("No Aseprite frame data available")
                return
            
            # Convert Aseprite frame indices to grid positions using pixel coordinates
            for f in frames:
                idx = f.index
                if 0 <= idx < len(doc.frames):
                    aseprite_frame = doc.frames[idx]
                    x = aseprite_frame.atlas_rect[0]
                    y = aseprite_frame.atlas_rect[1]
                    row, col = self._pixel_to_grid_position(x, y)
                    if 0 <= row < self.active_sheet.rows and 0 <= col < self.active_sheet.cols:
                        pos = (row, col)
                        self.selected_order.append(pos)
                        self.selected_set.add(pos)
            if self.selected_order:
                self.cursor_row, self.cursor_col = self.selected_order[0]
            self.status_bar.show_success(f"Loaded Aseprite animation: {descriptor.name} ({len(self.selected_order)} frames)")
            if self.animations_pane:
                # Mark as active (reuse existing API with synthetic path id if desired)
                self.animations_pane.set_active_animation(descriptor.id)
            self._update_ui_state()
    
    def _load_animation_frames(self, animation_entry):
        """Load animation frames and highlight them in the main viewer."""
        try:
            # Load the animation JSON data
            with open(animation_entry.filepath, 'r', encoding='utf-8') as f:
                animation_data = json.load(f)
            
            # Clear current selection
            self.selected_order.clear()
            self.selected_set.clear()
            
            # Extract frame coordinates and convert to row/col positions
            frames = animation_data.get('frames', [])
            if not frames:
                self.status_bar.show_info("Animation has no frames")
                return
            
            # Convert frame coordinates to row/col based on current spritesheet
            if self.active_sheet:
                for frame_data in frames:
                    # Use row/col if available (newer format)
                    if 'row' in frame_data and 'col' in frame_data:
                        row, col = frame_data['row'], frame_data['col']
                    else:
                        # Calculate from x,y coordinates (older format)
                        frame_x = frame_data.get('x', 0)
                        frame_y = frame_data.get('y', 0)
                        
                        # Calculate row/col from coordinates
                        col = (frame_x - self.active_sheet.margin) // (self.active_sheet.tile_size[0] + self.active_sheet.spacing)
                        row = (frame_y - self.active_sheet.margin) // (self.active_sheet.tile_size[1] + self.active_sheet.spacing)
                    
                    # Validate row/col are within bounds
                    if 0 <= row < self.active_sheet.rows and 0 <= col < self.active_sheet.cols:
                        frame_pos = (row, col)
                        self.selected_order.append(frame_pos)
                        self.selected_set.add(frame_pos)
                
                # Update cursor to first frame
                if self.selected_order:
                    self.cursor_row, self.cursor_col = self.selected_order[0]
                
                print(f"Loaded {len(self.selected_order)} frames for animation '{animation_entry.name}'")
                
                # Update active animation indicator
                if self.animations_pane:
                    self.animations_pane.set_active_animation(animation_entry.filepath)
                
        else:
                self.status_bar.show_info("No spritesheet loaded to display animation frames")
                
        except Exception as e:
            print(f"Error loading animation frames: {e}")
            self.status_bar.show_info(f"Failed to load animation: {animation_entry.name}")
    
    def _handle_tab_manager_action(self, action: str):
        """Handle actions from the tab manager."""
        if action.startswith("switch_tab:"):
            result = self.tab_manager.process_action(action)
            if result:
                # Update active spritesheet based on tab
                active_tab = self.tab_manager.get_active_tab()
                if active_tab and active_tab.is_loaded:
                    self.active_sheet = active_tab.spritesheet
                    self._update_sprite_info_panel()
                    self.status_bar.show_info(f"Switched to: {active_tab.name}")
        
        elif action.startswith("close_tab:"):
            result = self.tab_manager.process_action(action)
            if result:
                # Update active spritesheet based on remaining tabs
                active_tab = self.tab_manager.get_active_tab()
                if active_tab and active_tab.is_loaded:
                    self.active_sheet = active_tab.spritesheet
                else:
                    self.active_sheet = None
                self._update_sprite_info_panel()
                self.status_bar.show_info("Tab closed")
    
    def _load_spritesheet_in_tab(self, tab_index: int, spritesheet_path: str):
        """Enhanced spritesheet loading with robust error handling and recovery."""
        try:
            if not os.path.exists(spritesheet_path):
                raise FileNotFoundError(f"Spritesheet file not found: {spritesheet_path}")
            
            # Extract parameters from animation metadata with comprehensive fallback
            tile_size, margin, spacing = self._extract_spritesheet_parameters(spritesheet_path)
            
            # Validate parameters
            if not tile_size or tile_size[0] <= 0 or tile_size[1] <= 0:
                print(f"Warning: Invalid tile size {tile_size}, using default (32, 32)")
                tile_size = (32, 32)
            
            if margin < 0:
                print(f"Warning: Invalid margin {margin}, using 0")
                margin = 0
                
            if spacing < 0:
                print(f"Warning: Invalid spacing {spacing}, using 0")
                spacing = 0
            
            print(f"Loading spritesheet with parameters: tile_size={tile_size}, margin={margin}, spacing={spacing}")
            
            # Attempt to load with project system
            try:
                sheet_id = self.project.sprite_manager.load_sprite_sheet(spritesheet_path, tile_size, margin, spacing)
                sprite_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                
                if not sprite_sheet:
                    raise RuntimeError("Project system failed to create sprite sheet")
                    
            except Exception as project_error:
                print(f"Project system loading failed: {project_error}")
                # Fallback to direct SpriteSheet creation
                try:
                    from sprite_sheet import SpriteSheet
                    sprite_sheet = SpriteSheet(spritesheet_path, tile_size, margin, spacing)
                    sheet_id = f"fallback_{len(self.tab_manager.tabs)}"
                    print("Used fallback SpriteSheet creation")
                except Exception as fallback_error:
                    raise RuntimeError(f"Both project system and fallback failed: {project_error}, {fallback_error}")
            
            # Verify sprite sheet is valid
            if not hasattr(sprite_sheet, 'rows') or not hasattr(sprite_sheet, 'cols'):
                raise RuntimeError("Invalid sprite sheet object created")
            
            if sprite_sheet.rows <= 0 or sprite_sheet.cols <= 0:
                raise RuntimeError(f"Invalid sprite sheet dimensions: {sprite_sheet.rows}x{sprite_sheet.cols}")
            
            # Store in tab
            self.tab_manager.set_tab_spritesheet(tab_index, sprite_sheet)
            
            # If this is the active tab, set as active sheet
            if tab_index == self.tab_manager.active_tab_index:
                self.active_sheet = sprite_sheet
                self.active_sheet_id = sheet_id
                if self.sprite_browser_panel:
                    self.sprite_browser_panel.set_active_spritesheet(sprite_sheet, {'name': os.path.basename(spritesheet_path)})
                self._update_sprite_info_panel()
                
            print(f"Successfully loaded spritesheet in tab {tab_index}: {os.path.basename(spritesheet_path)} ({sprite_sheet.rows}x{sprite_sheet.cols} tiles)")
            self.status_bar.show_success(f"Loaded spritesheet: {os.path.basename(spritesheet_path)}")
            
        except FileNotFoundError as e:
            error_msg = f"Spritesheet file not found: {os.path.basename(spritesheet_path)}"
            print(f"Error: {e}")
            self.status_bar.show_error(error_msg)
            
        except RuntimeError as e:
            error_msg = f"Failed to load spritesheet: {str(e)}"
            print(f"Error: {e}")
            self.status_bar.show_error(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error loading spritesheet: {str(e)}"
            print(f"Error: {e}")
            self.status_bar.show_error(error_msg)
            
        # If loading failed, remove the problematic tab
        if tab_index < len(self.tab_manager.tabs):
            tab = self.tab_manager.tabs[tab_index]
            if not hasattr(tab, 'sprite_sheet') or not tab.sprite_sheet:
                print(f"Removing failed tab: {tab.name}")
                self.tab_manager.remove_tab(tab_index)
    
    def _extract_spritesheet_parameters(self, spritesheet_path: str) -> tuple:
        """Extract spritesheet parameters from animations that use this spritesheet.
        
        Returns:
            tuple: (tile_size, margin, spacing)
        """
        tile_size = (90, 37)  # Default fallback
        margin = 0
        spacing = 0
        
        # Look through all animations to find one that uses this spritesheet
        for folder in self.multi_spritesheet_manager.folders:
            for animation in folder.animations:
                # Resolve animation's spritesheet path
                if animation.spritesheet_path:
                    animation_dir = os.path.dirname(animation.filepath)
                    animation_spritesheet_path = os.path.abspath(
                        os.path.join(animation_dir, animation.spritesheet_path)
                    )
                    
                    if animation_spritesheet_path == os.path.abspath(spritesheet_path):
                        # Found an animation that uses this spritesheet - extract parameters
                        if 'frame_size' in animation.metadata:
                            tile_size = tuple(animation.metadata['frame_size'])
                        if 'margin' in animation.metadata:
                            margin = animation.metadata['margin']
                        if 'spacing' in animation.metadata:
                            spacing = animation.metadata['spacing']
                        
                        print(f"Extracted parameters from animation {animation.name}: tile_size={tile_size}, margin={margin}, spacing={spacing}")
                        return tile_size, margin, spacing
        
        print(f"No matching animation found for {spritesheet_path}, using defaults: tile_size={tile_size}, margin={margin}, spacing={spacing}")
        return tile_size, margin, spacing
    
    def _clear_recent_files(self):
        """Clear the recent files list."""
        self.preferences.set("file_management", "recent_sprite_sheets", [])
        self.preferences.save_preferences()
        self.status_bar.show_info("Recent files list cleared")
    
    def _setup_panels(self):
        """Set up the panel layout system."""
        # Calculate panel positions
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        content_height = content_bottom - content_top
        
        # Left panel - Sprite Browser
        self.sprite_browser_panel = SpriteSheetBrowserPanel(
            0, content_top, 
            self.left_panel_width, content_height,
            self.project
        )
        
        # Left splitter
        # Legacy left_splitter object removed (using custom overlay rendering now)
        self.left_splitter = None
        
        # Right panel - Animation Manager (choose between old and new system)
        right_panel_x = self.window_size[0] - self.right_panel_width
        
        if self.use_new_animations_pane:
            # Phase 2 - New multi-spritesheet animations pane
            animations_pane_rect = pygame.Rect(
                right_panel_x, content_top,
                self.right_panel_width, content_height
            )
            self.animations_pane = AnimationsPane(animations_pane_rect, self.multi_spritesheet_manager)
            
            # Add default animation folder if it exists
            default_anim_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "animations", "player")
            if os.path.exists(default_anim_dir):
                self.multi_spritesheet_manager.add_folder(default_anim_dir, "Player Animations")
        else:
            # Phase 1 - Original animation manager panel
            self.animation_manager_panel = AnimationManagerPanel(
                right_panel_x, content_top,
                self.right_panel_width, content_height,
                self.project
            )
        
        # Phase 2 - Tab Manager for multi-spritesheet support
        tab_bar_height = 32
        tab_bar_rect = pygame.Rect(
            self.left_panel_width + self.splitter_width,
            content_top,
            self.window_size[0] - self.left_panel_width - self.right_panel_width - 2 * self.splitter_width,
            tab_bar_height
        )
        self.tab_manager = TabManager(tab_bar_rect)
        
        # Right splitter
        # Legacy right_splitter object removed (using custom overlay rendering now)
        self.right_splitter = None
        
        # Set up panel callbacks
        self.sprite_browser_panel.on_sheet_changed = self._on_sprite_sheet_changed
        self.sprite_browser_panel.on_load_requested = self._on_load_sprite_sheet_requested
        
        # Only set up animation manager panel callbacks if using old system
        if not self.use_new_animations_pane and self.animation_manager_panel:
            self.animation_manager_panel.on_animation_selected = self._on_animation_selected
            self.animation_manager_panel.on_create_animation = self._on_create_animation_requested
    
    def _update_ui_state(self):
        """Update UI state based on current application state."""
        # Update toolbar button states
        has_sheet = self.active_sheet is not None
        has_selection = len(self.selected_set) > 0
        
        # Enable/disable toolbar buttons based on state
        if self.toolbar:
            self.toolbar.set_button_state('save', enabled=has_selection)
            self.toolbar.set_button_state('select_all', enabled=has_sheet)
            self.toolbar.set_button_state('clear', enabled=has_selection)
            self.toolbar.set_button_state('new_animation', enabled=has_selection)
        
        # Update comprehensive status bar
        if self.active_sheet:
            # Get sprite sheet dimensions
            if hasattr(self.active_sheet, 'image'):
                dimensions = (self.active_sheet.image.get_width(), self.active_sheet.image.get_height())
        else:
                dimensions = None
                
            self.status_bar.set_sprite_sheet_info(
                self.active_sheet.name,
                self.active_sheet.get_tile_count(),
                dimensions
            )
            
            # Update selection info with percentage
            total_tiles = self.active_sheet.get_tile_count()
            self.status_bar.set_selection_info(len(self.selected_set), total_tiles)
        else:
            self.status_bar.set_sprite_sheet_info("No sprite sheet loaded", 0)
            self.status_bar.set_selection_info(len(self.selected_set))
        
        # Update mouse and frame information
        mouse_pos = pygame.mouse.get_pos()
        if has_sheet and self._is_mouse_in_grid(mouse_pos):
            frame_pos = self._get_frame_at_mouse(mouse_pos)
            if frame_pos:
                frame_index = frame_pos[0] * self.active_sheet.cols + frame_pos[1]
                self.status_bar.set_mouse_info(mouse_pos, frame_pos, frame_index)
        else:
                self.status_bar.set_mouse_info(mouse_pos)
        else:
            self.status_bar.set_mouse_info(mouse_pos)
        
        # Update operation status based on current mode
        if self.save_mode:
            self.status_bar.set_operation_status("Save Mode", f"Input {self.save_index + 1}/2")
        elif has_selection:
            if self.analyze_mode:
                self.status_bar.set_operation_status("Analysis Mode", "Showing trim data")
        else:
                self.status_bar.set_operation_status("Ready", "Frames selected")
        else:
            if has_sheet:
                self.status_bar.set_operation_status("Ready", "Select frames to animate")
        else:
                self.status_bar.set_operation_status("Ready", "Load a sprite sheet to begin")
                
        # Update frame analysis if in analysis mode
        if self.analyze_mode:
            self._update_current_frame_analysis()
    
    def _is_mouse_in_grid(self, mouse_pos: tuple) -> bool:
        """Check if mouse is within the sprite grid area."""
        grid_rect = self._get_main_content_rect()
        return grid_rect.collidepoint(mouse_pos)
    
    def _get_frame_at_mouse(self, mouse_pos: tuple) -> tuple:
        """Get the frame coordinates at the mouse position."""
        if not self.active_sheet:
            return None
            
        grid_rect = self._get_main_content_rect()
        if not grid_rect.collidepoint(mouse_pos):
            return None
            
        # Calculate frame position accounting for scroll
        rel_x = mouse_pos[0] - grid_rect.x + self.scroll_x
        rel_y = mouse_pos[1] - grid_rect.y + self.scroll_y
        
        # Calculate tile dimensions with scale
        tile_width, tile_height = self.active_sheet.tile_size
        scale = getattr(self, 'scale', 1.0)
        scaled_tile_width = tile_width * scale
        scaled_tile_height = tile_height * scale
        
        # Calculate grid position
        col = int(rel_x // scaled_tile_width)
        row = int(rel_y // scaled_tile_height)
        
        # Check if within bounds
        if 0 <= row < self.active_sheet.rows and 0 <= col < self.active_sheet.cols:
            return (row, col)
        return None
    
    def _get_main_content_rect(self) -> pygame.Rect:
        """Get the rectangle for the main content area (sprite grid)."""
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        
        # Account for side panels
        left_boundary = self.left_panel_width + self.splitter_width
        right_boundary = self.window_size[0] - self.right_panel_width - self.splitter_width
        
        return pygame.Rect(
            left_boundary, content_top,
            right_boundary - left_boundary, 
            content_bottom - content_top
        )
        
        tile_size = self.active_sheet.tile_size
        col = int(rel_x // tile_size[0])
        row = int(rel_y // tile_size[1])
        
        # Check bounds
        if 0 <= row < self.active_sheet.rows and 0 <= col < self.active_sheet.cols:
            return (row, col)
        
        return None
        
        # Update panel layouts based on splitter positions
        self._update_panel_layout()
    
    def _update_panel_layout(self):
        """Update panel layout based on splitter positions."""
        # Panels may vary depending on new animations pane usage; ensure left panel exists
        if not self.sprite_browser_panel:
            return
        
        # Clamp widths again for safety
        total_w = self.window_size[0]
        available_for_center = total_w - self.left_panel_width - self.right_panel_width - 2 * self.splitter_width
        if available_for_center < self.min_center_width:
            # Reduce whichever side was just dragged (heuristic)
            deficit = self.min_center_width - available_for_center
            if self.drag_left_splitter and self.left_panel_width - deficit >= self.min_left_width:
                self.left_panel_width -= deficit
            elif self.drag_right_splitter and self.right_panel_width - deficit >= self.min_right_width:
                self.right_panel_width -= deficit
        else:
                # Split deficit proportionally
                half = deficit / 2
                self.left_panel_width = max(self.min_left_width, self.left_panel_width - half)
                self.right_panel_width = max(self.min_right_width, self.right_panel_width - half)
        
        # Apply to panels
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        content_height = content_bottom - content_top
        self.sprite_browser_panel.width = int(self.left_panel_width)
        self.sprite_browser_panel.height = content_height
        self.sprite_browser_panel.x = 0
        self.sprite_browser_panel.y = content_top
        
        if self.use_new_animations_pane and self.animations_pane:
            # Right animations pane placement
            self.animations_pane.resize(self.right_panel_width, content_height)
            self.animations_pane.x = self.window_size[0] - self.right_panel_width
            self.animations_pane.y = content_top
        elif self.animation_manager_panel:
            self.animation_manager_panel.width = int(self.right_panel_width)
            self.animation_manager_panel.height = content_height
            self.animation_manager_panel.x = self.window_size[0] - self.right_panel_width
            self.animation_manager_panel.y = content_top

        # Update tab bar rect to span new center width
        if self.tab_manager:
            tab_height = 32
            center_left = self.left_panel_width + self.splitter_width
            center_right = self.window_size[0] - self.right_panel_width - self.splitter_width
            bar_rect = pygame.Rect(center_left, content_top, center_right - center_left, tab_height)
            self.tab_manager.set_bar_rect(bar_rect)
        
    def _get_auto_exit_time(self) -> Optional[float]:
        """Get auto-exit time from environment variable."""
        try:
            v = os.environ.get("AUTO_EXIT_SEC")
            return float(v) if v else None
        except Exception:
            return None
    
    # Menu action methods
    def _menu_new_project(self):
        """Create a new project."""
        self.status_bar.show_info("New project created")
        # Reset current state
        self.selected_order.clear()
        self.selected_set.clear()
        self.save_mode = False
    
    def _menu_open_sprite_sheet(self):
        """Open a sprite sheet file dialog with enhanced file operations."""
        self.status_bar.set_operation_status("Opening", "Selecting sprite sheet...")
        
        file_paths = self.file_ops.open_sprite_sheet_dialog(multiple=False)
        if file_paths:
            file_path = file_paths[0]
            
            # Validate the file before loading
            is_valid, message = self.file_ops.validate_sprite_sheet(file_path)
            if not is_valid:
                self.file_ops.show_error("Invalid Sprite Sheet", message)
                self.status_bar.show_error(f"Invalid file: {message}")
                return
            
            # Show warning for large files
            if message and "Warning" in message:
                if not self.file_ops.show_warning("Large File Warning", message + "\n\nContinue loading?"):
                    self.status_bar.clear_operation_status()
                    return
                self.status_bar.show_warning("Loading large file...")
            
            self.status_bar.set_operation_status("Loading", f"Loading {os.path.basename(file_path)}...")
            
            # Load the sprite sheet
            self._load_sprite_sheet_file(file_path)
            
            # Add to recent files
            self.preferences.add_recent_file(file_path)
            
            self.status_bar.show_success(f"Loaded sprite sheet: {os.path.basename(file_path)}")
        else:
            # User cancelled - just clear the operation status
            self.status_bar.clear_operation_status()

    def _menu_import_aseprite_json(self):
        """Import an Aseprite JSON file and register as animation source."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select Aseprite JSON",
                filetypes=[("Aseprite JSON", "*.json"), ("All Files", "*.*")]
            )
            root.destroy()
            if not file_path:
                self.status_bar.show_info("Aseprite import cancelled")
                return
            from aseprite_loader import AsepriteJSONLoader
            loader = AsepriteJSONLoader(file_path)
            doc = loader.load()
            loader.report_summary()
            if doc.errors:
                self.status_bar.show_error(f"Aseprite load: {len(doc.errors)} errors, {len(doc.animations)} animations")
        else:
                self.status_bar.show_success(f"Imported Aseprite JSON: {len(doc.animations)} animations, {len(doc.frames)} frames")
            
            # Update sprite sheet grid based on Aseprite frame data
            if self.active_sheet and doc.frames:
                self._update_sprite_sheet_from_aseprite(doc)
            
            # Register source and refresh pane
            try:
                source = AsepriteAnimationSource(doc, file_path)
                self._register_aseprite_source(source)
            except Exception as adapt_e:
                print(f"Aseprite adapter error: {adapt_e}")
        except Exception as e:
            print(f"Aseprite import error: {e}")
            self.status_bar.show_error("Failed to import Aseprite JSON")
    
    def _menu_reimport_aseprite_jsons(self):
        """Re-parse all currently registered Aseprite JSON sources (Phase 2.6)."""
        if not getattr(self, '_aseprite_sources', None):
            self.status_bar.show_info("No Aseprite sources to reimport")
            return
        total = len(self._aseprite_sources)
        refreshed = 0
        errors = 0
        new_sources = []
        for src in list(self._aseprite_sources):
            path = getattr(src, 'origin_path', None)
            if not path or not os.path.exists(path):
                errors += 1
                continue
            try:
                from aseprite_loader import AsepriteJSONLoader
                loader = AsepriteJSONLoader(path)
                doc = loader.load()
                if doc.errors:
                    errors += 1
                # Replace source even if errors, to reflect current state
                new_sources.append(AsepriteAnimationSource(doc, path))
                refreshed += 1
            except Exception as e:
                print(f"Reimport error for {path}: {e}")
                errors += 1
        # Swap sources list
        self._aseprite_sources = new_sources
        # Notify pane
        if self.animations_pane:
            try:
                self.animations_pane.set_external_sources(self._aseprite_sources)
            except Exception as pane_e:
                print(f"Pane refresh after reimport failed: {pane_e}")
        if errors == 0:
            self.status_bar.show_success(f"Reimported {refreshed}/{total} Aseprite sources")
        else:
            self.status_bar.show_warning(f"Reimported {refreshed}/{total} sources with {errors} issue(s)")
    
    def _register_aseprite_source(self, source):
        """Register a new Aseprite animation source and update the UI."""
        # Initialize the sources list if it doesn't exist
        if not hasattr(self, '_aseprite_sources'):
            self._aseprite_sources = []
        
        # Add the new source to the list
        self._aseprite_sources.append(source)
        
        # Update the animations pane to show the new source
        if self.animations_pane:
            try:
                self.animations_pane.set_external_sources(self._aseprite_sources)
                print(f"Registered Aseprite source with {len(source.list_animations())} animations")
            except Exception as pane_e:
                print(f"Failed to update animations pane: {pane_e}")
    
    def _update_sprite_sheet_from_aseprite(self, aseprite_doc):
        """Update the active sprite sheet's grid configuration based on Aseprite frame data."""
        if not self.active_sheet or not aseprite_doc.frames:
            return
        
        try:
            # Analyze frame positions to determine grid structure
            frames = aseprite_doc.frames
            
            # Get all unique frame positions and sizes
            positions = []
            frame_sizes = []
            
            for frame in frames:
                x = frame.atlas_rect[0]  # x position
                y = frame.atlas_rect[1]  # y position
                w = frame.atlas_rect[2]  # width
                h = frame.atlas_rect[3]  # height
                
                positions.append((x, y))
                frame_sizes.append((w, h))
            
            if not positions:
                return
            
            # Sort positions to analyze grid structure
            positions.sort()
            
            # Determine grid spacing and tile size
            # Find the most common frame size
            size_counts = {}
            for size in frame_sizes:
                size_counts[size] = size_counts.get(size, 0) + 1
            
            # Use the most common frame size as the tile size
            most_common_size = max(size_counts.keys(), key=lambda k: size_counts[k])
            
            # Calculate spacing by looking at position differences
            x_positions = sorted(set(pos[0] for pos in positions))
            y_positions = sorted(set(pos[1] for pos in positions))
            
            # Determine spacing (if positions are regular)
            spacing = 0
            if len(x_positions) > 1:
                # Check if spacing is consistent
                diffs = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
                if diffs:
                    spacing_x = min(diffs) - most_common_size[0]
                    spacing = max(0, spacing_x)
            
            # Determine margin (offset of first frame)
            margin = 0
            if positions:
                margin = min(pos[0] for pos in positions)
            
            # Update the sprite sheet configuration
            print(f"Updating sprite sheet grid: tile_size={most_common_size}, margin={margin}, spacing={spacing}")
            self.active_sheet.reconfigure_grid(most_common_size, margin, spacing)
            
            # Update UI to reflect the new grid
            self._update_ui_state()
            
            # Show updated grid info
            grid_info = f"{self.active_sheet.rows}x{self.active_sheet.cols}"
            tile_info = f"{most_common_size[0]}x{most_common_size[1]}"
            self.status_bar.show_info(f"Updated grid: {grid_info} tiles ({tile_info} each)")
            
        except Exception as e:
            print(f"Error updating sprite sheet grid from Aseprite: {e}")
            self.status_bar.show_warning("Could not update grid from Aseprite data")
    
    def _pixel_to_grid_position(self, x, y):
        """Convert pixel coordinates to grid row/column position."""
        if not self.active_sheet:
            return (0, 0)
        
        # Account for margin and tile size
        margin = self.active_sheet.margin
        spacing = self.active_sheet.spacing
        tile_w, tile_h = self.active_sheet.tile_size
        
        # Calculate grid position
        # Remove margin first
        adjusted_x = x - margin
        adjusted_y = y - margin
        
        # Calculate column and row accounting for spacing between tiles
        # Each tile occupies (tile_size + spacing), except no spacing after the last tile
        col = adjusted_x // (tile_w + spacing)
        row = adjusted_y // (tile_h + spacing)
        
        return (row, col)
    
    def _menu_save_animation(self):
        """Save current animation with enhanced dialog."""
        if not self.selected_order:
            self.status_bar.show_error("No frames selected for animation")
            return
        
        # Generate default name based on current sprite sheet
        default_name = "animation"
        if self.active_sheet:
            sheet_name = os.path.splitext(os.path.basename(self.active_sheet.filepath))[0]
            default_name = f"{sheet_name}_animation"
        
        # Get export location and name
        result = self.file_ops.save_animation_dialog(default_name)
        if not result:
            return
            
        file_path, animation_name = result
        
        # Check for overwrite
        if not self.file_ops.confirm_overwrite(file_path):
            return
        
        # Export the animation with progress dialog
        self._export_animation_with_progress(file_path, animation_name)
    
    def _menu_save_animation_as(self):
        """Save animation as - same as regular save with enhanced dialogs."""
        self._menu_save_animation()
    
    def _export_animation_with_progress(self, file_path: str, animation_name: str):
        """Export animation with progress dialog and enhanced feedback."""
        # Set initial status
        self.status_bar.set_operation_status("Exporting", f"Preparing to export '{animation_name}'...")
        
        # Create progress dialog
        progress = ExportProgressDialog("Exporting Animation")
        
        try:
            # Prepare animation data
            progress.update_status("Preparing animation data...", 10)
            self.status_bar.set_operation_status("Exporting", "Preparing animation data...")
            
            if not self.selected_order or not self.active_sheet:
                progress.close()
                self.file_ops.show_error("Export Error", "No animation data to export")
                self.status_bar.show_error("No animation data to export")
                return
            
            # Create animation object
            progress.update_status("Creating animation object...", 30)
            self.status_bar.set_operation_status("Exporting", "Creating animation structure...")
            
            animation_data = {
                'name': animation_name,
                'spritesheet': self.active_sheet.filepath,
                'tile_size': self.active_sheet.tile_size,
                'frames': []
            }
            
            # Process frames with analysis data
            progress.update_status("Processing frames...", 50)
            self.status_bar.set_operation_status("Exporting", f"Processing {len(self.selected_order)} frames...")
            
            # Collect frame analysis data
            frames_data = []
            trimmed_data = []
            offsets_data = []
            pivots_data = []
            
            for i, (row, col) in enumerate(self.selected_order):
                if progress.is_cancelled():
                    self.status_bar.show_warning("Export cancelled by user")
                    return
                
                # Basic frame data
                frame_data = {
                    'row': row,
                    'col': col,
                    'index': i
                }
                
                # Add frame analysis if available
                if hasattr(self.active_sheet, 'image'):
                    # Calculate frame rectangle
                    tile_width, tile_height = self.active_sheet.tile_size
                    margin = getattr(self.active_sheet, 'margin', 0)
                    spacing = getattr(self.active_sheet, 'spacing', 0)
                    
                    x = margin + col * (tile_width + spacing)
                    y = margin + row * (tile_height + spacing)
                    frame_rect = pygame.Rect(x, y, tile_width, tile_height)
                    
                    # Perform analysis
                    sheet_id = self.active_sheet_id or "export_sheet"
                    analysis_result = self.frame_analyzer.analyze_frame(
                        self.active_sheet.image, frame_rect, sheet_id, row, col
                    )
                    
                    if analysis_result:
                        # Original frame data
                        orig_rect = analysis_result.original_rect
                        frame_data.update({
                            'x': orig_rect.x,
                            'y': orig_rect.y,
                            'w': orig_rect.w,
                            'h': orig_rect.h
                        })
                        
                        # Trimmed frame data
                        trim_rect = analysis_result.trimmed_rect
                        trimmed_data.append({
                            'x': trim_rect.x,
                            'y': trim_rect.y,
                            'w': trim_rect.w,
                            'h': trim_rect.h
                        })
                        
                        # Offset data
                        offsets_data.append({
                            'x': analysis_result.offset[0],
                            'y': analysis_result.offset[1]
                        })
                        
                        # Pivot data
                        pivots_data.append({
                            'x': analysis_result.pivot_point[0],
                            'y': analysis_result.pivot_point[1]
                        })
                    else:
                        # Fallback data if analysis fails
                        frame_data.update({
                            'x': x, 'y': y, 'w': tile_width, 'h': tile_height
                        })
                        trimmed_data.append({'x': x, 'y': y, 'w': tile_width, 'h': tile_height})
                        offsets_data.append({'x': 0, 'y': 0})
                        pivots_data.append({'x': tile_width // 2, 'y': tile_height - 1})
                
                frames_data.append(frame_data)
                frame_progress = 50 + (30 * (i + 1) / len(self.selected_order))
                progress.update_status(f"Processing frame {i + 1}/{len(self.selected_order)}", frame_progress)
            
            # Update animation data with enhanced frame information
            animation_data['frames'] = frames_data
            animation_data['trimmed'] = trimmed_data
            animation_data['offsets'] = offsets_data
            animation_data['pivots'] = pivots_data
            animation_data['analysis'] = {
                'alpha_threshold': self.frame_analyzer.alpha_threshold,
                'export_timestamp': time.time(),
                'has_analysis': len(trimmed_data) > 0
            }
            
            # Export files
            progress.update_status("Writing JSON file...", 80)
            self.status_bar.set_operation_status("Exporting", "Writing animation files...")
            
            # Export JSON
            json_path = file_path
            with open(json_path, 'w') as f:
                json.dump(animation_data, f, indent=2)
            
            # Export Python file
            progress.update_status("Writing Python file...", 90)
            
            python_path = os.path.splitext(json_path)[0] + '.py'
            self._write_python_animation_file(python_path, animation_data)
            
            progress.update_status("Export complete!", 100)
            progress.close()
            
            # Show success message
            export_paths = [json_path, python_path]
            self.file_ops.show_export_success(animation_name, export_paths)
            
            # Update status bar with success
            self.status_bar.show_success(f"Animation '{animation_name}' exported successfully to {len(export_paths)} files")
            
            # Trigger auto-discovery for animation folders
            self._check_for_new_animation_folder(json_path)
            
        except Exception as e:
            progress.close()
            error_msg = f"Failed to export animation: {str(e)}"
            self.file_ops.show_error("Export Error", error_msg)
            self.status_bar.show_error(f"Export failed: {str(e)}")
    
    def _resolve_spritesheet_path(self, spritesheet_path: str, animation_filepath: str) -> str:
        """Enhanced spritesheet path resolution with comprehensive fallback strategies.
        
        Args:
            spritesheet_path: The spritesheet path from animation metadata
            animation_filepath: The path to the animation file
            
        Returns:
            Absolute path to spritesheet file, or None if not found
        """
        if not spritesheet_path:
            return None
        
        # If already absolute and exists, return it
        if os.path.isabs(spritesheet_path) and os.path.exists(spritesheet_path):
            return os.path.abspath(spritesheet_path)
        
        animation_dir = os.path.dirname(animation_filepath)
        
        # Strategy 1: Relative to animation directory
        candidate = os.path.abspath(os.path.join(animation_dir, spritesheet_path))
        if os.path.exists(candidate):
            print(f"Path resolution strategy 1 (animation dir): {candidate}")
            return candidate
        
        # Strategy 2: Relative to project root (go up directories until we find a common structure)
        current_dir = animation_dir
        for _ in range(5):  # Try up to 5 levels up
            current_dir = os.path.dirname(current_dir)
            if not current_dir or current_dir == os.path.dirname(current_dir):  # Hit root
                break
            
            candidate = os.path.abspath(os.path.join(current_dir, spritesheet_path))
            if os.path.exists(candidate):
                print(f"Path resolution strategy 2 (project root): {candidate}")
                return candidate
        
        # Strategy 3: Relative to AnimationViewer directory
        viewer_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.abspath(os.path.join(viewer_root, "..", spritesheet_path))
        if os.path.exists(candidate):
            print(f"Path resolution strategy 3 (viewer root): {candidate}")
            return candidate
        
        # Strategy 4: Search common asset directories
        asset_dirs = ["Assets", "Assests", "assets", "sprites", "images", "textures"]
        for asset_dir in asset_dirs:
            # Try from animation directory upwards
            current_dir = animation_dir
            for _ in range(3):  # Try up to 3 levels up
                candidate = os.path.abspath(os.path.join(current_dir, asset_dir, spritesheet_path))
                if os.path.exists(candidate):
                    print(f"Path resolution strategy 4 (asset dir {asset_dir}): {candidate}")
                    return candidate
                current_dir = os.path.dirname(current_dir)
                if not current_dir or current_dir == os.path.dirname(current_dir):
                    break
        
        # Strategy 5: Use filename only and search for it
        spritesheet_filename = os.path.basename(spritesheet_path)
        if spritesheet_filename != spritesheet_path:  # Only if path had directories
            # Search in common directories
            search_dirs = [animation_dir]
            
            # Add parent directories
            current_dir = animation_dir
            for _ in range(3):
                current_dir = os.path.dirname(current_dir)
                if current_dir and current_dir != os.path.dirname(current_dir):
                    search_dirs.append(current_dir)
                    # Add asset subdirectories
                    for asset_dir in asset_dirs:
                        asset_path = os.path.join(current_dir, asset_dir)
                        if os.path.exists(asset_path):
                            search_dirs.append(asset_path)
            
            for search_dir in search_dirs:
                candidate = os.path.join(search_dir, spritesheet_filename)
                if os.path.exists(candidate):
                    print(f"Path resolution strategy 5 (filename search): {candidate}")
                    return os.path.abspath(candidate)
        
        # Strategy 6: Case-insensitive search on Windows
        if os.name == 'nt':  # Windows
            # Try case-insensitive search in animation directory
            animation_dir_files = []
            try:
                animation_dir_files = os.listdir(animation_dir)
            except (OSError, FileNotFoundError):
                pass
            
            target_filename = os.path.basename(spritesheet_path).lower()
            for file in animation_dir_files:
                if file.lower() == target_filename:
                    candidate = os.path.join(animation_dir, file)
                    if os.path.exists(candidate):
                        print(f"Path resolution strategy 6 (case-insensitive): {candidate}")
                        return os.path.abspath(candidate)
        
        print(f"Path resolution failed: Could not find {spritesheet_path}")
        return None

    def _check_for_new_animation_folder(self, animation_file_path: str):
        """Check if the saved animation is in a new folder and auto-add it to animations pane."""
        try:
            animation_dir = os.path.dirname(animation_file_path)
            
            # Check if this folder is already being tracked
            if self.animation_manager.is_folder_tracked(animation_dir):
                # Folder already tracked, just refresh
                self.animation_manager.refresh_folder(animation_dir)
                self.animations_pane.update_display()
                print(f"Refreshed existing animation folder: {animation_dir}")
                return
            
            # Check if the folder contains valid animation files
            animation_files = []
            if os.path.exists(animation_dir):
                for file in os.listdir(animation_dir):
                    if file.endswith('.json'):
                        file_path = os.path.join(animation_dir, file)
                        if self.animation_manager.validate_animation_file(file_path):
                            animation_files.append(file)
            
            # If we found valid animations, add the folder
            if animation_files:
                folder_name = os.path.basename(animation_dir)
                success = self.animation_manager.add_folder(animation_dir, folder_name)
                
                if success:
                    self.animations_pane.update_display()
                    print(f"Auto-discovered and added animation folder: {folder_name} ({len(animation_files)} animations)")
                    
                    # Show status message
                    self.status_bar.set_operation_status("Discovery", f"Added animation folder '{folder_name}' with {len(animation_files)} animations")
                else:
                    print(f"Failed to add animation folder: {animation_dir}")
        else:
                print(f"No valid animations found in directory: {animation_dir}")
                
        except Exception as e:
            print(f"Error in auto-discovery: {e}")

    def _write_python_animation_file(self, file_path, animation_data):
        """Write enhanced Python animation file with analysis data."""
        with open(file_path, 'w') as f:
            f.write(f"# Animation: {animation_data['name']}\n")
            f.write(f"# Generated from: {animation_data['spritesheet']}\n")
            f.write(f"# Generated by Sprite Animation Tool v1.2 with Frame Analysis\n\n")
            
            # Basic animation data
            f.write(f"ANIMATION = '{animation_data['name']}'\n")
            f.write(f"SPRITESHEET = '{animation_data['spritesheet']}'\n")
            f.write(f"TILE_SIZE = {animation_data['tile_size']}\n\n")
            
            # Original frames array (for backwards compatibility)
            f.write("# Original frame rectangles (x, y, w, h)\n")
            f.write("FRAMES = [\n")
            for frame in animation_data['frames']:
                if 'x' in frame:
                    f.write(f"    ({frame['x']}, {frame['y']}, {frame['w']}, {frame['h']}),\n")
                else:
                    f.write(f"    # Frame {frame['index']}: row={frame['row']}, col={frame['col']}\n")
            f.write("]\n\n")
            
            # Enhanced data arrays (if analysis was performed)
            if 'trimmed' in animation_data and animation_data['trimmed']:
                f.write("# Trimmed frame rectangles (x, y, w, h) - optimized bounds\n")
                f.write("TRIMMED = [\n")
                for trim in animation_data['trimmed']:
                    f.write(f"    ({trim['x']}, {trim['y']}, {trim['w']}, {trim['h']}),\n")
                f.write("]\n\n")
                
                f.write("# Frame offsets (x, y) - offset of trimmed rect from original\n")
                f.write("OFFSETS = [\n")
                for offset in animation_data['offsets']:
                    f.write(f"    ({offset['x']}, {offset['y']}),\n")
                f.write("]\n\n")
                
                f.write("# Pivot points (x, y) - relative to trimmed frame\n")
                f.write("PIVOTS = [\n")
                for pivot in animation_data['pivots']:
                    f.write(f"    ({pivot['x']}, {pivot['y']}),\n")
                f.write("]\n\n")
            
            # Metadata
            f.write("# Animation metadata\n")
            f.write("METADATA = {\n")
            f.write(f"    'name': '{animation_data['name']}',\n")
            f.write(f"    'spritesheet': '{animation_data['spritesheet']}',\n")
            f.write(f"    'tile_size': {animation_data['tile_size']},\n")
            f.write(f"    'frame_count': {len(animation_data['frames'])},\n")
            if 'analysis' in animation_data:
                analysis = animation_data['analysis']
                f.write(f"    'has_analysis': {analysis.get('has_analysis', False)},\n")
                f.write(f"    'alpha_threshold': {analysis.get('alpha_threshold', 16)},\n")
            f.write("}\n\n")
            
            # Helper functions
            f.write("# Helper functions for working with animation data\n")
            f.write("def get_frame_rect(index):\n")
            f.write("    '''Get original frame rectangle by index'''\n")
            f.write("    return FRAMES[index] if index < len(FRAMES) else None\n\n")
            
            if 'trimmed' in animation_data and animation_data['trimmed']:
                f.write("def get_trimmed_rect(index):\n")
                f.write("    '''Get trimmed frame rectangle by index'''\n")
                f.write("    return TRIMMED[index] if index < len(TRIMMED) else None\n\n")
                
                f.write("def get_pivot_point(index):\n")
                f.write("    '''Get pivot point by index (relative to trimmed frame)'''\n")
                f.write("    return PIVOTS[index] if index < len(PIVOTS) else None\n\n")
                
                f.write("def get_absolute_pivot(index):\n")
                f.write("    '''Get absolute pivot point in sprite sheet coordinates'''\n")
                f.write("    if index >= len(TRIMMED) or index >= len(PIVOTS):\n")
                f.write("        return None\n")
                f.write("    trim_rect = TRIMMED[index]\n")
                f.write("    pivot = PIVOTS[index]\n")
                f.write("    return (trim_rect[0] + pivot[0], trim_rect[1] + pivot[1])\n")
    
    def _menu_exit(self):
        """Exit the application."""
        self._save_window_state()
        pygame.quit()
        sys.exit()
    
    def _save_window_state(self):
        """Save current window state to preferences."""
        if self.preferences.get("general", "remember_window_state", True):
            self.preferences.set("layout", "window_width", self.window_size[0])
            self.preferences.set("layout", "window_height", self.window_size[1])
            self.preferences.set("layout", "left_panel_width", self.left_panel_width)
            self.preferences.set("layout", "right_panel_width", self.right_panel_width)
            self.preferences.save_preferences()
    
    def _menu_select_all(self):
        """Select all frames."""
        if self.active_sheet and self.active_sheet.get_tile_count() > 0:
            self.selected_order.clear()
            self.selected_set.clear()
            rows, cols = self.active_sheet.rows, self.active_sheet.cols
            for row in range(rows):
                for col in range(cols):
                    self.selected_order.append((row, col))
                    self.selected_set.add((row, col))
            self._update_ui_state()
    
    def _menu_clear_selection(self):
        """Clear frame selection."""
        self.selected_order.clear()
        self.selected_set.clear()
        self._update_ui_state()
    
    def _menu_invert_selection(self):
        """Invert frame selection."""
        if self.active_sheet and self.active_sheet.get_tile_count() > 0:
            rows, cols = self.active_sheet.rows, self.active_sheet.cols
            new_order = []
            new_set = set()
            
            for row in range(rows):
                for col in range(cols):
                    if (row, col) not in self.selected_set:
                        new_order.append((row, col))
                        new_set.add((row, col))
            
            self.selected_order = new_order
            self.selected_set = new_set
            self._update_ui_state()
    
    def _menu_select_row(self):
        """Select current row."""
        if self.active_sheet and self.active_sheet.get_tile_count() > 0:
            rows, cols = self.active_sheet.rows, self.active_sheet.cols
            if 0 <= self.cursor_row < rows:
                # Clear previous selection
                self.selected_order.clear()
                self.selected_set.clear()
                
                # Select entire row
                for col in range(cols):
                    self.selected_order.append((self.cursor_row, col))
                    self.selected_set.add((self.cursor_row, col))
                self._update_ui_state()
    
    def _menu_preferences(self):
        """Open preferences dialog."""
        show_preferences_dialog(None, self.preferences)
        self.status_bar.show_info("Preferences updated")
    
    def _menu_toggle_grid(self):
        """Toggle grid display."""
        self.show_grid = not self.show_grid
        if self.toolbar:
            self.toolbar.set_button_state('grid', active=self.show_grid)
        status = "on" if self.show_grid else "off"
        self.status_bar.show_info(f"Grid {status}")
    
    def _menu_toggle_analysis(self):
        """Toggle analysis mode."""
        self.analyze_mode = not self.analyze_mode
        self.analysis_overlay.set_overlay_visibility(self.analyze_mode)
        
        # Update current frame analysis if needed
        if self.analyze_mode:
            self._update_current_frame_analysis()
        else:
            self.current_frame_analysis = None
            
        if self.toolbar:
            self.toolbar.set_button_state('analysis', active=self.analyze_mode)
        status = "on" if self.analyze_mode else "off"
        self.status_bar.show_info(f"Analysis mode {status}")
        
    def _update_current_frame_analysis(self):
        """Update analysis for the currently selected frame."""
        if not self.active_sheet or not hasattr(self.active_sheet, 'image'):
            self.current_frame_analysis = None
            return
            
        # Get current frame coordinates
        if self.active_sheet.rows > 0 and self.active_sheet.cols > 0:
            row = max(0, min(self.cursor_row, self.active_sheet.rows - 1))
            col = max(0, min(self.cursor_col, self.active_sheet.cols - 1))
            
            # Calculate frame rectangle
            tile_width, tile_height = self.active_sheet.tile_size
            margin = getattr(self.active_sheet, 'margin', 0)
            spacing = getattr(self.active_sheet, 'spacing', 0)
            
            x = margin + col * (tile_width + spacing)
            y = margin + row * (tile_height + spacing)
            frame_rect = pygame.Rect(x, y, tile_width, tile_height)
            
            # Perform analysis
            sheet_id = self.active_sheet_id or "current_sheet"
            self.current_frame_analysis = self.frame_analyzer.analyze_frame(
                self.active_sheet.image, frame_rect, sheet_id, row, col
            )
    
    def _menu_zoom_in(self):
        """Zoom in."""
        self.status_bar.show_info("Zoom functionality not yet implemented")
    
    def _menu_zoom_out(self):
        """Zoom out."""
        self.status_bar.show_info("Zoom functionality not yet implemented")
    
    def _menu_fit_window(self):
        """Fit to window."""
        self.status_bar.show_info("Fit to window not yet implemented")
    
    def _menu_actual_size(self):
        """Actual size."""
        self.status_bar.show_info("Actual size not yet implemented")
    
    def _menu_toggle_animation_panel(self):
        """Toggle animation panel visibility."""
        if self.animation_manager_panel:
            self.animation_manager_panel.visible = not self.animation_manager_panel.visible
            status = "shown" if self.animation_manager_panel.visible else "hidden"
            self.status_bar.show_info(f"Animation panel {status}")
    
    def _menu_toggle_properties_panel(self):
        """Toggle properties panel visibility."""
        self.status_bar.show_info("Properties panel not yet implemented")
    
    def _menu_reset_panels(self):
        """Reset panel layout to defaults."""
        self.left_panel_width = 250
        self.right_panel_width = 300
        self._setup_panels()
        self.status_bar.show_info("Panel layout reset")
    
    def _menu_create_animation(self):
        """Create new animation."""
        if not self.selected_order:
            self.status_bar.show_error("No frames selected for animation")
            return
        self.save_mode = True
        self.save_index = 0
        self.current_text = self.save_inputs[0]
    
    def _menu_duplicate_animation(self):
        """Duplicate animation."""
        # Prevent duplication of external read-only (Aseprite) animations (id prefix check later when integrated fully)
        if getattr(self, 'animations_pane', None) and getattr(self.animations_pane, 'selected_animation', None):
            # Legacy folder JSON selection; allowed
            pass
        else:
            # No legacy selection; future: could detect external descriptor; for now just notify
            self.status_bar.show_info("Duplicate not available for imported animations yet")
            return
        self.status_bar.show_info("Duplicate animation not yet implemented")
    
    def _menu_delete_animation(self):
        """Delete animation."""
        selected = self.animation_manager_panel.get_selected_animation() if self.animation_manager_panel else None
        if selected:
            self.animation_manager_panel._delete_animation(selected['name'])
        else:
            # If using new pane, prevent deletion of external sources
            if hasattr(self, 'animations_pane') and self.animations_pane and getattr(self.animations_pane, 'selected_animation', None) is None:
                self.status_bar.show_info("Cannot delete imported Aseprite animations (read-only)")
                return
            self.status_bar.show_error("No animation selected")
    
    def _menu_refresh_animations(self):
        """Refresh animation list."""
        if self.animation_manager_panel:
            self.animation_manager_panel.refresh_animations()
            self.status_bar.show_info("Animation list refreshed")
    
    def _menu_shortcuts(self):
        """Show keyboard shortcuts."""
        self.status_bar.show_info("Keyboard shortcuts dialog not yet implemented")
    
    def _menu_quick_start(self):
        """Show quick start guide."""
        self.status_bar.show_info("Quick start guide not yet implemented")
    
    def _menu_export_docs(self):
        """Show export format documentation."""
        self.status_bar.show_info("Export documentation not yet implemented")
    
    def _menu_about(self):
        """Show about dialog."""
        self.status_bar.show_info("Sprite Animation Tool v1.2 - Professional Edition")
    
    # Panel callback methods
    def _on_sprite_sheet_changed(self, sheet_id: str):
        """Handle sprite sheet change from panel."""
        self.active_sheet_id = sheet_id
        self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
        self._update_ui_state()
        if self.active_sheet:
            self.status_bar.show_success(f"Switched to {self.active_sheet.name}")
    
    def _on_load_sprite_sheet_requested(self):
        """Handle sprite sheet load request from panel."""
        self._menu_open_sprite_sheet()
    
    def _on_animation_selected(self, animation: Dict):
        """Handle animation selection from panel."""
        self.status_bar.show_info(f"Selected animation: {animation['name']}")
    
    def _on_create_animation_requested(self):
        """Handle create animation request from panel."""
        self._menu_create_animation()
    
    def _load_sprite_sheet_file(self, filepath: str):
        """Load a sprite sheet from file path with enhanced status feedback."""
        try:
            # Set initial loading status
            filename = os.path.basename(filepath)
            self.status_bar.set_operation_status("Loading", f"Analyzing {filename}...")
            
            # Get file size for progress indication
            file_size = os.path.getsize(filepath)
            size_mb = file_size / (1024 * 1024)
            
            if size_mb > 10:
                self.status_bar.set_operation_status("Loading", f"Loading large file ({size_mb:.1f}MB)...")
            
            # Auto-detect tile size or use default
            tile_size = (90, 37)  # Default from original
            
            self.status_bar.set_operation_status("Loading", "Processing sprite sheet...")
            
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                filepath, tile_size, 
                margin=0, spacing=0,
                name=os.path.splitext(os.path.basename(filepath))[0]
            )
            
            if sheet_id:
                self.status_bar.set_operation_status("Loading", "Updating interface...")
                
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                # Provide active sheet to the info panel
                if self.sprite_browser_panel:
                    self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, {'name': os.path.basename(filepath)})
                
                # Get sprite sheet info for status display
                tile_count = self.active_sheet.get_tile_count() if self.active_sheet else 0
                dimensions = f"{self.active_sheet.rows}x{self.active_sheet.cols}" if self.active_sheet else "Unknown"
                
                self._update_ui_state()
                
                # Show success with detailed info
                self.status_bar.show_success(f"Loaded {filename} ({dimensions} grid, {tile_count} tiles)")

                # Auto-detect sibling Aseprite JSON (always attempt)
                try:
                    base, _ = os.path.splitext(filepath)
                    primary_json = base + ".json"
                    attempted = set()
                    def try_load_json(json_path: str):
                        if not os.path.exists(json_path) or json_path in attempted:
                            return False
                        attempted.add(json_path)
                        from aseprite_loader import AsepriteJSONLoader
                        loader = AsepriteJSONLoader(json_path)
                        doc = loader.load()
                        if doc.animations and doc.frames:
                            # Update grid if needed
                            if self.active_sheet and doc.frames:
                                self._update_sprite_sheet_from_aseprite(doc)
                            try:
                                source = AsepriteAnimationSource(doc, json_path)
                                self._register_aseprite_source(source)
                                self.status_bar.show_success(f"Auto-loaded Aseprite JSON: {os.path.basename(json_path)} ({len(doc.animations)} animations)")
                                return True
                            except Exception as adapt_e:
                                print(f"Auto adapter error: {adapt_e}")
                        return False
                    loaded = try_load_json(primary_json)
                    if not loaded:
                        # Fallback scan directory for matching meta.image
                        sheet_filename = os.path.basename(filepath)
                        folder = os.path.dirname(filepath)
                        for name in os.listdir(folder):
                            if not name.lower().endswith('.json'):
                                continue
                            candidate_path = os.path.join(folder, name)
                            if candidate_path in attempted:
                                continue
                            try:
                                with open(candidate_path, 'r', encoding='utf-8') as jf:
                                    jdata = json.load(jf)
                                meta = jdata.get('meta', {})
                                image_ref = meta.get('image')
                                if image_ref and os.path.basename(image_ref) == sheet_filename:
                                    if try_load_json(candidate_path):
                                        break
                            except Exception as scan_e:
                                print(f"Auto-scan skip {candidate_path}: {scan_e}")
                except Exception as ase_e:
                    print(f"Aseprite auto-detect error: {ase_e}")
        else:
                self.status_bar.show_error(f"Failed to load sprite sheet: {filename}")
        except Exception as e:
            filename = os.path.basename(filepath)
            error_msg = f"Error loading {filename}: {str(e)}"
            print(f"Error: {e}")
            self.status_bar.show_error(error_msg)

    def get_center_panel_rect(self) -> pygame.Rect:
        """Get the rectangle for the center panel (frame grid area)."""
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        
        # Account for tab bar height at the top of center panel
        tab_bar_height = 32 if self.tab_manager else 0
        adjusted_content_top = content_top + tab_bar_height
        
        left_boundary = self.left_panel_width + self.splitter_width
        right_boundary = self.window_size[0] - self.right_panel_width - self.splitter_width
        
        return pygame.Rect(
            left_boundary, adjusted_content_top,
            right_boundary - left_boundary, content_bottom - adjusted_content_top
        )
    
    def _update_sprite_info_panel(self):
        """Update the sprite sheet info panel with current active sheet."""
        if self.sprite_browser_panel:
            active_tab = self.tab_manager.get_active_tab() if self.tab_manager else None
            tab_info = {
                'name': active_tab.name if active_tab else 'None'
            } if active_tab else None
            
            self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, tab_info)
        
    def _get_auto_exit_time(self):
        """Get auto-exit time from environment variable."""
        try:
            v = os.environ.get("AUTO_EXIT_SEC")
            return float(v) if v else None
        except Exception:
            return None
    
    def _load_default_sprite_sheet(self):
        """Load the default sprite sheet if it exists."""
        # Try to load the existing sprite sheet for backward compatibility
        default_path = os.path.join(os.getcwd(), "Assests", "Sword Master Sprite Sheet 90x37.png")
        if os.path.exists(default_path):
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                default_path, 
                (90, 37), 
                margin=0, 
                spacing=0,
                name="Sword Master"
            )
            if sheet_id:
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                print(f"Loaded default sprite sheet: {default_path}")
    
    def run(self):
        """Main application loop."""
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle auto-exit for testing
            if self.auto_exit is not None:
                self.elapsed_time += dt
                if self.elapsed_time >= self.auto_exit:
                    running = False
                    continue
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self._handle_event(event)
            
            # Update and render
            self._update()
            self._render()
            pygame.display.flip()
        
        # Cleanup
        self._save_window_state()
        self.file_manager.cleanup()
        self.file_ops.cleanup()
        pygame.quit()
    
    def _handle_event(self, event):
        """Handle pygame events with professional UI framework."""
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            self.window_size = (event.w, event.h)
            self._setup_panels()  # Recreate panels with new size
            return
        
        # Let menu bar handle events first
        if self.menu_bar.handle_event(event, self.window_size[0]):
            return
        
        # Let toolbar handle events
        if self.toolbar and self.toolbar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let panels handle events
        if self.sprite_browser_panel and self.sprite_browser_panel.handle_event(event):
            return
            
        # Handle new animations pane vs old animation manager panel
        if self.use_new_animations_pane:
            # Phase 2 - New animations pane
            if self.animations_pane:
                if event.type == pygame.MOUSEMOTION:
                    self.animations_pane.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        action = self.animations_pane.handle_click(event.pos)
                        if action != "none":
                            self._handle_animations_pane_action(action)
                            return
                    elif event.button == 4:  # Scroll up
                        self.animations_pane.handle_scroll(event.pos, 1)
                        return
                    elif event.button == 5:  # Scroll down
                        self.animations_pane.handle_scroll(event.pos, -1)
                        return
            
            # Phase 2 - Tab manager
            if self.tab_manager:
                if event.type == pygame.MOUSEMOTION:
                    self.tab_manager.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    tab_action = self.tab_manager.handle_click(event.pos)
                    if tab_action != "none":
                        self._handle_tab_manager_action(tab_action)
                        return
        else:
            # Phase 1 - Original animation manager panel
            if self.animation_manager_panel and self.animation_manager_panel.handle_event(event):
                return
        
        # Let splitters handle events
        self._update_splitter_geometry()
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.left_splitter_hover = self.left_splitter_rect.collidepoint(mx, my)
            self.right_splitter_hover = self.right_splitter_rect.collidepoint(mx, my)
            # Apply dragging
            if self.drag_left_splitter:
                new_w = mx
                # Clamp
                max_left = self.window_size[0] - self.right_panel_width - self.min_center_width
                new_w = max(self.min_left_width, min(new_w, max_left))
                self.left_panel_width = new_w
            if self.drag_right_splitter:
                # Right splitter moves left boundary of right panel
                new_right_width = self.window_size[0] - mx - self.splitter_width // 2
                max_right = self.window_size[0] - self.left_panel_width - self.min_center_width
                new_right_width = max(self.min_right_width, min(new_right_width, max_right))
                self.right_panel_width = new_right_width
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_splitter_rect.collidepoint(event.pos):
                self.drag_left_splitter = True
            elif self.right_splitter_rect.collidepoint(event.pos):
                self.drag_right_splitter = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_left_splitter or self.drag_right_splitter:
                # Persist new widths
                self.preferences.set("layout", "left_panel_width", int(self.left_panel_width))
                self.preferences.set("layout", "right_panel_width", int(self.right_panel_width))
            self.drag_left_splitter = False
            self.drag_right_splitter = False
        
        # After potential changes, rebuild dependent layout pieces
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP) and (self.drag_left_splitter or self.drag_right_splitter or self.left_splitter_hover or self.right_splitter_hover):
            self._update_panel_layout()
            
        # End splitter handling
        
        
        # Handle center panel events
        center_rect = self.get_center_panel_rect()
        
        if event.type == pygame.MOUSEMOTION:
            # Update status bar with mouse info
            if center_rect.collidepoint(event.pos):
                frame_pos = self._get_frame_at_mouse(event.pos)
                if frame_pos:
                    frame_index = frame_pos[0] * self.active_sheet.cols + frame_pos[1] if self.active_sheet else None
                    self.status_bar.set_mouse_info(event.pos, frame_pos, frame_index)
                else:
                    self.status_bar.set_mouse_info(event.pos)
        else:
                self.status_bar.set_mouse_info(event.pos)
        
        # Handle frame selection and other main functionality
        if not self.save_mode:
            self._handle_main_events(event, center_rect)
        else:
            self._handle_save_events(event)
    
    def _get_frame_info_at_mouse(self, pos: Tuple[int, int]) -> str:
        """Get frame information at mouse position."""
        if not self.active_sheet:
            return ""
        
        center_rect = self.get_center_panel_rect()
        if not center_rect.collidepoint(pos):
            return ""
        
        # Calculate which frame is under the mouse
        # This would need the tile positioning logic from the original viewer
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame info detection
        return f"Frame info: ({relative_x:.0f}, {relative_y:.0f})"
    
    def _handle_main_events(self, event, center_rect: pygame.Rect):
        """Handle events in main mode for the center panel."""
        if event.type == pygame.KEYDOWN:
            # Handle keyboard shortcuts
            self._handle_keyboard_shortcuts(event)
            
            # Grid navigation (preserved from original)
            if self.active_sheet:
                self._handle_navigation_keys(event.key, event.mod)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Only handle mouse events in center panel
            if not center_rect.collidepoint(event.pos):
                return
                
            if event.button == 1:  # Left click
                # Get current key modifiers
                keys = pygame.key.get_pressed()
                mod = 0
                if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    mod |= pygame.KMOD_CTRL
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    mod |= pygame.KMOD_SHIFT
                
                self._handle_frame_click(event.pos, mod, center_rect)
            
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos, center_rect)
                
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 30)
                
            elif event.button == 5:  # Scroll down
                self.scroll_y += 30
        
        elif event.type == pygame.MOUSEMOTION:
            if center_rect.collidepoint(event.pos):
                self._handle_mouse_motion(event, center_rect)
    
    def _handle_keyboard_shortcuts(self, event):
        """Handle keyboard shortcuts."""
        mod = event.mod
        key = event.key
        
        # File operations
        if key == pygame.K_o and (mod & pygame.KMOD_CTRL):
            self._menu_open_sprite_sheet()
        elif key == pygame.K_s and (mod & pygame.KMOD_CTRL):
            if mod & pygame.KMOD_SHIFT:
                self._menu_save_animation_as()
        else:
                self._menu_save_animation()
        elif key == pygame.K_n and (mod & pygame.KMOD_CTRL):
            self._menu_new_project()
        elif key == pygame.K_q and (mod & pygame.KMOD_CTRL):
            self._menu_exit()
        
        # Selection operations
        elif key == pygame.K_a and (mod & pygame.KMOD_CTRL):
            self._menu_select_all()
        elif key == pygame.K_d and (mod & pygame.KMOD_CTRL):
            self._menu_clear_selection()
        
        # Display toggles
        elif key == pygame.K_g:
            self._menu_toggle_grid()
        elif key == pygame.K_h:
            self.show_help = not self.show_help
        elif key == pygame.K_t:
            self._menu_toggle_analysis()
        elif key == pygame.K_r:
            self._menu_select_row()
        
        # Other shortcuts
        elif key == pygame.K_ESCAPE:
            self._menu_clear_selection()
        elif key == pygame.K_F5:
            self._menu_refresh_animations()
        elif key == pygame.K_F1:
            self._menu_shortcuts()
    
    def _handle_frame_click(self, pos: Tuple[int, int], mod: int, center_rect: pygame.Rect):
        """Handle clicks on frame grid in center panel."""
        if not self.active_sheet:
            return
        
        # Convert screen position to grid coordinates
        # This would need the full positioning logic from the original viewer
        # For now, just update cursor position
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame click detection
        # This is a simplified version
        if self.active_sheet.get_tile_count() > 0:
            rows, cols = self.active_sheet.rows, self.active_sheet.cols
            
            # Calculate which frame was clicked (simplified)
            tile_width, tile_height = self.active_sheet.tile_size
            scale = 1.0  # TODO: Add proper scaling
            
            col = int(relative_x // (tile_width * scale))
            row = int(relative_y // (tile_height * scale))
            
            if 0 <= row < rows and 0 <= col < cols:
                self.cursor_row, self.cursor_col = row, col
                
                # Handle selection
                if mod & pygame.KMOD_CTRL:
                    self._toggle_select(row, col)
                else:
                    if not (mod & pygame.KMOD_SHIFT):
                        self._clear_selection()
                    self._toggle_select(row, col)
    
    def _handle_right_click(self, pos: Tuple[int, int], center_rect: pygame.Rect):
        """Handle right clicks on frame grid."""
        # TODO: Implement context menu
        pass
    
    def _handle_mouse_motion(self, event, center_rect: pygame.Rect):
        """Handle mouse motion in center panel."""
        # TODO: Implement mouse drag for selection
        pass
    
    def _handle_navigation_keys(self, key, mod):
        """Handle grid navigation keys."""
        if not self.active_sheet:
            return
        
        old_row, old_col = self.cursor_row, self.cursor_col
        
        if key == pygame.K_LEFT:
            self.cursor_col = max(0, self.cursor_col - 1)
        elif key == pygame.K_RIGHT:
            self.cursor_col = min(self.active_sheet.cols - 1, self.cursor_col + 1)
        elif key == pygame.K_UP:
            self.cursor_row = max(0, self.cursor_row - 1)
        elif key == pygame.K_DOWN:
            self.cursor_row = min(self.active_sheet.rows - 1, self.cursor_row + 1)
        elif key == pygame.K_SPACE:
            self._toggle_select(self.cursor_row, self.cursor_col)
        elif key == pygame.K_r:
            self._select_row(self.cursor_row)
        
        # Ensure cursor is visible
        if (old_row, old_col) != (self.cursor_row, self.cursor_col):
            self._ensure_cursor_visible()
    
    def _handle_mouse_click(self, pos, mod):
        """Handle mouse clicks on the frame grid."""
        if not self.active_sheet:
            return
        
        # Convert screen coordinates to grid coordinates
        scale = self._compute_scale()
        view_rect = pygame.Rect(0, self.header_height, 
                               self.screen.get_width(), 
                               self.screen.get_height() - self.header_height)
        
        # Adjust for scroll
        grid_x = pos[0] + self.scroll_x
        grid_y = (pos[1] - self.header_height) + self.scroll_y
        
        # Convert to sprite sheet coordinates
        sheet_x = grid_x / scale
        sheet_y = grid_y / scale
        
        # Find which frame was clicked
        for row in range(self.active_sheet.rows):
            for col in range(self.active_sheet.cols):
                frame_rect = self.active_sheet.get_frame_rect(row, col)
                if frame_rect.collidepoint(sheet_x, sheet_y):
                    self.cursor_row, self.cursor_col = row, col
                    
                    # Toggle selection
                    if mod & pygame.KMOD_CTRL:
                        self._toggle_select(row, col)
                    else:
                        self._clear_selection()
                        self._toggle_select(row, col)
                    return
    
    def _handle_save_events(self, event):
        """Handle events during save dialog."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._cancel_save()
            elif event.key == pygame.K_RETURN:
                self._commit_current_input()
            elif event.key == pygame.K_BACKSPACE:
                self.current_text = self.current_text[:-1]
        elif event.type == pygame.TEXTINPUT:
            self.current_text += event.text
    
    def _open_sprite_sheet(self):
        """Open sprite sheet dialog."""
        try:
            filepaths = self.file_manager.open_sprite_sheet_dialog()
            if filepaths:
                # For now, load the first selected file
                filepath = filepaths[0]
                
                # TODO: Add proper tile size detection dialog
                # For now, use suggested tile size or default
                suggested_size = self.project.sprite_manager.suggest_tile_size(filepath)
                tile_size = suggested_size or (32, 32)
                
                sheet_id = self.project.sprite_manager.load_sprite_sheet(
                    filepath, tile_size, margin=0, spacing=0
                )
                
                if sheet_id:
                    self.active_sheet_id = sheet_id
                    self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                    # Provide active sheet to the info panel
                    if self.sprite_browser_panel:
                        self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, {'name': os.path.basename(filepath)})
                    
                    # Get sprite sheet info for status display
                    tile_count = self.active_sheet.get_tile_count() if self.active_sheet else 0
                    dimensions = f"{self.active_sheet.rows}x{self.active_sheet.cols}" if self.active_sheet else "Unknown"
                    
                    self._update_ui_state()
                    
                    # Show success with detailed info
                    self.status_bar.show_success(f"Loaded {os.path.basename(filepath)} ({dimensions} grid, {tile_count} tiles)")

                    # Auto-detect sibling Aseprite JSON (always attempt)
                    try:
                        base, _ = os.path.splitext(filepath)
                        primary_json = base + ".json"
                        attempted = set()
                        def try_load_json(json_path: str):
                            if not os.path.exists(json_path) or json_path in attempted:
                                return False
                            attempted.add(json_path)
                            from aseprite_loader import AsepriteJSONLoader
                            loader = AsepriteJSONLoader(json_path)
                            doc = loader.load()
                            if doc.animations and doc.frames:
                                # Update grid if needed
                                if self.active_sheet and doc.frames:
                                    self._update_sprite_sheet_from_aseprite(doc)
                                try:
                                    source = AsepriteAnimationSource(doc, json_path)
                                    self._register_aseprite_source(source)
                                    self.status_bar.show_success(f"Auto-loaded Aseprite JSON: {os.path.basename(json_path)} ({len(doc.animations)} animations)")
                                    return True
                                except Exception as adapt_e:
                                    print(f"Auto adapter error: {adapt_e}")
                            return False
                        loaded = try_load_json(primary_json)
                        if not loaded:
                            # Fallback scan directory for matching meta.image
                            sheet_filename = os.path.basename(filepath)
                            folder = os.path.dirname(filepath)
                            for name in os.listdir(folder):
                                if not name.lower().endswith('.json'):
                                    continue
                                candidate_path = os.path.join(folder, name)
                                if candidate_path in attempted:
                                    continue
                                try:
                                    with open(candidate_path, 'r', encoding='utf-8') as jf:
                                        jdata = json.load(jf)
                                    meta = jdata.get('meta', {})
                                    image_ref = meta.get('image')
                                    if image_ref and os.path.basename(image_ref) == sheet_filename:
                                        if try_load_json(candidate_path):
                                            break
                                except Exception as scan_e:
                                    print(f"Auto-scan skip {candidate_path}: {scan_e}")
                    except Exception as ase_e:
                        print(f"Aseprite auto-detect error: {ase_e}")
                else:
                    self.status_bar.show_error(f"Failed to load sprite sheet: {os.path.basename(filepath)}")
        else:
                # User cancelled - no-op
                pass
        except Exception as e:
            error_msg = f"Error loading sprite sheet: {str(e)}"
            self.status_bar.show_error(error_msg)
    
    def get_center_panel_rect(self) -> pygame.Rect:
        """Get the rectangle for the center panel (frame grid area)."""
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        
        # Account for tab bar height at the top of center panel
        tab_bar_height = 32 if self.tab_manager else 0
        adjusted_content_top = content_top + tab_bar_height
        
        left_boundary = self.left_panel_width + self.splitter_width
        right_boundary = self.window_size[0] - self.right_panel_width - self.splitter_width
        
        return pygame.Rect(
            left_boundary, adjusted_content_top,
            right_boundary - left_boundary, content_bottom - adjusted_content_top
        )
    
    def _update_sprite_info_panel(self):
        """Update the sprite sheet info panel with current active sheet."""
        if self.sprite_browser_panel:
            active_tab = self.tab_manager.get_active_tab() if self.tab_manager else None
            tab_info = {
                'name': active_tab.name if active_tab else 'None'
            } if active_tab else None
            
            self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, tab_info)
        
    def _get_auto_exit_time(self):
        """Get auto-exit time from environment variable."""
        try:
            v = os.environ.get("AUTO_EXIT_SEC")
            return float(v) if v else None
        except Exception:
            return None
    
    def _load_default_sprite_sheet(self):
        """Load the default sprite sheet if it exists."""
        # Try to load the existing sprite sheet for backward compatibility
        default_path = os.path.join(os.getcwd(), "Assests", "Sword Master Sprite Sheet 90x37.png")
        if os.path.exists(default_path):
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                default_path, 
                (90, 37), 
                margin=0, 
                spacing=0,
                name="Sword Master"
            )
            if sheet_id:
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                print(f"Loaded default sprite sheet: {default_path}")
    
    def run(self):
        """Main application loop."""
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle auto-exit for testing
            if self.auto_exit is not None:
                self.elapsed_time += dt
                if self.elapsed_time >= self.auto_exit:
                    running = False
                    continue
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self._handle_event(event)
            
            # Update and render
            self._update()
            self._render()
            pygame.display.flip()
        
        # Cleanup
        self._save_window_state()
        self.file_manager.cleanup()
        self.file_ops.cleanup()
        pygame.quit()
    
    def _handle_event(self, event):
        """Handle pygame events with professional UI framework."""
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            self.window_size = (event.w, event.h)
            self._setup_panels()  # Recreate panels with new size
            return
        
        # Let menu bar handle events first
        if self.menu_bar.handle_event(event, self.window_size[0]):
            return
        
        # Let toolbar handle events
        if self.toolbar and self.toolbar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let panels handle events
        if self.sprite_browser_panel and self.sprite_browser_panel.handle_event(event):
            return
            
        # Handle new animations pane vs old animation manager panel
        if self.use_new_animations_pane:
            # Phase 2 - New animations pane
            if self.animations_pane:
                if event.type == pygame.MOUSEMOTION:
                    self.animations_pane.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        action = self.animations_pane.handle_click(event.pos)
                        if action != "none":
                            self._handle_animations_pane_action(action)
                            return
                    elif event.button == 4:  # Scroll up
                        self.animations_pane.handle_scroll(event.pos, 1)
                        return
                    elif event.button == 5:  # Scroll down
                        self.animations_pane.handle_scroll(event.pos, -1)
                        return
            
            # Phase 2 - Tab manager
            if self.tab_manager:
                if event.type == pygame.MOUSEMOTION:
                    self.tab_manager.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    tab_action = self.tab_manager.handle_click(event.pos)
                    if tab_action != "none":
                        self._handle_tab_manager_action(tab_action)
                        return
        else:
            # Phase 1 - Original animation manager panel
            if self.animation_manager_panel and self.animation_manager_panel.handle_event(event):
                return
        
        # Let splitters handle events
        self._update_splitter_geometry()
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.left_splitter_hover = self.left_splitter_rect.collidepoint(mx, my)
            self.right_splitter_hover = self.right_splitter_rect.collidepoint(mx, my)
            # Apply dragging
            if self.drag_left_splitter:
                new_w = mx
                # Clamp
                max_left = self.window_size[0] - self.right_panel_width - self.min_center_width
                new_w = max(self.min_left_width, min(new_w, max_left))
                self.left_panel_width = new_w
            if self.drag_right_splitter:
                # Right splitter moves left boundary of right panel
                new_right_width = self.window_size[0] - mx - self.splitter_width // 2
                max_right = self.window_size[0] - self.left_panel_width - self.min_center_width
                new_right_width = max(self.min_right_width, min(new_right_width, max_right))
                self.right_panel_width = new_right_width
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_splitter_rect.collidepoint(event.pos):
                self.drag_left_splitter = True
            elif self.right_splitter_rect.collidepoint(event.pos):
                self.drag_right_splitter = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_left_splitter or self.drag_right_splitter:
                # Persist new widths
                self.preferences.set("layout", "left_panel_width", int(self.left_panel_width))
                self.preferences.set("layout", "right_panel_width", int(self.right_panel_width))
            self.drag_left_splitter = False
            self.drag_right_splitter = False
        
        # After potential changes, rebuild dependent layout pieces
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP) and (self.drag_left_splitter or self.drag_right_splitter or self.left_splitter_hover or self.right_splitter_hover):
            self._update_panel_layout()
            
        # End splitter handling
        
        
        # Handle center panel events
        center_rect = self.get_center_panel_rect()
        
        if event.type == pygame.MOUSEMOTION:
            # Update status bar with mouse info
            if center_rect.collidepoint(event.pos):
                frame_pos = self._get_frame_at_mouse(event.pos)
                if frame_pos:
                    frame_index = frame_pos[0] * self.active_sheet.cols + frame_pos[1] if self.active_sheet else None
                    self.status_bar.set_mouse_info(event.pos, frame_pos, frame_index)
                else:
                    self.status_bar.set_mouse_info(event.pos)
        else:
                self.status_bar.set_mouse_info(event.pos)
        
        # Handle frame selection and other main functionality
        if not self.save_mode:
            self._handle_main_events(event, center_rect)
        else:
            self._handle_save_events(event)
    
    def _get_frame_info_at_mouse(self, pos: Tuple[int, int]) -> str:
        """Get frame information at mouse position."""
        if not self.active_sheet:
            return ""
        
        center_rect = self.get_center_panel_rect()
        if not center_rect.collidepoint(pos):
            return ""
        
        # Calculate which frame is under the mouse
        # This would need the tile positioning logic from the original viewer
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame info detection
        return f"Frame info: ({relative_x:.0f}, {relative_y:.0f})"
    
    def _handle_main_events(self, event, center_rect: pygame.Rect):
        """Handle events in main mode for the center panel."""
        if event.type == pygame.KEYDOWN:
            # Handle keyboard shortcuts
            self._handle_keyboard_shortcuts(event)
            
            # Grid navigation (preserved from original)
            if self.active_sheet:
                self._handle_navigation_keys(event.key, event.mod)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Only handle mouse events in center panel
            if not center_rect.collidepoint(event.pos):
                return
                
            if event.button == 1:  # Left click
                # Get current key modifiers
                keys = pygame.key.get_pressed()
                mod = 0
                if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    mod |= pygame.KMOD_CTRL
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    mod |= pygame.KMOD_SHIFT
                
                self._handle_frame_click(event.pos, mod, center_rect)
            
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos, center_rect)
                
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 30)
                
            elif event.button == 5:  # Scroll down
                self.scroll_y += 30
        
        elif event.type == pygame.MOUSEMOTION:
            if center_rect.collidepoint(event.pos):
                self._handle_mouse_motion(event, center_rect)
    
    def _handle_keyboard_shortcuts(self, event):
        """Handle keyboard shortcuts."""
        mod = event.mod
        key = event.key
        
        # File operations
        if key == pygame.K_o and (mod & pygame.KMOD_CTRL):
            self._menu_open_sprite_sheet()
        elif key == pygame.K_s and (mod & pygame.KMOD_CTRL):
            if mod & pygame.KMOD_SHIFT:
                self._menu_save_animation_as()
        else:
                self._menu_save_animation()
        elif key == pygame.K_n and (mod & pygame.KMOD_CTRL):
            self._menu_new_project()
        elif key == pygame.K_q and (mod & pygame.KMOD_CTRL):
            self._menu_exit()
        
        # Selection operations
        elif key == pygame.K_a and (mod & pygame.KMOD_CTRL):
            self._menu_select_all()
        elif key == pygame.K_d and (mod & pygame.KMOD_CTRL):
            self._menu_clear_selection()
        
        # Display toggles
        elif key == pygame.K_g:
            self._menu_toggle_grid()
        elif key == pygame.K_h:
            self.show_help = not self.show_help
        elif key == pygame.K_t:
            self._menu_toggle_analysis()
        elif key == pygame.K_r:
            self._menu_select_row()
        
        # Other shortcuts
        elif key == pygame.K_ESCAPE:
            self._menu_clear_selection()
        elif key == pygame.K_F5:
            self._menu_refresh_animations()
        elif key == pygame.K_F1:
            self._menu_shortcuts()
    
    def _handle_frame_click(self, pos: Tuple[int, int], mod: int, center_rect: pygame.Rect):
        """Handle clicks on frame grid in center panel."""
        if not self.active_sheet:
            return
        
        # Convert screen position to grid coordinates
        # This would need the full positioning logic from the original viewer
        # For now, just update cursor position
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame click detection
        # This is a simplified version
        if self.active_sheet.get_tile_count() > 0:
            rows, cols = self.active_sheet.rows, self.active_sheet.cols
            
            # Calculate which frame was clicked (simplified)
            tile_width, tile_height = self.active_sheet.tile_size
            scale = 1.0  # TODO: Add proper scaling
            
            col = int(relative_x // (tile_width * scale))
            row = int(relative_y // (tile_height * scale))
            
            if 0 <= row < rows and 0 <= col < cols:
                self.cursor_row, self.cursor_col = row, col
                
                # Handle selection
                if mod & pygame.KMOD_CTRL:
                    self._toggle_select(row, col)
                else:
                    if not (mod & pygame.KMOD_SHIFT):
                        self._clear_selection()
                    self._toggle_select(row, col)
    
    def _handle_right_click(self, pos: Tuple[int, int], center_rect: pygame.Rect):
        """Handle right clicks on frame grid."""
        # TODO: Implement context menu
        pass
    
    def _handle_mouse_motion(self, event, center_rect: pygame.Rect):
        """Handle mouse motion in center panel."""
        # TODO: Implement mouse drag for selection
        pass
    
    def _handle_navigation_keys(self, key, mod):
        """Handle grid navigation keys."""
        if not self.active_sheet:
            return
        
        old_row, old_col = self.cursor_row, self.cursor_col
        
        if key == pygame.K_LEFT:
            self.cursor_col = max(0, self.cursor_col - 1)
        elif key == pygame.K_RIGHT:
            self.cursor_col = min(self.active_sheet.cols - 1, self.cursor_col + 1)
        elif key == pygame.K_UP:
            self.cursor_row = max(0, self.cursor_row - 1)
        elif key == pygame.K_DOWN:
            self.cursor_row = min(self.active_sheet.rows - 1, self.cursor_row + 1)
        elif key == pygame.K_SPACE:
            self._toggle_select(self.cursor_row, self.cursor_col)
        elif key == pygame.K_r:
            self._select_row(self.cursor_row)
        
        # Ensure cursor is visible
        if (old_row, old_col) != (self.cursor_row, self.cursor_col):
            self._ensure_cursor_visible()
    
    def _handle_mouse_click(self, pos, mod):
        """Handle mouse clicks on the frame grid."""
        if not self.active_sheet:
            return
        
        # Convert screen coordinates to grid coordinates
        scale = self._compute_scale()
        view_rect = pygame.Rect(0, self.header_height, 
                               self.screen.get_width(), 
                               self.screen.get_height() - self.header_height)
        
        # Adjust for scroll
        grid_x = pos[0] + self.scroll_x
        grid_y = (pos[1] - self.header_height) + self.scroll_y
        
        # Convert to sprite sheet coordinates
        sheet_x = grid_x / scale
        sheet_y = grid_y / scale
        
        # Find which frame was clicked
        for row in range(self.active_sheet.rows):
            for col in range(self.active_sheet.cols):
                frame_rect = self.active_sheet.get_frame_rect(row, col)
                if frame_rect.collidepoint(sheet_x, sheet_y):
                    self.cursor_row, self.cursor_col = row, col
                    
                    # Toggle selection
                    if mod & pygame.KMOD_CTRL:
                        self._toggle_select(row, col)
                    else:
                        self._clear_selection()
                        self._toggle_select(row, col)
                    return
    
    def _handle_save_events(self, event):
        """Handle events during save dialog."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._cancel_save()
            elif event.key == pygame.K_RETURN:
                self._commit_current_input()
            elif event.key == pygame.K_BACKSPACE:
                self.current_text = self.current_text[:-1]
        elif event.type == pygame.TEXTINPUT:
            self.current_text += event.text
    
    def _open_sprite_sheet(self):
        """Open sprite sheet dialog."""
        filepaths = self.file_manager.open_sprite_sheet_dialog()
        if filepaths:
            # For now, load the first selected file
            filepath = filepaths[0]
            
            # TODO: Add proper tile size detection dialog
            # For now, use suggested tile size or default
            suggested_size = self.project.sprite_manager.suggest_tile_size(filepath)
            tile_size = suggested_size or (32, 32)
            
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                filepath, tile_size, margin=0, spacing=0
            )
            
            if sheet_id:
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                # Provide active sheet to the info panel
                if self.sprite_browser_panel:
                    self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, {'name': os.path.basename(filepath)})
                
                # Get sprite sheet info for status display
                tile_count = self.active_sheet.get_tile_count() if self.active_sheet else 0
                dimensions = f"{self.active_sheet.rows}x{self.active_sheet.cols}" if self.active_sheet else "Unknown"
                
                self._update_ui_state()
                
                # Show success with detailed info
                self.status_bar.show_success(f"Loaded {filename} ({dimensions} grid, {tile_count} tiles)")

                # Auto-detect sibling Aseprite JSON (always attempt)
                try:
                    base, _ = os.path.splitext(filepath)
                    primary_json = base + ".json"
                    attempted = set()
                    def try_load_json(json_path: str):
                        if not os.path.exists(json_path) or json_path in attempted:
                            return False
                        attempted.add(json_path)
                        from aseprite_loader import AsepriteJSONLoader
                        loader = AsepriteJSONLoader(json_path)
                        doc = loader.load()
                        if doc.animations and doc.frames:
                            # Update grid if needed
                            if self.active_sheet and doc.frames:
                                self._update_sprite_sheet_from_aseprite(doc)
                            try:
                                source = AsepriteAnimationSource(doc, json_path)
                                self._register_aseprite_source(source)
                                self.status_bar.show_success(f"Auto-loaded Aseprite JSON: {os.path.basename(json_path)} ({len(doc.animations)} animations)")
                                return True
                            except Exception as adapt_e:
                                print(f"Auto adapter error: {adapt_e}")
                        return False
                    loaded = try_load_json(primary_json)
                    if not loaded:
                        # Fallback scan directory for matching meta.image
                        sheet_filename = os.path.basename(filepath)
                        folder = os.path.dirname(filepath)
                        for name in os.listdir(folder):
                            if not name.lower().endswith('.json'):
                                continue
                            candidate_path = os.path.join(folder, name)
                            if candidate_path in attempted:
                                continue
                            try:
                                with open(candidate_path, 'r', encoding='utf-8') as jf:
                                    jdata = json.load(jf)
                                meta = jdata.get('meta', {})
                                image_ref = meta.get('image')
                                if image_ref and os.path.basename(image_ref) == sheet_filename:
                                    if try_load_json(candidate_path):
                                        break
                            except Exception as scan_e:
                                print(f"Auto-scan skip {candidate_path}: {scan_e}")
                except Exception as ase_e:
                    print(f"Aseprite auto-detect error: {ase_e}")
        else:
                self.status_bar.show_error(f"Failed to load sprite sheet: {filename}")
                
        except Exception as e:
            error_msg = f"Error loading {os.path.basename(filepath)}: {str(e)}"
            self.status_bar.show_error(error_msg)
    
    def get_center_panel_rect(self) -> pygame.Rect:
        """Get the rectangle for the center panel (frame grid area)."""
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        
        # Account for tab bar height at the top of center panel
        tab_bar_height = 32 if self.tab_manager else 0
        adjusted_content_top = content_top + tab_bar_height
        
        left_boundary = self.left_panel_width + self.splitter_width
        right_boundary = self.window_size[0] - self.right_panel_width - self.splitter_width
        
        return pygame.Rect(
            left_boundary, adjusted_content_top,
            right_boundary - left_boundary, content_bottom - adjusted_content_top
        )
    
    def _update_sprite_info_panel(self):
        """Update the sprite sheet info panel with current active sheet."""
        if self.sprite_browser_panel:
            active_tab = self.tab_manager.get_active_tab() if self.tab_manager else None
            tab_info = {
                'name': active_tab.name if active_tab else 'None'
            } if active_tab else None
            
            self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, tab_info)
        
    def _get_auto_exit_time(self):
        """Get auto-exit time from environment variable."""
        try:
            v = os.environ.get("AUTO_EXIT_SEC")
            return float(v) if v else None
        except Exception:
            return None
    
    def _load_default_sprite_sheet(self):
        """Load the default sprite sheet if it exists."""
        # Try to load the existing sprite sheet for backward compatibility
        default_path = os.path.join(os.getcwd(), "Assests", "Sword Master Sprite Sheet 90x37.png")
        if os.path.exists(default_path):
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                default_path, 
                (90, 37), 
                margin=0, 
                spacing=0,
                name="Sword Master"
            )
            if sheet_id:
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                print(f"Loaded default sprite sheet: {default_path}")
    
    def run(self):
        """Main application loop."""
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle auto-exit for testing
            if self.auto_exit is not None:
                self.elapsed_time += dt
                if self.elapsed_time >= self.auto_exit:
                    running = False
                    continue
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self._handle_event(event)
            
            # Update and render
            self._update()
            self._render()
            pygame.display.flip()
        
        # Cleanup
        self._save_window_state()
        self.file_manager.cleanup()
        self.file_ops.cleanup()
        pygame.quit()
    
    def _handle_event(self, event):
        """Handle pygame events with professional UI framework."""
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            self.window_size = (event.w, event.h)
            self._setup_panels()  # Recreate panels with new size
            return
        
        # Let menu bar handle events first
        if self.menu_bar.handle_event(event, self.window_size[0]):
            return
        
        # Let toolbar handle events
        if self.toolbar and self.toolbar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let panels handle events
        if self.sprite_browser_panel and self.sprite_browser_panel.handle_event(event):
            return
            
        # Handle new animations pane vs old animation manager panel
        if self.use_new_animations_pane:
            # Phase 2 - New animations pane
            if self.animations_pane:
                if event.type == pygame.MOUSEMOTION:
                    self.animations_pane.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        action = self.animations_pane.handle_click(event.pos)
                        if action != "none":
                            self._handle_animations_pane_action(action)
                            return
                    elif event.button == 4:  # Scroll up
                        self.animations_pane.handle_scroll(event.pos, 1)
                        return
                    elif event.button == 5:  # Scroll down
                        self.animations_pane.handle_scroll(event.pos, -1)
                        return
            
            # Phase 2 - Tab manager
            if self.tab_manager:
                if event.type == pygame.MOUSEMOTION:
                    self.tab_manager.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    tab_action = self.tab_manager.handle_click(event.pos)
                    if tab_action != "none":
                        self._handle_tab_manager_action(tab_action)
                        return
        else:
            # Phase 1 - Original animation manager panel
            if self.animation_manager_panel and self.animation_manager_panel.handle_event(event):
                return
        
        # Let splitters handle events
        self._update_splitter_geometry()
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.left_splitter_hover = self.left_splitter_rect.collidepoint(mx, my)
            self.right_splitter_hover = self.right_splitter_rect.collidepoint(mx, my)
            # Apply dragging
            if self.drag_left_splitter:
                new_w = mx
                # Clamp
                max_left = self.window_size[0] - self.right_panel_width - self.min_center_width
                new_w = max(self.min_left_width, min(new_w, max_left))
                self.left_panel_width = new_w
            if self.drag_right_splitter:
                # Right splitter moves left boundary of right panel
                new_right_width = self.window_size[0] - mx - self.splitter_width // 2
                max_right = self.window_size[0] - self.left_panel_width - self.min_center_width
                new_right_width = max(self.min_right_width, min(new_right_width, max_right))
                self.right_panel_width = new_right_width
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_splitter_rect.collidepoint(event.pos):
                self.drag_left_splitter = True
            elif self.right_splitter_rect.collidepoint(event.pos):
                self.drag_right_splitter = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_left_splitter or self.drag_right_splitter:
                # Persist new widths
                self.preferences.set("layout", "left_panel_width", int(self.left_panel_width))
                self.preferences.set("layout", "right_panel_width", int(self.right_panel_width))
            self.drag_left_splitter = False
            self.drag_right_splitter = False
        
        # After potential changes, rebuild dependent layout pieces
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP) and (self.drag_left_splitter or self.drag_right_splitter or self.left_splitter_hover or self.right_splitter_hover):
            self._update_panel_layout()
            
        # End splitter handling
        
        
        # Handle center panel events
        center_rect = self.get_center_panel_rect()
        
        if event.type == pygame.MOUSEMOTION:
            # Update status bar with mouse info
            if center_rect.collidepoint(event.pos):
                frame_pos = self._get_frame_at_mouse(event.pos)
                if frame_pos:
                    frame_index = frame_pos[0] * self.active_sheet.cols + frame_pos[1] if self.active_sheet else None
                    self.status_bar.set_mouse_info(event.pos, frame_pos, frame_index)
                else:
                    self.status_bar.set_mouse_info(event.pos)
        else:
                self.status_bar.set_mouse_info(event.pos)
        
        # Handle frame selection and other main functionality
        if not self.save_mode:
            self._handle_main_events(event, center_rect)
        else:
            self._handle_save_events(event)
    
    def _get_frame_info_at_mouse(self, pos: Tuple[int, int]) -> str:
        """Get frame information at mouse position."""
        if not self.active_sheet:
            return ""
        
        center_rect = self.get_center_panel_rect()
        if not center_rect.collidepoint(pos):
            return ""
        
        # Calculate which frame is under the mouse
        # This would need the tile positioning logic from the original viewer
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame info detection
        return f"Frame info: ({relative_x:.0f}, {relative_y:.0f})"
    
    def _handle_main_events(self, event, center_rect: pygame.Rect):
        """Handle events in main mode for the center panel."""
        if event.type == pygame.KEYDOWN:
            # Handle keyboard shortcuts
            self._handle_keyboard_shortcuts(event)
            
            # Grid navigation (preserved from original)
            if self.active_sheet:
                self._handle_navigation_keys(event.key, event.mod)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Only handle mouse events in center panel
            if not center_rect.collidepoint(event.pos):
                return
                
            if event.button == 1:  # Left click
                # Get current key modifiers
                keys = pygame.key.get_pressed()
                mod = 0
                if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    mod |= pygame.KMOD_CTRL
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    mod |= pygame.KMOD_SHIFT
                
                self._handle_frame_click(event.pos, mod, center_rect)
            
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos, center_rect)
                
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 30)
                
            elif event.button == 5:  # Scroll down
                self.scroll_y += 30
        
        elif event.type == pygame.MOUSEMOTION:
            if center_rect.collidepoint(event.pos):
                self._handle_mouse_motion(event, center_rect)
    
    def _handle_keyboard_shortcuts(self, event):
        """Handle keyboard shortcuts."""
        mod = event.mod
        key = event.key
        
        # File operations
        if key == pygame.K_o and (mod & pygame.KMOD_CTRL):
            self._menu_open_sprite_sheet()
        elif key == pygame.K_s and (mod & pygame.KMOD_CTRL):
            if mod & pygame.KMOD_SHIFT:
                self._menu_save_animation_as()
        else:
                self._menu_save_animation()
        elif key == pygame.K_n and (mod & pygame.KMOD_CTRL):
            self._menu_new_project()
        elif key == pygame.K_q and (mod & pygame.KMOD_CTRL):
            self._menu_exit()
        
        # Selection operations
        elif key == pygame.K_a and (mod & pygame.KMOD_CTRL):
            self._menu_select_all()
        elif key == pygame.K_d and (mod & pygame.KMOD_CTRL):
            self._menu_clear_selection()
        
        # Display toggles
        elif key == pygame.K_g:
            self._menu_toggle_grid()
        elif key == pygame.K_h:
            self.show_help = not self.show_help
        elif key == pygame.K_t:
            self._menu_toggle_analysis()
        elif key == pygame.K_r:
            self._menu_select_row()
        
        # Other shortcuts
        elif key == pygame.K_ESCAPE:
            self._menu_clear_selection()
        elif key == pygame.K_F5:
            self._menu_refresh_animations()
        elif key == pygame.K_F1:
            self._menu_shortcuts()
    
    def _handle_frame_click(self, pos: Tuple[int, int], mod: int, center_rect: pygame.Rect):
        """Handle clicks on frame grid in center panel."""
        if not self.active_sheet:
            return
        
        # Convert screen position to grid coordinates
        # This would need the full positioning logic from the original viewer
        # For now, just update cursor position
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame click detection
        # This is a simplified version
        if self.active_sheet.get_tile_count() > 0:
            rows, cols = self.active_sheet.rows, self.active_sheet.cols
            
            # Calculate which frame was clicked (simplified)
            tile_width, tile_height = self.active_sheet.tile_size
            scale = 1.0  # TODO: Add proper scaling
            
            col = int(relative_x // (tile_width * scale))
            row = int(relative_y // (tile_height * scale))
            
            if 0 <= row < rows and 0 <= col < cols:
                self.cursor_row, self.cursor_col = row, col
                
                # Handle selection
                if mod & pygame.KMOD_CTRL:
                    self._toggle_select(row, col)
                else:
                    if not (mod & pygame.KMOD_SHIFT):
                        self._clear_selection()
                    self._toggle_select(row, col)
    
    def _handle_right_click(self, pos: Tuple[int, int], center_rect: pygame.Rect):
        """Handle right clicks on frame grid."""
        # TODO: Implement context menu
        pass
    
    def _handle_mouse_motion(self, event, center_rect: pygame.Rect):
        """Handle mouse motion in center panel."""
        # TODO: Implement mouse drag for selection
        pass
    
    def _handle_navigation_keys(self, key, mod):
        """Handle grid navigation keys."""
        if not self.active_sheet:
            return
        
        old_row, old_col = self.cursor_row, self.cursor_col
        
        if key == pygame.K_LEFT:
            self.cursor_col = max(0, self.cursor_col - 1)
        elif key == pygame.K_RIGHT:
            self.cursor_col = min(self.active_sheet.cols - 1, self.cursor_col + 1)
        elif key == pygame.K_UP:
            self.cursor_row = max(0, self.cursor_row - 1)
        elif key == pygame.K_DOWN:
            self.cursor_row = min(self.active_sheet.rows - 1, self.cursor_row + 1)
        elif key == pygame.K_SPACE:
            self._toggle_select(self.cursor_row, self.cursor_col)
        elif key == pygame.K_r:
            self._select_row(self.cursor_row)
        
        # Ensure cursor is visible
        if (old_row, old_col) != (self.cursor_row, self.cursor_col):
            self._ensure_cursor_visible()
    
    def _handle_mouse_click(self, pos, mod):
        """Handle mouse clicks on the frame grid."""
        if not self.active_sheet:
            return
        
        # Convert screen coordinates to grid coordinates
        scale = self._compute_scale()
        view_rect = pygame.Rect(0, self.header_height, 
                               self.screen.get_width(), 
                               self.screen.get_height() - self.header_height)
        
        # Adjust for scroll
        grid_x = pos[0] + self.scroll_x
        grid_y = (pos[1] - self.header_height) + self.scroll_y
        
        # Convert to sprite sheet coordinates
        sheet_x = grid_x / scale
        sheet_y = grid_y / scale
        
        # Find which frame was clicked
        for row in range(self.active_sheet.rows):
            for col in range(self.active_sheet.cols):
                frame_rect = self.active_sheet.get_frame_rect(row, col)
                if frame_rect.collidepoint(sheet_x, sheet_y):
                    self.cursor_row, self.cursor_col = row, col
                    
                    # Toggle selection
                    if mod & pygame.KMOD_CTRL:
                        self._toggle_select(row, col)
                    else:
                        self._clear_selection()
                        self._toggle_select(row, col)
                    return
    
    def _handle_save_events(self, event):
        """Handle events during save dialog."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._cancel_save()
            elif event.key == pygame.K_RETURN:
                self._commit_current_input()
            elif event.key == pygame.K_BACKSPACE:
                self.current_text = self.current_text[:-1]
        elif event.type == pygame.TEXTINPUT:
            self.current_text += event.text
    
    def _open_sprite_sheet(self):
        """Open sprite sheet dialog."""
        filepaths = self.file_manager.open_sprite_sheet_dialog()
        if filepaths:
            # For now, load the first selected file
            filepath = filepaths[0]
            
            # TODO: Add proper tile size detection dialog
            # For now, use suggested tile size or default
            suggested_size = self.project.sprite_manager.suggest_tile_size(filepath)
            tile_size = suggested_size or (32, 32)
            
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                filepath, tile_size, margin=0, spacing=0
            )
            
            if sheet_id:
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                # Provide active sheet to the info panel
                if self.sprite_browser_panel:
                    self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, {'name': os.path.basename(filepath)})
                
                # Get sprite sheet info for status display
                tile_count = self.active_sheet.get_tile_count() if self.active_sheet else 0
                dimensions = f"{self.active_sheet.rows}x{self.active_sheet.cols}" if self.active_sheet else "Unknown"
                
                self._update_ui_state()
                
                # Show success with detailed info
                self.status_bar.show_success(f"Loaded {filename} ({dimensions} grid, {tile_count} tiles)")

                # Auto-detect sibling Aseprite JSON (always attempt)
                try:
                    base, _ = os.path.splitext(filepath)
                    primary_json = base + ".json"
                    attempted = set()
                    def try_load_json(json_path: str):
                        if not os.path.exists(json_path) or json_path in attempted:
                            return False
                        attempted.add(json_path)
                        from aseprite_loader import AsepriteJSONLoader
                        loader = AsepriteJSONLoader(json_path)
                        doc = loader.load()
                        if doc.animations and doc.frames:
                            # Update grid if needed
                            if self.active_sheet and doc.frames:
                                self._update_sprite_sheet_from_aseprite(doc)
                            try:
                                source = AsepriteAnimationSource(doc, json_path)
                                self._register_aseprite_source(source)
                                self.status_bar.show_success(f"Auto-loaded Aseprite JSON: {os.path.basename(json_path)} ({len(doc.animations)} animations)")
                                return True
                            except Exception as adapt_e:
                                print(f"Auto adapter error: {adapt_e}")
                        return False
                    loaded = try_load_json(primary_json)
                    if not loaded:
                        # Fallback scan directory for matching meta.image
                        sheet_filename = os.path.basename(filepath)
                        folder = os.path.dirname(filepath)
                        for name in os.listdir(folder):
                            if not name.lower().endswith('.json'):
                                continue
                            candidate_path = os.path.join(folder, name)
                            if candidate_path in attempted:
                                continue
                            try:
                                with open(candidate_path, 'r', encoding='utf-8') as jf:
                                    jdata = json.load(jf)
                                meta = jdata.get('meta', {})
                                image_ref = meta.get('image')
                                if image_ref and os.path.basename(image_ref) == sheet_filename:
                                    if try_load_json(candidate_path):
                                        break
                            except Exception as scan_e:
                                print(f"Auto-scan skip {candidate_path}: {scan_e}")
                except Exception as ase_e:
                    print(f"Aseprite auto-detect error: {ase_e}")
        else:
                self.status_bar.show_error(f"Failed to load sprite sheet: {filename}")
                
        except Exception as e:
            error_msg = f"Error loading {os.path.basename(filepath)}: {str(e)}"
            self.status_bar.show_error(error_msg)
    
    def get_center_panel_rect(self) -> pygame.Rect:
        """Get the rectangle for the center panel (frame grid area)."""
        content_top = self.menu_height + self.toolbar_height
        content_bottom = self.window_size[1] - self.status_height
        
        # Account for tab bar height at the top of center panel
        tab_bar_height = 32 if self.tab_manager else 0
        adjusted_content_top = content_top + tab_bar_height
        
        left_boundary = self.left_panel_width + self.splitter_width
        right_boundary = self.window_size[0] - self.right_panel_width - self.splitter_width
        
        return pygame.Rect(
            left_boundary, adjusted_content_top,
            right_boundary - left_boundary, content_bottom - adjusted_content_top
        )
    
    def _update_sprite_info_panel(self):
        """Update the sprite sheet info panel with current active sheet."""
        if self.sprite_browser_panel:
            active_tab = self.tab_manager.get_active_tab() if self.tab_manager else None
            tab_info = {
                'name': active_tab.name if active_tab else 'None'
            } if active_tab else None
            
            self.sprite_browser_panel.set_active_spritesheet(self.active_sheet, tab_info)
        
    def _get_auto_exit_time(self):
        """Get auto-exit time from environment variable."""
        try:
            v = os.environ.get("AUTO_EXIT_SEC")
            return float(v) if v else None
        except Exception:
            return None
    
    def _load_default_sprite_sheet(self):
        """Load the default sprite sheet if it exists."""
        # Try to load the existing sprite sheet for backward compatibility
        default_path = os.path.join(os.getcwd(), "Assests", "Sword Master Sprite Sheet 90x37.png")
        if os.path.exists(default_path):
            sheet_id = self.project.sprite_manager.load_sprite_sheet(
                default_path, 
                (90, 37), 
                margin=0, 
                spacing=0,
                name="Sword Master"
            )
            if sheet_id:
                self.active_sheet_id = sheet_id
                self.active_sheet = self.project.sprite_manager.get_sprite_sheet(sheet_id)
                print(f"Loaded default sprite sheet: {default_path}")
    
    def run(self):
        """Main application loop."""
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle auto-exit for testing
            if self.auto_exit is not None:
                self.elapsed_time += dt
                if self.elapsed_time >= self.auto_exit:
                    running = False
                    continue
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self._handle_event(event)
            
            # Update and render
            self._update()
            self._render()
            pygame.display.flip()
        
        # Cleanup
        self._save_window_state()
        self.file_manager.cleanup()
        self.file_ops.cleanup()
        pygame.quit()
    
    def _handle_event(self, event):
        """Handle pygame events with professional UI framework."""
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            self.window_size = (event.w, event.h)
            self._setup_panels()  # Recreate panels with new size
            return
        
        # Let menu bar handle events first
        if self.menu_bar.handle_event(event, self.window_size[0]):
            return
        
        # Let toolbar handle events
        if self.toolbar and self.toolbar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let status bar handle events
        if self.status_bar.handle_event(event):
            return
        
        # Let panels handle events
        if self.sprite_browser_panel and self.sprite_browser_panel.handle_event(event):
            return
            
        # Handle new animations pane vs old animation manager panel
        if self.use_new_animations_pane:
            # Phase 2 - New animations pane
            if self.animations_pane:
                if event.type == pygame.MOUSEMOTION:
                    self.animations_pane.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        action = self.animations_pane.handle_click(event.pos)
                        if action != "none":
                            self._handle_animations_pane_action(action)
                            return
                    elif event.button == 4:  # Scroll up
                        self.animations_pane.handle_scroll(event.pos, 1)
                        return
                    elif event.button == 5:  # Scroll down
                        self.animations_pane.handle_scroll(event.pos, -1)
                        return
            
            # Phase 2 - Tab manager
            if self.tab_manager:
                if event.type == pygame.MOUSEMOTION:
                    self.tab_manager.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    tab_action = self.tab_manager.handle_click(event.pos)
                    if tab_action != "none":
                        self._handle_tab_manager_action(tab_action)
                        return
        else:
            # Phase 1 - Original animation manager panel
            if self.animation_manager_panel and self.animation_manager_panel.handle_event(event):
                return
        
        # Let splitters handle events
        self._update_splitter_geometry()
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.left_splitter_hover = self.left_splitter_rect.collidepoint(mx, my)
            self.right_splitter_hover = self.right_splitter_rect.collidepoint(mx, my)
            # Apply dragging
            if self.drag_left_splitter:
                new_w = mx
                # Clamp
                max_left = self.window_size[0] - self.right_panel_width - self.min_center_width
                new_w = max(self.min_left_width, min(new_w, max_left))
                self.left_panel_width = new_w
            if self.drag_right_splitter:
                # Right splitter moves left boundary of right panel
                new_right_width = self.window_size[0] - mx - self.splitter_width // 2
                max_right = self.window_size[0] - self.left_panel_width - self.min_center_width
                new_right_width = max(self.min_right_width, min(new_right_width, max_right))
                self.right_panel_width = new_right_width
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_splitter_rect.collidepoint(event.pos):
                self.drag_left_splitter = True
            elif self.right_splitter_rect.collidepoint(event.pos):
                self.drag_right_splitter = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_left_splitter or self.drag_right_splitter:
                # Persist new widths
                self.preferences.set("layout", "left_panel_width", int(self.left_panel_width))
                self.preferences.set("layout", "right_panel_width", int(self.right_panel_width))
            self.drag_left_splitter = False
            self.drag_right_splitter = False
        
        # After potential changes, rebuild dependent layout pieces
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP) and (self.drag_left_splitter or self.drag_right_splitter or self.left_splitter_hover or self.right_splitter_hover):
            self._update_panel_layout()
            
        # End splitter handling
        
        
        # Handle center panel events
        center_rect = self.get_center_panel_rect()
        
        if event.type == pygame.MOUSEMOTION:
            # Update status bar with mouse info
            if center_rect.collidepoint(event.pos):
                frame_pos = self._get_frame_at_mouse(event.pos)
                if frame_pos:
                    frame_index = frame_pos[0] * self.active_sheet.cols + frame_pos[1] if self.active_sheet else None
                    self.status_bar.set_mouse_info(event.pos, frame_pos, frame_index)
                else:
                    self.status_bar.set_mouse_info(event.pos)
        else:
                self.status_bar.set_mouse_info(event.pos)
        
        # Handle frame selection and other main functionality
        if not self.save_mode:
            self._handle_main_events(event, center_rect)
        else:
            self._handle_save_events(event)
    
    def _get_frame_info_at_mouse(self, pos: Tuple[int, int]) -> str:
        """Get frame information at mouse position."""
        if not self.active_sheet:
            return ""
        
        center_rect = self.get_center_panel_rect()
        if not center_rect.collidepoint(pos):
            return ""
        
        # Calculate which frame is under the mouse
        # This would need the tile positioning logic from the original viewer
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame info detection
        return f"Frame info: ({relative_x:.0f}, {relative_y:.0f})"
    
    def _handle_main_events(self, event, center_rect: pygame.Rect):
        """Handle events in main mode for the center panel."""
        if event.type == pygame.KEYDOWN:
            # Handle keyboard shortcuts
            self._handle_keyboard_shortcuts(event)
            
            # Grid navigation (preserved from original)
            if self.active_sheet:
                self._handle_navigation_keys(event.key, event.mod)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Only handle mouse events in center panel
            if not center_rect.collidepoint(event.pos):
                return
                
            if event.button == 1:  # Left click
                # Get current key modifiers
                keys = pygame.key.get_pressed()
                mod = 0
                if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    mod |= pygame.KMOD_CTRL
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    mod |= pygame.KMOD_SHIFT
                
                self._handle_frame_click(event.pos, mod, center_rect)
            
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos, center_rect)
                
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - 30)
                
            elif event.button == 5:  # Scroll down
                self.scroll_y += 30
        
        elif event.type == pygame.MOUSEMOTION:
            if center_rect.collidepoint(event.pos):
                self._handle_mouse_motion(event, center_rect)
    
    def _handle_keyboard_shortcuts(self, event):
        """Handle keyboard shortcuts."""
        mod = event.mod
        key = event.key
        
        # File operations
        if key == pygame.K_o and (mod & pygame.KMOD_CTRL):
            self._menu_open_sprite_sheet()
        elif key == pygame.K_s and (mod & pygame.KMOD_CTRL):
            if mod & pygame.KMOD_SHIFT:
                self._menu_save_animation_as()
        else:
                self._menu_save_animation()
        elif key == pygame.K_n and (mod & pygame.KMOD_CTRL):
            self._menu_new_project()
        elif key == pygame.K_q and (mod & pygame.KMOD_CTRL):
            self._menu_exit()
        
        # Selection operations
        elif key == pygame.K_a and (mod & pygame.KMOD_CTRL):
            self._menu_select_all()
        elif key == pygame.K_d and (mod & pygame.KMOD_CTRL):
            self._menu_clear_selection()
        
        # Display toggles
        elif key == pygame.K_g:
            self._menu_toggle_grid()
        elif key == pygame.K_h:
            self.show_help = not self.show_help
        elif key == pygame.K_t:
            self._menu_toggle_analysis()
        elif key == pygame.K_r:
            self._menu_select_row()
        
        # Other shortcuts
        elif key == pygame.K_ESCAPE:
            self._menu_clear_selection()
        elif key == pygame.K_F5:
            self._menu_refresh_animations()
        elif key == pygame.K_F1:
            self._menu_shortcuts()
    
    def _handle_frame_click(self, pos: Tuple[int, int], mod: int, center_rect: pygame.Rect):
        """Handle clicks on frame grid in center panel."""
        if not self.active_sheet:
            return
        
        # Convert screen position to grid coordinates
        # This would need the full positioning logic from the original viewer
        # For now, just update cursor position
        relative_x = pos[0] - center_rect.x + self.scroll_x
        relative_y = pos[1] - center_rect.y + self.scroll_y
        
        # TODO: Implement proper frame click detection
        # This is a simplified version
        if self.active_sheet
