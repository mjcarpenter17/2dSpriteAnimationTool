"""
Sprite sheet browser panel for managing and displaying multiple sprite sheets.
"""
import pygame
import os
from typing import List, Dict, Optional, Tuple
from .base_panel import Panel


class SpriteSheetBrowserPanel(Panel):
    """
    Panel for browsing and managing sprite sheets with tabbed interface.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, project):
        """Initialize the sprite sheet info panel."""
        super().__init__(x, y, width, height, "Sprite Sheet Info")
        
        self.project = project
        self.sprite_manager = project.sprite_manager
        
        # Tab configuration
        self.tab_height = 30
        self.tab_padding = 10
        self.tab_min_width = 120
        self.active_tab_color = (255, 255, 255)
        self.inactive_tab_color = (230, 230, 230)
        self.tab_border_color = (180, 180, 180)
        
        # Sheet information display
        self.info_y_offset = self.tab_height + 10
        self.line_height = 20
        
        # Load button
        self.load_button_rect = None
        self.load_button_hovered = False
        
        # Tab management
        self.tabs: List[Dict] = []  # List of tab info: {id, name, rect, close_rect}
        self.active_tab_id: Optional[str] = None
        self.tab_scroll_x = 0  # For scrolling tabs if too many
        
        # Colors for different elements
        self.info_text_color = (60, 60, 60)
        self.label_color = (100, 100, 100)
        self.button_color = (70, 130, 180)
        self.button_hover_color = (100, 149, 237)
        self.button_text_color = (255, 255, 255)
        
        # Editing fields
        self.edit_mode = None  # 'tile_w','tile_h','margin','spacing'
        self.edit_text = ''
        self.fields_rects = {}  # store rects for click detection
    
    def update_tabs(self):
        """Update the tab list based on loaded sprite sheets."""
        self.tabs.clear()
        sheet_ids = self.sprite_manager.get_all_sheet_ids()
        
        x_offset = 5
        for sheet_id in sheet_ids:
            sheet = self.sprite_manager.get_sprite_sheet(sheet_id)
            if not sheet:
                continue
                
            tab_width = max(self.tab_min_width, len(sheet.name) * 8 + 40)
            
            tab_rect = pygame.Rect(
                self.x + x_offset,
                self.y + 25,  # Below title bar
                tab_width,
                self.tab_height
            )
            
            close_rect = pygame.Rect(
                tab_rect.right - 20,
                tab_rect.y + 5,
                15,
                20
            )
            
            self.tabs.append({
                'id': sheet_id,
                'name': sheet.name,
                'rect': tab_rect,
                'close_rect': close_rect
            })
            
            x_offset += tab_width + 2
        
        # Update active tab
        if self.sprite_manager.active_sheet_id:
            self.active_tab_id = self.sprite_manager.active_sheet_id
        elif self.tabs and not self.active_tab_id:
            self.active_tab_id = self.tabs[0]['id']
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for the sprite sheet info panel."""
        if not self.visible:
            return False
            
        if self.edit_mode:
            # While editing, capture keystrokes
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.edit_mode = None; self.edit_text = ''
                    return True
                elif event.key == pygame.K_RETURN:
                    self._commit_field_edit()
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.edit_text = self.edit_text[:-1]
                    return True
                elif event.unicode and (event.unicode.isdigit()):
                    if len(self.edit_text) < 4:
                        self.edit_text += event.unicode
                    return True
            return False if self.edit_mode else super().handle_event(event)
        
        if event.type == pygame.MOUSEMOTION:
            # Check button hover
            if self.load_button_rect and self.load_button_rect.collidepoint(event.pos):
                self.load_button_hovered = True
            else:
                self.load_button_hovered = False
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check load button
                if self.load_button_rect and self.load_button_rect.collidepoint(event.pos):
                    self._load_new_sprite_sheet()
                    return True
                # Detect clicks on field rects
                for key, r in self.fields_rects.items():
                    if r.collidepoint(event.pos):
                        # Begin editing that field
                        self.edit_mode = key
                        self.edit_text = ''
                        return True
        
        return super().handle_event(event)

    def render(self, surface: pygame.Surface):
        """Custom render to suppress right border (splitter will draw)."""
        if not self.visible:
            return
        # Draw background
        rect = self.get_rect()
        pygame.draw.rect(surface, self.bg_color, rect)
        # Left, top, bottom borders only
        pygame.draw.line(surface, self.border_color, (rect.x, rect.y), (rect.right, rect.y))
        pygame.draw.line(surface, self.border_color, (rect.x, rect.bottom - 1), (rect.right, rect.bottom - 1))
        pygame.draw.line(surface, self.border_color, (rect.x, rect.y), (rect.x, rect.bottom))
        # Title bar
        if self.title:
            title_rect = pygame.Rect(rect.x, rect.y, rect.width, 25)
            pygame.draw.rect(surface, self.title_bg_color, title_rect)
            pygame.draw.line(surface, self.border_color, (rect.x, rect.y + 25), (rect.right, rect.y + 25))
            title_surface = self.title_font.render(self.title, True, self.text_color)
            surface.blit(title_surface, (rect.x + 8, rect.y + 6))
        # Content
        self.render_content(surface)
    
    def _switch_to_sprite_sheet(self, sheet_id: str):
        """Switch to a different sprite sheet."""
        if self.sprite_manager.set_active_sheet(sheet_id):
            self.active_tab_id = sheet_id
            # Notify parent application about the change
            if hasattr(self, 'on_sheet_changed'):
                self.on_sheet_changed(sheet_id)
    
    def _close_sprite_sheet(self, sheet_id: str):
        """Close a sprite sheet tab."""
        # Don't close if it's the only sheet
        if len(self.tabs) <= 1:
            return
            
        self.sprite_manager.remove_sheet(sheet_id)
        
        # Switch to another sheet if we closed the active one
        if self.active_tab_id == sheet_id:
            remaining_sheet_ids = self.sprite_manager.get_all_sheet_ids()
            if remaining_sheet_ids:
                next_id = remaining_sheet_ids[0]
                self._switch_to_sprite_sheet(next_id)
        
        self.update_tabs()
    
    def _load_new_sprite_sheet(self):
        """Open dialog to load a new sprite sheet."""
        # This would trigger the parent application's file dialog
        if hasattr(self, 'on_load_requested'):
            self.on_load_requested()
    
    def render_content(self, surface: pygame.Surface):
        """Render the sprite sheet info content."""
        # Render active sheet information
        self._render_sheet_info(surface)
        
        # Render load button
        self._render_load_button(surface)
    
    def set_active_spritesheet(self, spritesheet, tab_info=None):
        """Set the active spritesheet to display info for.
        
        Args:
            spritesheet: The active SpriteSheet object
            tab_info: Optional dict with tab information
        """
        self.active_spritesheet = spritesheet
        self.active_tab_info = tab_info
    
    def _render_tabs(self, surface: pygame.Surface):
        """Render the sprite sheet tabs."""
        for tab in self.tabs:
            # Determine tab color
            if tab['id'] == self.active_tab_id:
                bg_color = self.active_tab_color
            else:
                bg_color = self.inactive_tab_color
            
            # Draw tab background
            pygame.draw.rect(surface, bg_color, tab['rect'])
            pygame.draw.rect(surface, self.tab_border_color, tab['rect'], 1)
            
            # Draw tab text
            text_surface = self.font.render(tab['name'], True, self.text_color)
            text_x = tab['rect'].x + 8
            text_y = tab['rect'].y + (tab['rect'].height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))
            
            # Draw close button (X)
            close_rect = tab['close_rect']
            pygame.draw.rect(surface, (200, 200, 200), close_rect)
            
            # Draw X
            x_color = (100, 100, 100)
            pygame.draw.line(surface, x_color, 
                           (close_rect.x + 3, close_rect.y + 5),
                           (close_rect.right - 3, close_rect.bottom - 5))
            pygame.draw.line(surface, x_color,
                           (close_rect.right - 3, close_rect.y + 5),
                           (close_rect.x + 3, close_rect.bottom - 5))
    
    def _commit_field_edit(self):
        """Commit the edited value for a field."""
        if not self.edit_mode or not self.edit_text:
            self.edit_mode = None; self.edit_text = ''; return
        try:
            value = int(self.edit_text)
            if value <= 0 and self.edit_mode in ('tile_w','tile_h'):  # basic validation
                raise ValueError
            sheet = getattr(self, 'active_spritesheet', None)
            if sheet:
                tw, th = sheet.tile_size
                margin = sheet.margin
                spacing = sheet.spacing
                if self.edit_mode == 'tile_w': tw = value
                elif self.edit_mode == 'tile_h': th = value
                elif self.edit_mode == 'margin': margin = value
                elif self.edit_mode == 'spacing': spacing = value
                # Apply change via reconfigure_grid if available
                if hasattr(sheet, 'reconfigure_grid'):
                    sheet.reconfigure_grid((tw, th), margin=margin, spacing=spacing)
                # Clear any cached selection/analysis in parent (if accessible)
                if hasattr(self.project, 'main_window'):
                    mw = self.project.main_window
                    try:
                        mw._clear_selection()
                        mw._update_ui_state()
                    except Exception:
                        pass
        except Exception:
            pass
        self.edit_mode = None
        self.edit_text = ''

    def _render_sheet_info(self, surface: pygame.Surface):
        """Render information about the active sprite sheet."""
        # Get active sheet from the main application (will be set by parent)
        active_sheet = getattr(self, 'active_spritesheet', None)
        # Fallback to project's sprite manager if not explicitly set
        if not active_sheet and hasattr(self, 'sprite_manager') and hasattr(self.sprite_manager, 'active_sheet_id'):
            try:
                sid = self.sprite_manager.active_sheet_id
                if sid:
                    active_sheet = self.sprite_manager.get_sprite_sheet(sid)
                    # Cache for subsequent frames
                    if active_sheet:
                        self.active_spritesheet = active_sheet
            except Exception:
                pass
        if not active_sheet:
            # Show "No spritesheet loaded" message
            info_x = self.x + 10
            info_y = self.y + 40
            no_sheet_text = "No spritesheet loaded"
            text_surface = self.font.render(no_sheet_text, True, self.info_text_color)
            surface.blit(text_surface, (info_x, info_y))
            
            hint_text = "Use File > Open Sprite Sheet..."
            hint_surface = self.font.render(hint_text, True, self.label_color)
            surface.blit(hint_surface, (info_x, info_y + 25))
            return
        
        # Starting position for info display (no tab height needed now)
        info_x = self.x + 10
        info_y = self.y + 40
        
        # Sheet name
        sheet_name = getattr(active_sheet, 'name', 'Unknown')
        if not sheet_name and hasattr(active_sheet, 'filepath'):
            sheet_name = os.path.basename(active_sheet.filepath)
        self._render_info_line(surface, "Name:", sheet_name, info_x, info_y)
        info_y += self.line_height
        
        # File path (truncated if too long)
        if hasattr(active_sheet, 'filepath') and active_sheet.filepath:
            path = active_sheet.filepath
            if len(path) > 40:
                path = "..." + path[-37:]
            self._render_info_line(surface, "File:", path, info_x, info_y)
            info_y += self.line_height
        
        # Dimensions
        if hasattr(active_sheet, 'surface') and active_sheet.surface:
            size_text = f"{active_sheet.surface.get_width()}x{active_sheet.surface.get_height()}"
            self._render_info_line(surface, "Size:", size_text, info_x, info_y)
            info_y += self.line_height
        
        # Editable fields
        font = self.font
        self.fields_rects = {}
        # Tile width / height
        label_surface = font.render("Tile W:", True, self.label_color); surface.blit(label_surface, (info_x, info_y))
        lx = info_x + label_surface.get_width() + 5
        tw_rect = pygame.Rect(lx, info_y-2, 50, self.line_height)
        pygame.draw.rect(surface, (245,245,245), tw_rect)
        pygame.draw.rect(surface, (120,120,120), tw_rect, 1)
        tw_val = self.edit_text if self.edit_mode=='tile_w' else str(active_sheet.tile_size[0])
        surface.blit(font.render(tw_val, True, self.info_text_color), (tw_rect.x+4, tw_rect.y+2))
        self.fields_rects['tile_w'] = tw_rect
        # Tile height
        label_surface2 = font.render("H:", True, self.label_color); surface.blit(label_surface2, (tw_rect.right + 8, info_y))
        th_rect = pygame.Rect(tw_rect.right + 8 + label_surface2.get_width() + 5, info_y-2, 50, self.line_height)
        pygame.draw.rect(surface, (245,245,245), th_rect); pygame.draw.rect(surface, (120,120,120), th_rect,1)
        th_val = self.edit_text if self.edit_mode=='tile_h' else str(active_sheet.tile_size[1])
        surface.blit(font.render(th_val, True, self.info_text_color), (th_rect.x+4, th_rect.y+2))
        self.fields_rects['tile_h'] = th_rect
        info_y += self.line_height
        # Margin
        label_surface3 = font.render("Margin:", True, self.label_color); surface.blit(label_surface3, (info_x, info_y))
        m_rect = pygame.Rect(info_x + label_surface3.get_width() + 5, info_y-2, 50, self.line_height)
        pygame.draw.rect(surface, (245,245,245), m_rect); pygame.draw.rect(surface, (120,120,120), m_rect,1)
        m_val = self.edit_text if self.edit_mode=='margin' else str(active_sheet.margin)
        surface.blit(font.render(m_val, True, self.info_text_color), (m_rect.x+4, m_rect.y+2))
        self.fields_rects['margin'] = m_rect
        # Spacing
        label_surface4 = font.render("Spacing:", True, self.label_color); surface.blit(label_surface4, (m_rect.right + 10, info_y))
        s_rect = pygame.Rect(m_rect.right + 10 + label_surface4.get_width() + 5, info_y-2, 50, self.line_height)
        pygame.draw.rect(surface, (245,245,245), s_rect); pygame.draw.rect(surface, (120,120,120), s_rect,1)
        s_val = self.edit_text if self.edit_mode=='spacing' else str(active_sheet.spacing)
        surface.blit(font.render(s_val, True, self.info_text_color), (s_rect.x+4, s_rect.y+2))
        self.fields_rects['spacing'] = s_rect
        info_y += self.line_height
        
        # Tile count and grid
        if hasattr(active_sheet, 'get_tile_count'):
            tile_count = active_sheet.get_tile_count()
            if tile_count > 0 and hasattr(active_sheet, 'rows'):
                count_text = f"Tiles: {tile_count} ({active_sheet.rows}x{active_sheet.cols})"
                surface.blit(font.render(count_text, True, self.info_text_color), (info_x, info_y))
                info_y += self.line_height
        
        # Editing hint
        if not self.edit_mode:
            hint = "Click a field to edit (Enter=apply, Esc=cancel)"
            surface.blit(font.render(hint, True, (130,130,130)), (info_x, info_y))
        else:
            hint = f"Editing {self.edit_mode}..."
            surface.blit(font.render(hint, True, (30,120,30)), (info_x, info_y))
        
        # Tab information (from TabManager)
        if hasattr(self, 'active_tab_info') and self.active_tab_info:
            info_y += self.line_height
            surface.blit(font.render(f"Tab: {self.active_tab_info.get('name','Unknown')}", True, self.label_color), (info_x, info_y))
    
    def _render_info_line(self, surface: pygame.Surface, label: str, value: str, x: int, y: int):
        """Render a label-value pair."""
        # Render label
        label_surface = self.font.render(label, True, self.label_color)
        surface.blit(label_surface, (x, y))
        
        # Render value
        label_width = label_surface.get_width()
        value_surface = self.font.render(value, True, self.info_text_color)
        surface.blit(value_surface, (x + label_width + 5, y))
    
    def _render_load_button(self, surface: pygame.Surface):
        """Render the load new sprite sheet button."""
        # Position button at bottom of panel
        button_width = 150
        button_height = 30
        button_x = self.x + (self.width - button_width) // 2
        button_y = self.y + self.height - button_height - 15
        
        self.load_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # Choose button color
        if self.load_button_hovered:
            bg_color = self.button_hover_color
        else:
            bg_color = self.button_color
        
        # Draw button
        pygame.draw.rect(surface, bg_color, self.load_button_rect)
        pygame.draw.rect(surface, self.tab_border_color, self.load_button_rect, 1)
        
        # Draw button text
        button_text = "Load Sprite Sheet"
        text_surface = self.font.render(button_text, True, self.button_text_color)
        text_x = button_x + (button_width - text_surface.get_width()) // 2
        text_y = button_y + (button_height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
