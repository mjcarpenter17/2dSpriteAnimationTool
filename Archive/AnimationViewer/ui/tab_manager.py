#!/usr/bin/env python3
"""
Tab Manager - Multi-Spritesheet Tab System

This implements the tab system for managing multiple spritesheets simultaneously.
Users can switch between different spritesheets and each tab maintains its own
spritesheet state and currently selected animation.

Author: AI Assistant
Project: Sprite Animation Tool - Phase 2
"""

import os
import pygame
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class SpritesheetTab:
    """Represents a single spritesheet tab."""
    spritesheet_path: str
    name: str
    spritesheet: Optional[object] = None  # Will hold SpriteSheet object when loaded
    current_animation: Optional[object] = None  # Current AnimationEntry
    is_loaded: bool = False
    
    def __post_init__(self):
        """Initialize derived properties."""
        if not self.name:
            self.name = os.path.splitext(os.path.basename(self.spritesheet_path))[0]


class TabManager:
    """
    Manages multiple spritesheet tabs with switching and close functionality.
    """
    
    def __init__(self, tab_bar_rect: pygame.Rect):
        """Initialize the tab manager.
        
        Args:
            tab_bar_rect: Rectangle defining the tab bar area
        """
        self.tab_bar_rect = tab_bar_rect
        self.tabs: List[SpritesheetTab] = []
        self.active_tab_index = 0
        self.max_tabs = 8  # Reasonable limit
        
        # Tab appearance
        self.tab_width = 120
        self.tab_height = 30
        self.tab_spacing = 2
        self.close_button_size = 12
        
        # Fonts
        try:
            self.font = pygame.font.Font(None, 16)
        except pygame.error:
            self.font = pygame.font.SysFont("Arial", 14)
        
        # Colors
        self.ACTIVE_TAB_COLOR = (60, 60, 60)
        self.INACTIVE_TAB_COLOR = (40, 40, 40)
        self.ACTIVE_BORDER_COLOR = (100, 100, 100)
        self.INACTIVE_BORDER_COLOR = (70, 70, 70)
        self.TEXT_COLOR = (255, 255, 255)
        self.CLOSE_BUTTON_COLOR = (180, 180, 180)
        self.CLOSE_BUTTON_HOVER_COLOR = (220, 50, 50)
        self.BACKGROUND_COLOR = (35, 35, 35)
        
        # Interactive tracking
        self.hovered_tab: Optional[int] = None
        self.hovered_close_button: Optional[int] = None
        
        # Tab positioning
        self._update_tab_layout()
    
    def add_tab(self, spritesheet_path: str, name: str = None) -> int:
        """Add new tab for spritesheet, return tab index.
        
        Args:
            spritesheet_path: Absolute path to spritesheet file
            name: Optional display name (defaults to filename)
            
        Returns:
            Index of the tab (existing or newly created)
        """
        # Check if spritesheet already has a tab open
        existing_tab = self.find_tab_by_spritesheet(spritesheet_path)
        if existing_tab >= 0:
            self.active_tab_index = existing_tab
            return existing_tab
        
        # Check max tabs limit
        if len(self.tabs) >= self.max_tabs:
            print(f"Maximum number of tabs ({self.max_tabs}) reached")
            return -1
        
        # Create new tab
        tab_name = name or os.path.splitext(os.path.basename(spritesheet_path))[0]
        new_tab = SpritesheetTab(spritesheet_path, tab_name)
        self.tabs.append(new_tab)
        self.active_tab_index = len(self.tabs) - 1
        
        # Update layout
        self._update_tab_layout()
        
        print(f"Added new tab: {tab_name}")
        return self.active_tab_index
    
    def close_tab(self, tab_index: int) -> bool:
        """Close tab and adjust active index.
        
        Args:
            tab_index: Index of tab to close
            
        Returns:
            True if tab was closed, False if invalid index or last tab
        """
        if not (0 <= tab_index < len(self.tabs)):
            return False
        
        # Don't close the last tab if it's the only one
        if len(self.tabs) == 1:
            print("Cannot close the last remaining tab")
            return False
        
        # Remove the tab
        closed_tab = self.tabs.pop(tab_index)
        print(f"Closed tab: {closed_tab.name}")
        
        # Adjust active tab index
        if self.active_tab_index >= tab_index and self.active_tab_index > 0:
            self.active_tab_index -= 1
        elif self.active_tab_index >= len(self.tabs):
            self.active_tab_index = len(self.tabs) - 1
        
        # Update layout
        self._update_tab_layout()
        
        return True
    
    def remove_tab(self, tab_index: int) -> bool:
        """Remove a tab (alias for close_tab for consistency).
        
        Args:
            tab_index: Index of tab to remove
            
        Returns:
            True if tab was removed, False otherwise
        """
        return self.close_tab(tab_index)
    
    def switch_to_tab(self, tab_index: int) -> bool:
        """Switch to the specified tab.
        
        Args:
            tab_index: Index of tab to switch to
            
        Returns:
            True if switch was successful, False if invalid index
        """
        if 0 <= tab_index < len(self.tabs):
            self.active_tab_index = tab_index
            print(f"Switched to tab: {self.tabs[tab_index].name}")
            return True
        return False
    
    def find_tab_by_spritesheet(self, spritesheet_path: str) -> int:
        """Find tab index by spritesheet path.
        
        Args:
            spritesheet_path: Path to spritesheet file
            
        Returns:
            Tab index if found, -1 if not found
        """
        abs_path = os.path.abspath(spritesheet_path)
        for i, tab in enumerate(self.tabs):
            if os.path.abspath(tab.spritesheet_path) == abs_path:
                return i
        return -1
    
    def get_active_tab(self) -> Optional[SpritesheetTab]:
        """Get the currently active tab.
        
        Returns:
            Active SpritesheetTab or None if no tabs
        """
        if 0 <= self.active_tab_index < len(self.tabs):
            return self.tabs[self.active_tab_index]
        return None
    
    def get_tab_count(self) -> int:
        """Get the number of open tabs."""
        return len(self.tabs)

    def set_bar_rect(self, rect: pygame.Rect):
        """Update the tab bar rectangle (used when panels are resized)."""
        self.tab_bar_rect = rect
        self._update_tab_layout()
    
    def render_tabs(self, surface: pygame.Surface):
        """Render tab bar with clickable tabs."""
        # Clear background
        pygame.draw.rect(surface, self.BACKGROUND_COLOR, self.tab_bar_rect)
        
        # Render each tab
        for i, tab in enumerate(self.tabs):
            tab_rect = self.get_tab_rect(i)
            is_active = (i == self.active_tab_index)
            is_hovered = (self.hovered_tab == i)
            
            # Tab background
            if is_active:
                tab_color = self.ACTIVE_TAB_COLOR
                border_color = self.ACTIVE_BORDER_COLOR
            else:
                tab_color = self.INACTIVE_TAB_COLOR
                border_color = self.INACTIVE_BORDER_COLOR
            
            # Slight highlight for hover
            if is_hovered and not is_active:
                tab_color = tuple(min(255, c + 15) for c in tab_color)
            
            # Draw tab background
            pygame.draw.rect(surface, tab_color, tab_rect)
            pygame.draw.rect(surface, border_color, tab_rect, 1)
            
            # Tab text (truncated if necessary)
            text_rect = pygame.Rect(tab_rect.x + 8, tab_rect.y, 
                                   tab_rect.width - 20, tab_rect.height)
            tab_text = self._truncate_text(tab.name, text_rect.width)
            text_surface = self.font.render(tab_text, True, self.TEXT_COLOR)
            text_y = tab_rect.y + (tab_rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_rect.x, text_y))
            
            # Close button (small X) - only show if more than one tab
            if len(self.tabs) > 1:
                close_rect = self.get_close_button_rect(i)
                close_color = (self.CLOSE_BUTTON_HOVER_COLOR 
                             if self.hovered_close_button == i 
                             else self.CLOSE_BUTTON_COLOR)
                self._draw_close_button(surface, close_rect, close_color)
    
    def get_tab_rect(self, tab_index: int) -> pygame.Rect:
        """Get the rectangle for a specific tab.
        
        Args:
            tab_index: Index of the tab
            
        Returns:
            Rectangle for the tab
        """
        if not (0 <= tab_index < len(self.tabs)):
            return pygame.Rect(0, 0, 0, 0)
        
        x = self.tab_bar_rect.x + tab_index * (self.tab_width + self.tab_spacing)
        y = self.tab_bar_rect.y
        return pygame.Rect(x, y, self.tab_width, self.tab_height)
    
    def get_close_button_rect(self, tab_index: int) -> pygame.Rect:
        """Get the rectangle for a tab's close button.
        
        Args:
            tab_index: Index of the tab
            
        Returns:
            Rectangle for the close button
        """
        tab_rect = self.get_tab_rect(tab_index)
        close_x = tab_rect.right - self.close_button_size - 4
        close_y = tab_rect.y + (tab_rect.height - self.close_button_size) // 2
        return pygame.Rect(close_x, close_y, self.close_button_size, self.close_button_size)
    
    def handle_click(self, pos: Tuple[int, int]) -> str:
        """Handle mouse clicks in the tab bar.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            Action string: "switch_tab:index", "close_tab:index", or "none"
        """
        if not self.tab_bar_rect.collidepoint(pos):
            return "none"
        
        # Check close buttons first (they have priority)
        for i in range(len(self.tabs)):
            if len(self.tabs) > 1:  # Only check if close buttons are visible
                close_rect = self.get_close_button_rect(i)
                if close_rect.collidepoint(pos):
                    return f"close_tab:{i}"
        
        # Check tab clicks
        for i in range(len(self.tabs)):
            tab_rect = self.get_tab_rect(i)
            if tab_rect.collidepoint(pos):
                return f"switch_tab:{i}"
        
        return "none"
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse motion for hover effects.
        
        Args:
            pos: Mouse position (x, y)
        """
        if not self.tab_bar_rect.collidepoint(pos):
            self.hovered_tab = None
            self.hovered_close_button = None
            return
        
        # Check close button hovers
        self.hovered_close_button = None
        for i in range(len(self.tabs)):
            if len(self.tabs) > 1:  # Only check if close buttons are visible
                close_rect = self.get_close_button_rect(i)
                if close_rect.collidepoint(pos):
                    self.hovered_close_button = i
                    self.hovered_tab = i  # Tab is also hovered
                    return
        
        # Check tab hovers
        self.hovered_tab = None
        for i in range(len(self.tabs)):
            tab_rect = self.get_tab_rect(i)
            if tab_rect.collidepoint(pos):
                self.hovered_tab = i
                return
    
    def process_action(self, action: str) -> bool:
        """Process an action returned from handle_click.
        
        Args:
            action: Action string from handle_click
            
        Returns:
            True if action was processed, False otherwise
        """
        if action.startswith("switch_tab:"):
            tab_index = int(action[11:])  # Remove "switch_tab:" prefix
            return self.switch_to_tab(tab_index)
        
        elif action.startswith("close_tab:"):
            tab_index = int(action[10:])  # Remove "close_tab:" prefix
            return self.close_tab(tab_index)
        
        return False
    
    def _update_tab_layout(self):
        """Update tab layout calculations."""
        # Calculate available width
        available_width = self.tab_bar_rect.width
        
        # Adjust tab width if we have many tabs
        if len(self.tabs) > 0:
            total_spacing = (len(self.tabs) - 1) * self.tab_spacing
            max_tab_width = (available_width - total_spacing) // len(self.tabs)
            self.tab_width = min(120, max(80, max_tab_width))  # Between 80-120 pixels
    
    def _truncate_text(self, text: str, max_width: int) -> str:
        """Truncate text to fit within specified width.
        
        Args:
            text: Text to truncate
            max_width: Maximum width in pixels
            
        Returns:
            Truncated text with ellipsis if needed
        """
        # Quick check if text fits
        text_surface = self.font.render(text, True, self.TEXT_COLOR)
        if text_surface.get_width() <= max_width:
            return text
        
        # Binary search for best fit
        left, right = 0, len(text)
        best_text = ""
        
        while left <= right:
            mid = (left + right) // 2
            test_text = text[:mid] + ("..." if mid < len(text) else "")
            test_surface = self.font.render(test_text, True, self.TEXT_COLOR)
            
            if test_surface.get_width() <= max_width:
                best_text = test_text
                left = mid + 1
            else:
                right = mid - 1
        
        return best_text
    
    def _draw_close_button(self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int]):
        """Draw a close button (X) in the specified rectangle.
        
        Args:
            surface: Surface to draw on
            rect: Rectangle for the close button
            color: Color for the X
        """
        # Draw small X
        center_x, center_y = rect.center
        offset = 3
        
        # X lines
        pygame.draw.line(surface, color, 
                        (center_x - offset, center_y - offset),
                        (center_x + offset, center_y + offset), 2)
        pygame.draw.line(surface, color,
                        (center_x + offset, center_y - offset),
                        (center_x - offset, center_y + offset), 2)
    
    def set_tab_spritesheet(self, tab_index: int, spritesheet_object):
        """Set the spritesheet object for a specific tab.
        
        Args:
            tab_index: Index of the tab
            spritesheet_object: Loaded spritesheet object
        """
        if 0 <= tab_index < len(self.tabs):
            self.tabs[tab_index].spritesheet = spritesheet_object
            self.tabs[tab_index].is_loaded = True
    
    def set_tab_animation(self, tab_index: int, animation_entry):
        """Set the current animation for a specific tab.
        
        Args:
            tab_index: Index of the tab
            animation_entry: AnimationEntry object
        """
        if 0 <= tab_index < len(self.tabs):
            self.tabs[tab_index].current_animation = animation_entry
    
    def get_tab_info(self) -> List[Dict[str, any]]:
        """Get information about all tabs for debugging/display.
        
        Returns:
            List of dictionaries with tab information
        """
        return [
            {
                "index": i,
                "name": tab.name,
                "path": tab.spritesheet_path,
                "is_active": i == self.active_tab_index,
                "is_loaded": tab.is_loaded,
                "has_animation": tab.current_animation is not None
            }
            for i, tab in enumerate(self.tabs)
        ]


# Test function for development
def test_tab_manager():
    """Test function for the tab manager."""
    pygame.init()
    screen = pygame.display.set_mode((800, 100))
    pygame.display.set_caption("Tab Manager Test")
    clock = pygame.time.Clock()
    
    # Create tab manager
    tab_bar_rect = pygame.Rect(10, 10, 780, 30)
    tab_manager = TabManager(tab_bar_rect)
    
    # Add some test tabs
    tab_manager.add_tab(r"c:\Users\Michael\Documents\Test Games\Walk_GhCp_Test\Assests\Sword Master Sprite Sheet 90x37.png", "Player Sprites")
    tab_manager.add_tab(r"c:\test\enemy_sprites.png", "Enemy Sprites")
    tab_manager.add_tab(r"c:\test\background_tiles.png", "Background")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                tab_manager.handle_mouse_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    action = tab_manager.handle_click(event.pos)
                    tab_manager.process_action(action)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Add a new test tab
                    tab_manager.add_tab(f"c:\\test\\sprites_{len(tab_manager.tabs)}.png", f"Test {len(tab_manager.tabs)}")
        
        # Clear screen
        screen.fill((30, 30, 30))
        
        # Render tabs
        tab_manager.render_tabs(screen)
        
        # Show tab info
        font = pygame.font.Font(None, 16)
        info_text = f"Active: {tab_manager.active_tab_index} | Tabs: {tab_manager.get_tab_count()} | Press SPACE to add tab"
        info_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(info_surface, (10, 50))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    test_tab_manager()
