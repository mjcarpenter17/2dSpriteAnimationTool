#!/usr/bin/env python3
"""
Animations Pane - UI Panel for Multi-Folder Animation Management

This implements the animations pane system that allows users to:
- Add multiple animation folders for discovery
- Browse animations organized by folder with color-coded headers
- Select animations across different spritesheets with automatic tab creation
- Manage animation library with visual feedback and proper UI polish

Author: AI Assistant
Project: Sprite Animation Tool - Phase 2
"""

import os
import pygame
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

# Import our new animation management system
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from animation_manager import AnimationManager, AnimationFolder, AnimationEntry
from animation_sources import build_folder_json_descriptor, IAnimationSource, AnimationDescriptor


class AnimationsPane:
    """
    UI panel for managing animations with folder-based organization
    and cross-spritesheet workflow support.
    """
    
    def __init__(self, rect: pygame.Rect, animation_manager: AnimationManager):
        """Initialize the animations pane.
        
        Args:
            rect: Rectangle defining the pane's screen area
            animation_manager: AnimationManager instance for data management
        """
        self.rect = rect
        self.animation_manager = animation_manager
        self.scroll_offset = 0
        self.selected_animation: Optional[AnimationEntry] = None
        
        # Fonts
        try:
            self.font = pygame.font.Font(None, 16)
            self.header_font = pygame.font.Font(None, 18)
            self.title_font = pygame.font.Font(None, 20)
        except pygame.error:
            # Fallback to default font
            self.font = pygame.font.SysFont("Arial", 14)
            self.header_font = pygame.font.SysFont("Arial", 16)
            self.title_font = pygame.font.SysFont("Arial", 18)
        
        # UI Constants
        self.HEADER_HEIGHT = 32
        self.FOLDER_HEADER_HEIGHT = 24
        self.ANIMATION_ITEM_HEIGHT = 20
        self.INDENT_SIZE = 16
        self.ADD_FOLDER_BTN_HEIGHT = 28
        self.SCROLL_SPEED = 20
        
        # Colors
        self.BACKGROUND_COLOR = (45, 45, 48)
        self.HEADER_COLOR = (60, 60, 60)
        self.BORDER_COLOR = (80, 80, 80)
        self.TEXT_COLOR = (255, 255, 255)
        self.SECONDARY_TEXT_COLOR = (200, 200, 200)
        self.BUTTON_COLOR = (70, 130, 180)
        self.BUTTON_HOVER_COLOR = (100, 149, 237)
        self.SELECTED_COLOR = (70, 70, 120)
        self.HOVER_COLOR = (55, 55, 65)
        self.ACTIVE_ANIMATION_COLOR = (85, 140, 85)  # Green tint for active animation
        self.ACTIVE_ANIMATION_BORDER = (120, 180, 120)  # Brighter green border
        
        # Interactive elements tracking
        self.add_folder_button_rect: Optional[pygame.Rect] = None
        self.folder_header_rects: Dict[str, pygame.Rect] = {}  # folder_path -> rect
        self.animation_item_rects: Dict[str, pygame.Rect] = {}  # animation_filepath -> rect
        self.hovered_element: Optional[str] = None  # "add_folder", "folder:path", or "animation:filepath"
        
        # Active animation tracking
        self.active_animation_filepath: Optional[str] = None  # Currently loaded animation in main viewer
        
        # Scrolling
        self.content_height = 0
        self.max_scroll = 0
        
        # Auto-refresh interval
        self.last_refresh = datetime.now()
        self.refresh_interval = 30  # seconds
        # External sources (e.g., Aseprite)
        self._external_sources: list[IAnimationSource] = []
        self._merged_descriptors: list[AnimationDescriptor] = []  # cached per frame
        self._external_rects = {}
        self.active_external_descriptor_id: str | None = None

    # Convenience geometry properties so external layout code can treat this like other panels
    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, value):
        self.rect.x = value

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, value):
        self.rect.y = value

    @property
    def width(self):
        return self.rect.width

    @width.setter
    def width(self, value):
        self.rect.width = value

    @property
    def height(self):
        return self.rect.height

    @height.setter
    def height(self, value):
        self.rect.height = value

    def resize(self, width: int, height: int):
        """Resize the pane (used by layout/splitter logic)."""
        self.rect.width = max(120, int(width))
        self.rect.height = max(120, int(height))
        # Recalculate scrolling bounds based on new size
        visible_height = self.rect.height - self.HEADER_HEIGHT - 2
        if visible_height < 0:
            visible_height = 0
        # content_height may not be known until next render; clamp existing scroll
            
        if self.content_height > 0:
            self.max_scroll = max(0, self.content_height - visible_height)
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
    def render(self, surface: pygame.Surface):
        """Main render function for animations pane."""
        # Merge descriptors at start of render
        self._merged_descriptors = []
        external_map = []
        for src in self._external_sources:
            try:
                for desc in src.list_descriptors():
                    external_map.append(desc)
            except Exception as e:
                print(f"External source list error: {e}")
        self._merged_descriptors.extend(external_map)
        # Clear background
        pygame.draw.rect(surface, self.BACKGROUND_COLOR, self.rect)
        # Top, right, bottom borders
        pygame.draw.line(surface, self.BORDER_COLOR, (self.rect.x, self.rect.y), (self.rect.right, self.rect.y))
        pygame.draw.line(surface, self.BORDER_COLOR, (self.rect.right - 1, self.rect.y), (self.rect.right - 1, self.rect.bottom))
        pygame.draw.line(surface, self.BORDER_COLOR, (self.rect.x, self.rect.bottom - 1), (self.rect.right, self.rect.bottom - 1))
        
        # Calculate content area
        content_rect = pygame.Rect(
            self.rect.x + 1,
            self.rect.y + self.HEADER_HEIGHT + 1,
            self.rect.width - 2,
            self.rect.height - self.HEADER_HEIGHT - 2
        )
        
        # Render header
        self._render_header(surface)
        
        # Set up clipping for scrollable content
        surface.set_clip(content_rect)
        
        # Calculate current y position with scroll offset
        current_y = content_rect.y - self.scroll_offset
        
        # Clear tracking dictionaries
        self.folder_header_rects.clear()
        self.animation_item_rects.clear()
        
        # Render "+ Add Folder" button
        current_y = self._render_add_folder_button(surface, current_y, content_rect)
        current_y += 8  # Small gap
        
        # Render folder sections
        for folder in self.animation_manager.folders:
            current_y = self._render_folder_section(surface, folder, current_y, content_rect)
            current_y += 4  # Gap between folders
        # Render external (Aseprite) descriptors after folders
        if self._merged_descriptors:
            hdr_rect = pygame.Rect(content_rect.x, current_y, content_rect.width, self.FOLDER_HEADER_HEIGHT)
            pygame.draw.rect(surface, (65,65,72), hdr_rect)
            pygame.draw.rect(surface, self.BORDER_COLOR, hdr_rect, 1)
            label = self.header_font.render("Imported (Aseprite)", True, self.TEXT_COLOR)
            surface.blit(label, (hdr_rect.x + 25, hdr_rect.y + (hdr_rect.height - label.get_height()) // 2))
            tri_pts = self._get_triangle_points((hdr_rect.x + 10, hdr_rect.y + self.FOLDER_HEADER_HEIGHT // 2), True)
            pygame.draw.polygon(surface, self.TEXT_COLOR, tri_pts)
            current_y = hdr_rect.bottom
            for desc in self._merged_descriptors:
                current_y = self._render_external_descriptor(surface, desc, current_y, content_rect)
            current_y += 4
        
        # Update content height and scroll bounds
        self.content_height = current_y - (content_rect.y - self.scroll_offset)
        self._update_scroll_bounds(content_rect)
        
        # Clear clipping
        surface.set_clip(None)
        
        # Render scrollbar if needed
        if self.max_scroll > 0:
            self._render_scrollbar(surface, content_rect)
    
    def _render_header(self, surface: pygame.Surface):
        """Render the pane header with title."""
        header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.HEADER_HEIGHT)
        pygame.draw.rect(surface, self.HEADER_COLOR, header_rect)
        pygame.draw.line(surface, self.BORDER_COLOR, 
                        (header_rect.x, header_rect.bottom), 
                        (header_rect.right, header_rect.bottom))
        title_text = self.title_font.render("Animations", True, self.TEXT_COLOR)
        title_x = header_rect.x + 8
        title_y = header_rect.y + (header_rect.height - title_text.get_height()) // 2
        surface.blit(title_text, (title_x, title_y))
        total_animations = len(self.animation_manager.get_all_animations()) + len(self._merged_descriptors)
        count_text = f"({total_animations})"
        count_surface = self.font.render(count_text, True, self.SECONDARY_TEXT_COLOR)
        count_x = header_rect.right - count_surface.get_width() - 8
        count_y = header_rect.y + (header_rect.height - count_surface.get_height()) // 2
        surface.blit(count_surface, (count_x, count_y))
    
    def _render_add_folder_button(self, surface: pygame.Surface, y_pos: int, content_rect: pygame.Rect) -> int:
        """Render the '+ Add Folder' button."""
        button_width = content_rect.width - 16
        button_rect = pygame.Rect(content_rect.x + 8, y_pos, button_width, self.ADD_FOLDER_BTN_HEIGHT)
        
        # Store for click detection
        self.add_folder_button_rect = button_rect
        
        # Button color based on hover state
        button_color = self.BUTTON_HOVER_COLOR if self.hovered_element == "add_folder" else self.BUTTON_COLOR
        
        # Draw button
        pygame.draw.rect(surface, button_color, button_rect)
        pygame.draw.rect(surface, self.BORDER_COLOR, button_rect, 1)
        
        # Button text
        button_text = "+ Add Folder"
        text_surface = self.font.render(button_text, True, self.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=button_rect.center)
        surface.blit(text_surface, text_rect)
        
        return button_rect.bottom
    
    def _render_folder_section(self, surface: pygame.Surface, folder: AnimationFolder, 
                              y_pos: int, content_rect: pygame.Rect) -> int:
        """Render a complete folder section with header and animations."""
        current_y = y_pos
        
        # Render folder header
        current_y = self._render_folder_header(surface, folder, current_y, content_rect)
        
        # Render animations if folder is expanded
        if folder.is_expanded:
            for animation in folder.animations:
                current_y = self._render_animation_entry(surface, animation, current_y, content_rect)
        
        return current_y
    
    def _render_folder_header(self, surface: pygame.Surface, folder: AnimationFolder, 
                             y_pos: int, content_rect: pygame.Rect) -> int:
        """Render folder header with colored band and expand/collapse icon."""
        header_rect = pygame.Rect(content_rect.x, y_pos, content_rect.width, self.FOLDER_HEADER_HEIGHT)
        
        # Store for click detection
        self.folder_header_rects[folder.path] = header_rect
        
        # Background color with hover effect
        bg_color = folder.color_band
        if self.hovered_element == f"folder:{folder.path}":
            # Lighten the color for hover effect
            bg_color = tuple(min(255, c + 30) for c in bg_color)
        
        # Draw colored background band
        pygame.draw.rect(surface, bg_color, header_rect)
        pygame.draw.rect(surface, self.BORDER_COLOR, header_rect, 1)
        
        # Draw expand/collapse triangle
        triangle_center = (content_rect.x + 10, y_pos + self.FOLDER_HEADER_HEIGHT // 2)
        triangle_points = self._get_triangle_points(triangle_center, folder.is_expanded)
        pygame.draw.polygon(surface, self.TEXT_COLOR, triangle_points)
        
        # Draw folder name
        text_surface = self.header_font.render(folder.name, True, self.TEXT_COLOR)
        text_x = content_rect.x + 25
        text_y = y_pos + (self.FOLDER_HEADER_HEIGHT - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
        
        # Draw animation count
        count_text = f"({len(folder.animations)})"
        count_surface = self.font.render(count_text, True, self.TEXT_COLOR)
        count_x = header_rect.right - count_surface.get_width() - 8
        count_y = y_pos + (self.FOLDER_HEADER_HEIGHT - count_surface.get_height()) // 2
        surface.blit(count_surface, (count_x, count_y))
        
        return header_rect.bottom
    
    def _render_animation_entry(self, surface: pygame.Surface, animation: AnimationEntry, 
                               y_pos: int, content_rect: pygame.Rect) -> int:
        """Render individual animation entry with metadata and external badges."""
        item_rect = pygame.Rect(content_rect.x, y_pos, content_rect.width, self.ANIMATION_ITEM_HEIGHT)
        self.animation_item_rects[animation.filepath] = item_rect
        is_selected = (self.selected_animation and self.selected_animation.filepath == animation.filepath)
        is_hovered = (self.hovered_element == f"animation:{animation.filepath}")
        is_active = (self.active_animation_filepath == animation.filepath)
        if is_active:
            pygame.draw.rect(surface, self.ACTIVE_ANIMATION_COLOR, item_rect)
            pygame.draw.rect(surface, self.ACTIVE_ANIMATION_BORDER, item_rect, 2)
        elif is_selected:
            pygame.draw.rect(surface, self.SELECTED_COLOR, item_rect)
        elif is_hovered:
            pygame.draw.rect(surface, self.HOVER_COLOR, item_rect)
        thumbnail_width = 24
        thumbnail_spacing = 4
        name_start_x = content_rect.x + self.INDENT_SIZE + thumbnail_width + thumbnail_spacing
        thumbnail_rect = pygame.Rect(
            content_rect.x + self.INDENT_SIZE,
            y_pos + (self.ANIMATION_ITEM_HEIGHT - thumbnail_width) // 2,
            thumbnail_width,
            thumbnail_width
        )
        thumbnail_surface = self._get_animation_thumbnail(animation, thumbnail_width)
        if thumbnail_surface:
            surface.blit(thumbnail_surface, thumbnail_rect)
        else:
            pygame.draw.rect(surface, (80, 80, 80), thumbnail_rect)
            pygame.draw.rect(surface, (120, 120, 120), thumbnail_rect, 1)
        name_surface = self.font.render(animation.name, True, self.TEXT_COLOR)
        name_y = y_pos + (self.ANIMATION_ITEM_HEIGHT - name_surface.get_height()) // 2
        surface.blit(name_surface, (name_start_x, name_y))
        frame_text = f"{animation.frame_count}f"
        frame_surface = self.font.render(frame_text, True, self.SECONDARY_TEXT_COLOR)
        frame_x = item_rect.right - frame_surface.get_width() - 8
        frame_y = y_pos + (self.ANIMATION_ITEM_HEIGHT - frame_surface.get_height()) // 2
        surface.blit(frame_surface, (frame_x, frame_y))
        if animation.spritesheet_path:
            dot_center = (content_rect.x + 8, y_pos + self.ANIMATION_ITEM_HEIGHT // 2)
            pygame.draw.circle(surface, (255, 165, 0), dot_center, 3)
        if is_active:
            play_center_x = content_rect.x + self.INDENT_SIZE - 8
            play_center_y = y_pos + self.ANIMATION_ITEM_HEIGHT // 2
            triangle_size = 4
            triangle_points = [
                (play_center_x - triangle_size//2, play_center_y - triangle_size),
                (play_center_x - triangle_size//2, play_center_y + triangle_size),
                (play_center_x + triangle_size//2, play_center_y)
            ]
            pygame.draw.polygon(surface, self.ACTIVE_ANIMATION_BORDER, triangle_points)
        return item_rect.bottom
    
    def _render_external_descriptor(self, surface, desc: AnimationDescriptor, y_pos: int, content_rect: pygame.Rect) -> int:
        item_rect = pygame.Rect(content_rect.x, y_pos, content_rect.width, self.ANIMATION_ITEM_HEIGHT)
        key = f"ext:{desc.id}"
        self._external_rects[key] = item_rect
        hovered = (self.hovered_element == key)
        active = (self.active_external_descriptor_id == desc.id)
        if hovered:
            pygame.draw.rect(surface, self.HOVER_COLOR, item_rect)
        elif active:
            pygame.draw.rect(surface, self.SELECTED_COLOR, item_rect)
        # Badge pill
        pill_text = 'A' if desc.source_type == 'aseprite' else '?'
        base_color = (148, 92, 204)  # purple
        active_color = (180, 130, 230)
        pill_color = active_color if active else base_color
        pill_rect = pygame.Rect(item_rect.x + self.INDENT_SIZE, y_pos + 3, 18, self.ANIMATION_ITEM_HEIGHT - 6)
        pygame.draw.rect(surface, pill_color, pill_rect, border_radius=7)
        border_col = (220,200,240) if hovered or active else (110,80,150)
        pygame.draw.rect(surface, border_col, pill_rect, 1, border_radius=7)
        letter = self.font.render(pill_text, True, (255,255,255))
        letter_pos = (pill_rect.x + (pill_rect.width - letter.get_width())//2, pill_rect.y + (pill_rect.height - letter.get_height())//2)
        surface.blit(letter, letter_pos)
        # Name
        name_surface = self.font.render(desc.name, True, self.TEXT_COLOR)
        name_x = pill_rect.right + 6
        name_y = y_pos + (self.ANIMATION_ITEM_HEIGHT - name_surface.get_height()) // 2
        surface.blit(name_surface, (name_x, name_y))
        # Frame count right side
        frame_text = f"{desc.frame_count}f"
        frame_surface = self.font.render(frame_text, True, self.SECONDARY_TEXT_COLOR)
        frame_x = item_rect.right - frame_surface.get_width() - 8
        frame_y = y_pos + (self.ANIMATION_ITEM_HEIGHT - frame_surface.get_height()) // 2
        surface.blit(frame_surface, (frame_x, frame_y))
        return item_rect.bottom
    
    def _get_triangle_points(self, center: Tuple[int, int], is_expanded: bool) -> List[Tuple[int, int]]:
        """Get triangle points for expand/collapse indicator."""
        cx, cy = center
        size = 4
        
        if is_expanded:
            # Downward pointing triangle
            return [
                (cx - size, cy - size//2),
                (cx + size, cy - size//2),
                (cx, cy + size//2)
            ]
        else:
            # Rightward pointing triangle
            return [
                (cx - size//2, cy - size),
                (cx - size//2, cy + size),
                (cx + size//2, cy)
            ]
    
    def _render_scrollbar(self, surface: pygame.Surface, content_rect: pygame.Rect):
        """Render scrollbar when content overflows."""
        scrollbar_width = 8
        scrollbar_rect = pygame.Rect(
            content_rect.right - scrollbar_width - 2,
            content_rect.y,
            scrollbar_width,
            content_rect.height
        )
        
        # Background
        pygame.draw.rect(surface, (60, 60, 60), scrollbar_rect)
        
        # Thumb
        if self.max_scroll > 0:
            thumb_height = max(20, int(content_rect.height * content_rect.height / self.content_height))
            thumb_y = scrollbar_rect.y + int(self.scroll_offset * (scrollbar_rect.height - thumb_height) / self.max_scroll)
            thumb_rect = pygame.Rect(scrollbar_rect.x, thumb_y, scrollbar_width, thumb_height)
            pygame.draw.rect(surface, (120, 120, 120), thumb_rect)
    
    def _update_scroll_bounds(self, content_rect: pygame.Rect):
        """Update scrolling bounds based on content."""
        self.max_scroll = max(0, self.content_height - content_rect.height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
    
    def handle_click(self, pos: Tuple[int, int]) -> str:
        """Handle mouse clicks and return action type.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            Action string: "add_folder", "toggle_folder:path", "select_animation:filepath", or "none"
        """
        if not self.rect.collidepoint(pos):
            return "none"
        
        # Check "+ Add Folder" button
        if self.add_folder_button_rect and self.add_folder_button_rect.collidepoint(pos):
            return "add_folder"
        
        # Check folder headers
        for folder_path, rect in self.folder_header_rects.items():
            if rect.collidepoint(pos):
                return f"toggle_folder:{folder_path}"
        
        # Check animation entries
        for animation_filepath, rect in self.animation_item_rects.items():
            if rect.collidepoint(pos):
                return f"select_animation:{animation_filepath}"
        
        # External descriptors
        for key, rect in self._external_rects.items():
            if rect.collidepoint(pos):
                desc_id = key[4:]
                return f"select_external:{desc_id}"
        return "none"
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse motion for hover effects."""
        if not self.rect.collidepoint(pos):
            self.hovered_element = None
            return
        
        # Check what we're hovering over
        if self.add_folder_button_rect and self.add_folder_button_rect.collidepoint(pos):
            self.hovered_element = "add_folder"
        else:
            # Check folder headers
            for folder_path, rect in self.folder_header_rects.items():
                if rect.collidepoint(pos):
                    self.hovered_element = f"folder:{folder_path}"
                    return
            
            # Check animation entries
            for animation_filepath, rect in self.animation_item_rects.items():
                if rect.collidepoint(pos):
                    self.hovered_element = f"animation:{animation_filepath}"
                    return
            # External descriptors
            for key, rect in self._external_rects.items():
                if rect.collidepoint(pos):
                    self.hovered_element = key
                    return
            self.hovered_element = None
    
    def handle_scroll(self, pos: Tuple[int, int], direction: int):
        """Handle mouse wheel scrolling.
        
        Args:
            pos: Mouse position
            direction: Scroll direction (positive = up, negative = down)
        """
        if not self.rect.collidepoint(pos):
            return
        
        scroll_amount = direction * self.SCROLL_SPEED
        self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - scroll_amount))
    
    def select_animation(self, animation_filepath: str):
        """Select an animation by filepath."""
        animation = self.animation_manager.get_animation_by_path(animation_filepath)
        if animation:
            self.selected_animation = animation
    
    def refresh_if_needed(self):
        """Refresh animation data if enough time has passed."""
        now = datetime.now()
        if (now - self.last_refresh).total_seconds() >= self.refresh_interval:
            self.animation_manager.rescan_all_folders()
            self.last_refresh = now
    
    def get_selected_animation(self) -> Optional[AnimationEntry]:
        """Get the currently selected animation."""
        return self.selected_animation
    
    def set_active_animation(self, animation_filepath: str):
        """Set the currently active animation being displayed in the main viewer."""
        self.active_animation_filepath = animation_filepath
    
    def clear_active_animation(self):
        """Clear the active animation indicator."""
        self.active_animation_filepath = None
    
    def add_folder_dialog(self) -> Optional[str]:
        """Show folder selection dialog and return selected path."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            folder_path = filedialog.askdirectory(
                title="Select Animation Folder",
                initialdir=os.getcwd()
            )
            
            root.destroy()
            return folder_path if folder_path else None
            
        except ImportError:
            print("tkinter not available for folder dialog")
            return None
    
    def process_action(self, action: str) -> bool:
        """Process an action returned from handle_click.
        
        Args:
            action: Action string from handle_click
            
        Returns:
            True if action was processed, False otherwise
        """
        if action == "add_folder":
            folder_path = self.add_folder_dialog()
            if folder_path:
                folder = self.animation_manager.add_folder(folder_path)
                if folder:
                    print(f"Added animation folder: {folder.name}")
                    return True
            return False
        
        elif action.startswith("toggle_folder:"):
            folder_path = action[14:]  # Remove "toggle_folder:" prefix
            folder = self.animation_manager.get_folder_by_path(folder_path)
            if folder:
                folder.is_expanded = not folder.is_expanded
                return True
            return False
        
        elif action.startswith("select_animation:"):
            animation_filepath = action[17:]  # Remove "select_animation:" prefix
            self.select_animation(animation_filepath)
            if self.selected_animation:
                print(f"Selected animation: {self.selected_animation.name}")
                return True
            return False
        
        elif action.startswith("select_external:"):
            desc_id = action[len("select_external:"):]

            # Just store last external id for potential UI feedback (future expansion)
            self.last_external_selected = desc_id
            print(f"Selected external animation: {desc_id}")
            return True
        return False
    
    def set_external_sources(self, sources):
        """Set list of external animation sources (read-only descriptors)."""
        self._external_sources = list(sources) if sources else []
        self._external_rects.clear()
        self.active_external_descriptor_id = None

    def set_active_external(self, descriptor_id: str):
        self.active_external_descriptor_id = descriptor_id
    
    def _get_animation_thumbnail(self, animation: AnimationEntry, size: int) -> pygame.Surface:
        """Generate thumbnail preview for animation.
        
        Args:
            animation: Animation entry to generate thumbnail for
            size: Size of the thumbnail (square)
            
        Returns:
            Pygame surface with thumbnail, or None if generation failed
        """
        try:
            # Check if we already have a cached thumbnail
            cache_key = f"{animation.filepath}_{size}"
            if hasattr(self, '_thumbnail_cache') and cache_key in self._thumbnail_cache:
                return self._thumbnail_cache[cache_key]
            
            # Initialize cache if needed
            if not hasattr(self, '_thumbnail_cache'):
                self._thumbnail_cache = {}
            
            # Load animation data to get first frame
            if not animation.metadata or 'frames' not in animation.metadata:
                return None
            
            frames = animation.metadata['frames']
            if not frames:
                return None
            
            # Get first frame data
            first_frame = frames[0]
            frame_x = first_frame.get('x', 0)
            frame_y = first_frame.get('y', 0)
            frame_w = first_frame.get('w', 32)
            frame_h = first_frame.get('h', 32)
            
            # Try to load the spritesheet to extract the frame
            spritesheet_path = self._resolve_animation_spritesheet_path(animation)
            if not spritesheet_path or not os.path.exists(spritesheet_path):
                return self._create_placeholder_thumbnail(size)
            
            # Load spritesheet image
            try:
                spritesheet_surface = pygame.image.load(spritesheet_path).convert_alpha()
            except pygame.error:
                return self._create_placeholder_thumbnail(size)
            
            # Extract frame from spritesheet
            frame_rect = pygame.Rect(frame_x, frame_y, frame_w, frame_h)
            if (frame_rect.right > spritesheet_surface.get_width() or 
                frame_rect.bottom > spritesheet_surface.get_height()):
                # Frame is outside spritesheet bounds
                return self._create_placeholder_thumbnail(size)
            
            frame_surface = spritesheet_surface.subsurface(frame_rect).copy()
            
            # Scale to thumbnail size while maintaining aspect ratio
            thumbnail_surface = self._scale_to_thumbnail(frame_surface, size)
            
            # Cache the thumbnail
            self._thumbnail_cache[cache_key] = thumbnail_surface
            
            return thumbnail_surface
            
        except Exception as e:
            print(f"Error generating thumbnail for {animation.name}: {e}")
            return self._create_placeholder_thumbnail(size)
    
    def _resolve_animation_spritesheet_path(self, animation: AnimationEntry) -> str:
        """Resolve the absolute path to animation's spritesheet."""
        if not animation.spritesheet_path:
            return None
        
        # If already absolute, return it
        if os.path.isabs(animation.spritesheet_path):
            return animation.spritesheet_path
        
        # Resolve relative to animation file location
        animation_dir = os.path.dirname(animation.filepath)
        spritesheet_abs = os.path.abspath(os.path.join(animation_dir, animation.spritesheet_path))
        
        if os.path.exists(spritesheet_abs):
            return spritesheet_abs
        
        # Try other common locations (simplified version of main window's resolution)
        # Go up directories to find project root
        current_dir = animation_dir
        for _ in range(3):
            current_dir = os.path.dirname(current_dir)
            if not current_dir or current_dir == os.path.dirname(current_dir):
                break
            
            candidate = os.path.abspath(os.path.join(current_dir, animation.spritesheet_path))
            if os.path.exists(candidate):
                return candidate
        
        return None
    
    def _create_placeholder_thumbnail(self, size: int) -> pygame.Surface:
        """Create a placeholder thumbnail when actual frame can't be loaded."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Create a simple pattern
        color1 = (100, 100, 100, 180)
        color2 = (140, 140, 140, 180)
        
        # Checkerboard pattern
        for x in range(0, size, 4):
            for y in range(0, size, 4):
                color = color1 if (x // 4 + y // 4) % 2 == 0 else color2
                pygame.draw.rect(surface, color, (x, y, 4, 4))
        
        # Border
        pygame.draw.rect(surface, (160, 160, 160), surface.get_rect(), 1)
        
        return surface
    
    def _scale_to_thumbnail(self, source_surface: pygame.Surface, target_size: int) -> pygame.Surface:
        """Scale a surface to fit within thumbnail size while maintaining aspect ratio."""
        source_w, source_h = source_surface.get_size()
        
        # Calculate scale to fit within target size
        scale = min(target_size / source_w, target_size / source_h)
        new_w = int(source_w * scale)
        new_h = int(source_h * scale)
        
        # Create thumbnail surface with padding
        thumbnail = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
        
        # Scale source and center it
        scaled_surface = pygame.transform.scale(source_surface, (new_w, new_h))
        center_x = (target_size - new_w) // 2
        center_y = (target_size - new_h) // 2
        
        thumbnail.blit(scaled_surface, (center_x, center_y))
        
        return thumbnail
    
    def clear_thumbnail_cache(self):
        """Clear the thumbnail cache to free memory."""
        if hasattr(self, '_thumbnail_cache'):
            self._thumbnail_cache.clear()
            print("Thumbnail cache cleared")
    
    def update_display(self):
        """Update the display and clear thumbnails for changed animations."""
        # Clear cache when display updates to ensure fresh thumbnails
        if hasattr(self, '_thumbnail_cache'):
            # Only clear cache for animations that no longer exist
            current_animations = set()
            for folder in self.animation_manager.folders:
                for animation in folder.animations:
                    current_animations.add(animation.filepath)
            
            # Remove cached thumbnails for animations that no longer exist
            to_remove = []
            for cache_key in self._thumbnail_cache:
                animation_path = cache_key.split('_')[0]  # Extract filepath from cache key
                if animation_path not in current_animations:
                    to_remove.append(cache_key)
            
            for key in to_remove:
                del self._thumbnail_cache[key]


# Test function for development
def test_animations_pane():
    """Test function for the animations pane."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Animations Pane Test")
    clock = pygame.time.Clock()
    
    # Create animation manager and add test folder
    animation_manager = AnimationManager()
    test_dir = r"c:\Users\Michael\Documents\Test Games\Walk_GhCp_Test\src\animations\player"
    animation_manager.add_folder(test_dir, "Player Animations")
    
    # Create animations pane
    pane_rect = pygame.Rect(10, 10, 300, 580)
    animations_pane = AnimationsPane(pane_rect, animation_manager)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                animations_pane.handle_mouse_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    action = animations_pane.handle_click(event.pos)
                    animations_pane.process_action(action)
                elif event.button == 4:  # Scroll up
                    animations_pane.handle_scroll(event.pos, 1)
                elif event.button == 5:  # Scroll down
                    animations_pane.handle_scroll(event.pos, -1)
        
        # Clear screen
        screen.fill((30, 30, 30))
        
        # Render animations pane
        animations_pane.render(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    test_animations_pane()
