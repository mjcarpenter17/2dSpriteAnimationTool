"""
Animation management panel for discovering and managing animations.
"""
import pygame
import os
import json
from typing import List, Dict, Optional, Tuple, Any
from .base_panel import Panel


class AnimationManagerPanel(Panel):
    """
    Panel for managing animations with discovery and organization features.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, project):
        """Initialize the animation manager panel."""
        super().__init__(x, y, width, height, "Animations")
        
        self.project = project
        self.animation_manager = project.animation_manager
        
        # Animation list configuration
        self.item_height = 25
        self.scroll_y = 0
        self.max_scroll = 0
        
        # Animation list state
        self.animations: List[Dict[str, Any]] = []
        self.selected_animation: Optional[str] = None
        self.hovered_animation: Optional[str] = None
        
        # UI elements
        self.refresh_button_rect = None
        self.create_button_rect = None
        self.delete_button_rect = None
        self.button_hovered = None
        
        # Search functionality
        self.search_text = ""
        self.search_active = False
        self.filtered_animations = []
        
        # Colors
        self.list_bg_color = (250, 250, 250)
        self.list_border_color = (200, 200, 200)
        self.selected_color = (173, 216, 230)
        self.hover_color = (230, 240, 250)
        self.button_color = (70, 130, 180)
        self.button_hover_color = (100, 149, 237)
        self.button_disabled_color = (150, 150, 150)
        self.search_bg_color = (255, 255, 255)
        
        # Status indicators
        self.status_colors = {
            'valid': (34, 139, 34),      # Green
            'missing_sheet': (255, 140, 0),  # Orange
            'invalid': (220, 20, 60),    # Red
            'modified': (75, 0, 130)     # Purple
        }
        
        # Initial scan
        self.refresh_animations()
    
    def refresh_animations(self):
        """Refresh the animation list by scanning the directory."""
        self.animations = self.animation_manager.discover_animations()
        self._update_filtered_list()
        self._update_scroll_bounds()
    
    def _update_filtered_list(self):
        """Update the filtered animation list based on search."""
        if not self.search_text:
            self.filtered_animations = self.animations.copy()
        else:
            search_lower = self.search_text.lower()
            self.filtered_animations = [
                anim for anim in self.animations
                if search_lower in anim.get('name', '').lower() or
                   search_lower in anim.get('source_sheet', '').lower()
            ]
    
    def _update_scroll_bounds(self):
        """Update scrolling bounds based on content."""
        content_rect = self.get_content_rect()
        total_height = len(self.filtered_animations) * self.item_height
        list_height = content_rect.height - 100  # Reserve space for buttons
        self.max_scroll = max(0, total_height - list_height)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for the animation manager."""
        if not self.visible:
            return False
            
        content_rect = self.get_content_rect()
        
        if event.type == pygame.MOUSEMOTION:
            # Update button hover states
            self._update_button_hovers(event.pos)
            
            # Update animation hover
            self._update_animation_hover(event.pos)
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check button clicks
                if self._handle_button_clicks(event.pos):
                    return True
                    
                # Check animation list clicks
                if self._handle_animation_clicks(event.pos):
                    return True
            
            elif event.button == 4:  # Scroll up
                if content_rect.collidepoint(event.pos):
                    self.scroll_y = max(0, self.scroll_y - 30)
                    return True
                    
            elif event.button == 5:  # Scroll down
                if content_rect.collidepoint(event.pos):
                    self.scroll_y = min(self.max_scroll, self.scroll_y + 30)
                    return True
        
        elif event.type == pygame.KEYDOWN:
            if self.search_active:
                if event.key == pygame.K_RETURN:
                    self.search_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                    self._update_filtered_list()
                    self._update_scroll_bounds()
                elif event.unicode.isprintable():
                    self.search_text += event.unicode
                    self._update_filtered_list()
                    self._update_scroll_bounds()
                return True
        
        return super().handle_event(event)
    
    def _update_button_hovers(self, pos: Tuple[int, int]):
        """Update button hover states."""
        self.button_hovered = None
        if self.refresh_button_rect and self.refresh_button_rect.collidepoint(pos):
            self.button_hovered = 'refresh'
        elif self.create_button_rect and self.create_button_rect.collidepoint(pos):
            self.button_hovered = 'create'
        elif self.delete_button_rect and self.delete_button_rect.collidepoint(pos):
            self.button_hovered = 'delete'
    
    def _update_animation_hover(self, pos: Tuple[int, int]):
        """Update animation hover state."""
        content_rect = self.get_content_rect()
        list_rect = pygame.Rect(content_rect.x, content_rect.y + 30, 
                               content_rect.width, content_rect.height - 100)
        
        if list_rect.collidepoint(pos):
            relative_y = pos[1] - list_rect.y + self.scroll_y
            item_index = int(relative_y // self.item_height)
            
            if 0 <= item_index < len(self.filtered_animations):
                self.hovered_animation = self.filtered_animations[item_index]['name']
            else:
                self.hovered_animation = None
        else:
            self.hovered_animation = None
    
    def _handle_button_clicks(self, pos: Tuple[int, int]) -> bool:
        """Handle button clicks."""
        if self.refresh_button_rect and self.refresh_button_rect.collidepoint(pos):
            self.refresh_animations()
            return True
            
        elif self.create_button_rect and self.create_button_rect.collidepoint(pos):
            self._create_animation()
            return True
            
        elif self.delete_button_rect and self.delete_button_rect.collidepoint(pos):
            if self.selected_animation:
                self._delete_animation(self.selected_animation)
            return True
            
        return False
    
    def _handle_animation_clicks(self, pos: Tuple[int, int]) -> bool:
        """Handle animation list clicks."""
        content_rect = self.get_content_rect()
        list_rect = pygame.Rect(content_rect.x, content_rect.y + 30, 
                               content_rect.width, content_rect.height - 100)
        
        if list_rect.collidepoint(pos):
            relative_y = pos[1] - list_rect.y + self.scroll_y
            item_index = int(relative_y // self.item_height)
            
            if 0 <= item_index < len(self.filtered_animations):
                animation = self.filtered_animations[item_index]
                self.selected_animation = animation['name']
                
                # Notify parent about selection
                if hasattr(self, 'on_animation_selected'):
                    self.on_animation_selected(animation)
                return True
                
        return False
    
    def _create_animation(self):
        """Create a new animation from current selection."""
        # This would be handled by the parent application
        if hasattr(self, 'on_create_animation'):
            self.on_create_animation()
    
    def _delete_animation(self, animation_name: str):
        """Delete an animation."""
        # Find the animation file and delete it
        for animation in self.animations:
            if animation['name'] == animation_name:
                try:
                    if os.path.exists(animation['filepath']):
                        os.remove(animation['filepath'])
                    self.refresh_animations()
                    if self.selected_animation == animation_name:
                        self.selected_animation = None
                    break
                except Exception as e:
                    print(f"Error deleting animation: {e}")
    
    def render_content(self, surface: pygame.Surface):
        """Render the animation manager content."""
        content_rect = self.get_content_rect()
        
        # Render search box
        self._render_search_box(surface, content_rect)
        
        # Render animation list
        self._render_animation_list(surface, content_rect)
        
        # Render buttons
        self._render_buttons(surface, content_rect)
    
    def _render_search_box(self, surface: pygame.Surface, content_rect: pygame.Rect):
        """Render the search box."""
        search_rect = pygame.Rect(content_rect.x, content_rect.y, content_rect.width, 25)
        
        # Draw search box
        pygame.draw.rect(surface, self.search_bg_color, search_rect)
        pygame.draw.rect(surface, self.list_border_color, search_rect, 1)
        
        # Draw search text
        search_display = self.search_text if self.search_text else "Search animations..."
        text_color = self.text_color if self.search_text else (150, 150, 150)
        text_surface = self.font.render(search_display, True, text_color)
        surface.blit(text_surface, (search_rect.x + 5, search_rect.y + 4))
        
        # Draw cursor if search is active
        if self.search_active:
            cursor_x = search_rect.x + 5 + text_surface.get_width()
            pygame.draw.line(surface, self.text_color,
                           (cursor_x, search_rect.y + 3),
                           (cursor_x, search_rect.bottom - 3))
    
    def _render_animation_list(self, surface: pygame.Surface, content_rect: pygame.Rect):
        """Render the animation list."""
        list_rect = pygame.Rect(content_rect.x, content_rect.y + 30, 
                               content_rect.width, content_rect.height - 100)
        
        # Draw list background
        pygame.draw.rect(surface, self.list_bg_color, list_rect)
        pygame.draw.rect(surface, self.list_border_color, list_rect, 1)
        
        # Clip to list area
        original_clip = surface.get_clip()
        surface.set_clip(list_rect)
        
        # Render animation items
        y_offset = list_rect.y - self.scroll_y
        for animation in self.filtered_animations:
            item_rect = pygame.Rect(list_rect.x, y_offset, list_rect.width, self.item_height)
            
            # Skip items that are not visible
            if item_rect.bottom < list_rect.y or item_rect.y > list_rect.bottom:
                y_offset += self.item_height
                continue
            
            # Draw item background
            bg_color = None
            if animation['name'] == self.selected_animation:
                bg_color = self.selected_color
            elif animation['name'] == self.hovered_animation:
                bg_color = self.hover_color
            
            if bg_color:
                pygame.draw.rect(surface, bg_color, item_rect)
            
            # Draw status indicator
            status = self._get_animation_status(animation)
            status_color = self.status_colors.get(status, self.text_color)
            status_rect = pygame.Rect(item_rect.x + 5, item_rect.y + 8, 8, 8)
            pygame.draw.ellipse(surface, status_color, status_rect)
            
            # Draw animation name
            name_surface = self.font.render(animation['name'], True, self.text_color)
            surface.blit(name_surface, (item_rect.x + 20, item_rect.y + 3))
            
            # Draw frame count and source sheet (smaller text)
            info_text = f"{animation.get('frame_count', 0)} frames"
            if animation.get('source_sheet'):
                sheet_name = os.path.basename(animation['source_sheet'])
                info_text += f" • {sheet_name}"
            
            info_surface = pygame.font.Font(None, 14).render(info_text, True, (100, 100, 100))
            surface.blit(info_surface, (item_rect.x + 20, item_rect.y + 18))
            
            y_offset += self.item_height
        
        # Restore clip
        surface.set_clip(original_clip)
        
        # Draw scrollbar if needed
        if self.max_scroll > 0:
            self._render_scrollbar(surface, list_rect)
    
    def _render_scrollbar(self, surface: pygame.Surface, list_rect: pygame.Rect):
        """Render scrollbar for the animation list."""
        scrollbar_width = 12
        scrollbar_rect = pygame.Rect(list_rect.right - scrollbar_width, list_rect.y,
                                   scrollbar_width, list_rect.height)
        
        # Draw scrollbar track
        pygame.draw.rect(surface, (230, 230, 230), scrollbar_rect)
        
        # Calculate thumb position and size
        thumb_height = max(20, int(list_rect.height * list_rect.height / 
                                 (list_rect.height + self.max_scroll)))
        thumb_y = list_rect.y + int(self.scroll_y / self.max_scroll * 
                                   (list_rect.height - thumb_height))
        
        thumb_rect = pygame.Rect(scrollbar_rect.x + 2, thumb_y, 
                               scrollbar_width - 4, thumb_height)
        
        # Draw scrollbar thumb
        pygame.draw.rect(surface, (180, 180, 180), thumb_rect)
        pygame.draw.rect(surface, (150, 150, 150), thumb_rect, 1)
    
    def _render_buttons(self, surface: pygame.Surface, content_rect: pygame.Rect):
        """Render the action buttons."""
        button_y = content_rect.bottom - 35
        button_height = 25
        button_spacing = 5
        button_width = (content_rect.width - 2 * button_spacing) // 3
        
        # Refresh button
        self.refresh_button_rect = pygame.Rect(content_rect.x, button_y, 
                                             button_width, button_height)
        refresh_color = (self.button_hover_color if self.button_hovered == 'refresh' 
                        else self.button_color)
        pygame.draw.rect(surface, refresh_color, self.refresh_button_rect)
        self._render_button_text(surface, self.refresh_button_rect, "Refresh")
        
        # Create button
        create_x = content_rect.x + button_width + button_spacing
        self.create_button_rect = pygame.Rect(create_x, button_y, 
                                            button_width, button_height)
        create_color = (self.button_hover_color if self.button_hovered == 'create' 
                       else self.button_color)
        pygame.draw.rect(surface, create_color, self.create_button_rect)
        self._render_button_text(surface, self.create_button_rect, "Create")
        
        # Delete button
        delete_x = create_x + button_width + button_spacing
        self.delete_button_rect = pygame.Rect(delete_x, button_y, 
                                            button_width, button_height)
        delete_enabled = self.selected_animation is not None
        delete_color = (self.button_hover_color if self.button_hovered == 'delete' and delete_enabled
                       else self.button_color if delete_enabled 
                       else self.button_disabled_color)
        pygame.draw.rect(surface, delete_color, self.delete_button_rect)
        self._render_button_text(surface, self.delete_button_rect, "Delete")
    
    def _render_button_text(self, surface: pygame.Surface, rect: pygame.Rect, text: str):
        """Render text centered on a button."""
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_x = rect.x + (rect.width - text_surface.get_width()) // 2
        text_y = rect.y + (rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
    
    def _get_animation_status(self, animation: Dict[str, Any]) -> str:
        """Get the status of an animation."""
        if not os.path.exists(animation['filepath']):
            return 'invalid'
        
        # Check if source sheet exists
        source_sheet = animation.get('source_sheet')
        if source_sheet and not os.path.exists(source_sheet):
            return 'missing_sheet'
        
        # Check if file has been modified recently
        try:
            stat = os.stat(animation['filepath'])
            import time
            if time.time() - stat.st_mtime < 3600:  # Modified within last hour
                return 'modified'
        except:
            pass
        
        return 'valid'
    
    def get_selected_animation(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected animation."""
        if not self.selected_animation:
            return None
            
        for animation in self.animations:
            if animation['name'] == self.selected_animation:
                return animation
        return None
