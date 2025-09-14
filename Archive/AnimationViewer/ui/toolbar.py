"""
Toolbar implementation for the Sprite Animation Tool.
Provides quick access to commonly used functions with icon-based buttons.
"""

import pygame
import os
from typing import Dict, List, Tuple, Optional, Callable

class ToolbarButton:
    """Individual toolbar button with icon, tooltip, and callback."""
    
    def __init__(self, icon_name: str, tooltip: str, callback: Callable, 
                 shortcut: str = "", enabled: bool = True, toggle: bool = False):
        self.icon_name = icon_name
        self.tooltip = tooltip
        self.callback = callback
        self.shortcut = shortcut
        self.enabled = enabled
        self.toggle = toggle
        self.active = False
        self.hovered = False
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.icon_surface = None
        self._load_icon()
    
    def _load_icon(self):
        """Load or create icon surface for the button."""
        # Create a larger icon surface for better detail
        self.icon_surface = pygame.Surface((24, 24))
        self.icon_surface.fill((255, 255, 255))  # White background
        
        # Create recognizable icons with clear visual metaphors
        if self.icon_name == 'open':
            # Folder icon - yellow folder with white interior
            pygame.draw.rect(self.icon_surface, (255, 215, 0), (4, 8, 16, 12))  # Folder body
            pygame.draw.rect(self.icon_surface, (255, 235, 59), (4, 8, 6, 3))   # Folder tab
            pygame.draw.rect(self.icon_surface, (255, 255, 255), (6, 10, 12, 8)) # Interior
            pygame.draw.rect(self.icon_surface, (0, 0, 0), (4, 8, 16, 12), 2)   # Outline
            
        elif self.icon_name == 'save':
            # Floppy disk icon - classic save symbol
            pygame.draw.rect(self.icon_surface, (100, 100, 100), (5, 5, 14, 14)) # Disk body
            pygame.draw.rect(self.icon_surface, (200, 200, 200), (6, 6, 12, 12)) # Disk surface
            pygame.draw.rect(self.icon_surface, (100, 100, 100), (7, 5, 10, 4))  # Metal slider
            pygame.draw.rect(self.icon_surface, (255, 255, 255), (8, 6, 8, 2))   # Label area
            pygame.draw.rect(self.icon_surface, (0, 0, 0), (5, 5, 14, 14), 2)    # Outline
            
        elif self.icon_name == 'recent':
            # Clock icon for recent files
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (12, 12), 9)
            pygame.draw.circle(self.icon_surface, (0, 0, 0), (12, 12), 9, 2)
            # Clock hands
            pygame.draw.line(self.icon_surface, (0, 0, 0), (12, 12), (12, 7), 2)  # Hour hand
            pygame.draw.line(self.icon_surface, (0, 0, 0), (12, 12), (16, 9), 2)  # Minute hand
            pygame.draw.circle(self.icon_surface, (0, 0, 0), (12, 12), 2)
            
        elif self.icon_name == 'select_all':
            # Selection box with checkmark
            pygame.draw.rect(self.icon_surface, (255, 255, 255), (5, 5, 14, 14))
            pygame.draw.rect(self.icon_surface, (0, 100, 0), (5, 5, 14, 14), 2)
            # Checkmark
            pygame.draw.line(self.icon_surface, (0, 150, 0), (8, 12), (11, 15), 2)
            pygame.draw.line(self.icon_surface, (0, 150, 0), (11, 15), (16, 8), 2)
            
        elif self.icon_name == 'clear':
            # X mark for clear selection
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (12, 12), 10)
            pygame.draw.circle(self.icon_surface, (220, 50, 50), (12, 12), 10, 2)
            pygame.draw.line(self.icon_surface, (220, 50, 50), (8, 8), (16, 16), 3)
            pygame.draw.line(self.icon_surface, (220, 50, 50), (16, 8), (8, 16), 3)
            
        elif self.icon_name == 'grid':
            # Grid pattern - clear grid lines
            pygame.draw.rect(self.icon_surface, (255, 255, 255), (4, 4, 16, 16))
            for i in range(4, 21, 4):
                pygame.draw.line(self.icon_surface, (150, 150, 150), (i, 4), (i, 20), 1)
                pygame.draw.line(self.icon_surface, (150, 150, 150), (4, i), (20, i), 1)
            pygame.draw.rect(self.icon_surface, (0, 0, 0), (4, 4, 16, 16), 2)
            
        elif self.icon_name == 'analysis':
            # Magnifying glass with gear/analysis symbol
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (10, 10), 7)
            pygame.draw.circle(self.icon_surface, (100, 149, 237), (10, 10), 7, 2)
            pygame.draw.line(self.icon_surface, (100, 149, 237), (15, 15), (20, 20), 3)
            # Analysis symbol inside
            pygame.draw.circle(self.icon_surface, (100, 149, 237), (10, 10), 3, 2)
            pygame.draw.line(self.icon_surface, (100, 149, 237), (8, 10), (12, 10), 1)
            pygame.draw.line(self.icon_surface, (100, 149, 237), (10, 8), (10, 12), 1)
            
        elif self.icon_name == 'zoom_in':
            # Magnifying glass with plus sign
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (10, 10), 7)
            pygame.draw.circle(self.icon_surface, (34, 139, 34), (10, 10), 7, 2)
            pygame.draw.line(self.icon_surface, (34, 139, 34), (15, 15), (20, 20), 3)
            # Plus sign
            pygame.draw.line(self.icon_surface, (34, 139, 34), (8, 10), (12, 10), 2)
            pygame.draw.line(self.icon_surface, (34, 139, 34), (10, 8), (10, 12), 2)
            
        elif self.icon_name == 'zoom_out':
            # Magnifying glass with minus sign
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (10, 10), 7)
            pygame.draw.circle(self.icon_surface, (178, 34, 34), (10, 10), 7, 2)
            pygame.draw.line(self.icon_surface, (178, 34, 34), (15, 15), (20, 20), 3)
            # Minus sign
            pygame.draw.line(self.icon_surface, (178, 34, 34), (8, 10), (12, 10), 2)
            
        elif self.icon_name == 'new_animation':
            # Film strip icon
            pygame.draw.rect(self.icon_surface, (50, 50, 50), (4, 7, 16, 10))
            pygame.draw.rect(self.icon_surface, (200, 200, 200), (6, 9, 12, 6))
            # Film perforations
            for i in range(5, 19, 3):
                pygame.draw.rect(self.icon_surface, (0, 0, 0), (i, 8, 1, 1))
                pygame.draw.rect(self.icon_surface, (0, 0, 0), (i, 15, 1, 1))
            # Play button overlay
            pygame.draw.polygon(self.icon_surface, (50, 205, 50), [(9, 10), (9, 14), (13, 12)])
            
        elif self.icon_name == 'refresh':
            # Circular arrow (refresh symbol)
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (12, 12), 9)
            pygame.draw.circle(self.icon_surface, (30, 144, 255), (12, 12), 9, 2)
            # Arrow path
            pygame.draw.arc(self.icon_surface, (30, 144, 255), (6, 6, 12, 12), 0, 4.7, 2)
            # Arrow head
            pygame.draw.polygon(self.icon_surface, (30, 144, 255), [(18, 8), (16, 6), (18, 10)])
        
        else:
            # Default icon - question mark
            pygame.draw.circle(self.icon_surface, (200, 200, 200), (12, 12), 10)
            pygame.draw.circle(self.icon_surface, (100, 100, 100), (12, 12), 10, 2)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the button."""
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                self.callback()
                return True
        
        return False
    
    def render(self, surface: pygame.Surface):
        """Render the toolbar button."""
        # Button background
        if not self.enabled:
            bg_color = (240, 240, 240)
        elif self.active:
            bg_color = (200, 200, 255)
        elif self.hovered:
            bg_color = (220, 220, 220)
        else:
            bg_color = (250, 250, 250)
        
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (128, 128, 128), self.rect, 1)
        
        # Icon
        if self.icon_surface:
            icon_x = self.rect.x + (self.rect.width - 24) // 2
            icon_y = self.rect.y + (self.rect.height - 24) // 2
            if not self.enabled:
                # Gray out disabled icons
                gray_icon = self.icon_surface.copy()
                gray_icon.fill((128, 128, 128, 128), special_flags=pygame.BLEND_MULT)
                surface.blit(gray_icon, (icon_x, icon_y))
            else:
                surface.blit(self.icon_surface, (icon_x, icon_y))


class ToolbarSeparator:
    """Visual separator between toolbar button groups."""
    
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 8, 32)
    
    def render(self, surface: pygame.Surface):
        """Render the separator line."""
        line_x = self.rect.x + self.rect.width // 2
        pygame.draw.line(surface, (180, 180, 180), 
                        (line_x, self.rect.y + 4), 
                        (line_x, self.rect.bottom - 4))


class Toolbar:
    """Main toolbar with grouped buttons and separators."""
    
    def __init__(self, height: int = 40):
        self.height = height
        self.rect = pygame.Rect(0, 0, 0, height)
        self.buttons: List[ToolbarButton] = []
        self.separators: List[ToolbarSeparator] = []
        self.items: List = []  # Mixed list of buttons and separators
        self.background_color = (245, 245, 245)
        self.font = pygame.font.Font(None, 14)
        self.tooltip_visible = False
        self.tooltip_text = ""
        self.tooltip_pos = (0, 0)
        self.tooltip_timer = 0
        self.tooltip_delay = 500  # milliseconds
        
    def add_button(self, icon_name: str, tooltip: str, callback: Callable,
                   shortcut: str = "", enabled: bool = True, toggle: bool = False) -> ToolbarButton:
        """Add a button to the toolbar."""
        button = ToolbarButton(icon_name, tooltip, callback, shortcut, enabled, toggle)
        self.buttons.append(button)
        self.items.append(button)
        self._update_layout()
        return button
    
    def add_separator(self):
        """Add a visual separator to the toolbar."""
        separator = ToolbarSeparator()
        self.separators.append(separator)
        self.items.append(separator)
        self._update_layout()
    
    def _update_layout(self):
        """Update the layout of toolbar items."""
        x = 8  # Start padding
        for item in self.items:
            item.rect.x = x
            item.rect.y = (self.height - item.rect.height) // 2
            x += item.rect.width + 2
    
    def set_button_state(self, icon_name: str, enabled: bool = None, active: bool = None):
        """Update button state by icon name."""
        for button in self.buttons:
            if button.icon_name == icon_name:
                if enabled is not None:
                    button.enabled = enabled
                if active is not None and button.toggle:
                    button.active = active
                break
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for all toolbar items."""
        # Handle tooltip timing
        if event.type == pygame.MOUSEMOTION:
            self.tooltip_timer = pygame.time.get_ticks()
            self.tooltip_visible = False
            
            # Check if hovering over any button
            for button in self.buttons:
                if button.rect.collidepoint(event.pos) and button.enabled:
                    self.tooltip_text = button.tooltip
                    if button.shortcut:
                        self.tooltip_text += f" ({button.shortcut})"
                    self.tooltip_pos = (event.pos[0], event.pos[1] + 20)
                    break
            else:
                self.tooltip_text = ""
        
        # Handle button events
        for button in self.buttons:
            if button.handle_event(event):
                return True
        
        return False
    
    def update(self):
        """Update toolbar state (tooltips, animations, etc.)."""
        # Show tooltip after delay
        if (self.tooltip_text and not self.tooltip_visible and 
            pygame.time.get_ticks() - self.tooltip_timer > self.tooltip_delay):
            self.tooltip_visible = True
    
    def render(self, surface: pygame.Surface):
        """Render the complete toolbar."""
        # Background
        pygame.draw.rect(surface, self.background_color, self.rect)
        pygame.draw.line(surface, (200, 200, 200), 
                        (self.rect.left, self.rect.bottom - 1), 
                        (self.rect.right, self.rect.bottom - 1))
        
        # Render all items
        for item in self.items:
            item.render(surface)
        
        # Render tooltip
        if self.tooltip_visible and self.tooltip_text:
            self._render_tooltip(surface)
    
    def _render_tooltip(self, surface: pygame.Surface):
        """Render the tooltip popup."""
        if not self.tooltip_text:
            return
            
        # Create tooltip surface
        text_surface = self.font.render(self.tooltip_text, True, (0, 0, 0))
        padding = 4
        tooltip_width = text_surface.get_width() + padding * 2
        tooltip_height = text_surface.get_height() + padding * 2
        
        # Position tooltip (avoid screen edges)
        x, y = self.tooltip_pos
        screen_rect = surface.get_rect()
        if x + tooltip_width > screen_rect.right:
            x = screen_rect.right - tooltip_width
        if y + tooltip_height > screen_rect.bottom:
            y = self.tooltip_pos[1] - tooltip_height - 20
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(x, y, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, (255, 255, 225), tooltip_rect)
        pygame.draw.rect(surface, (128, 128, 128), tooltip_rect, 1)
        
        # Draw tooltip text
        text_x = x + padding
        text_y = y + padding
        surface.blit(text_surface, (text_x, text_y))
    
    def resize(self, width: int):
        """Update toolbar width."""
        self.rect.width = width
