"""
Base panel class for the sprite animation tool UI panels.
"""
import pygame
from typing import Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod


class Panel(ABC):
    """
    Base class for UI panels in the sprite animation tool.
    
    Provides common functionality for resizable panels with proper
    event handling and rendering.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        """Initialize the panel."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        
        # Panel state
        self.visible = True
        self.resizable = True
        self.min_width = 200
        self.min_height = 100
        
        # Colors and styling
        self.bg_color = (240, 240, 240)
        self.border_color = (180, 180, 180)
        self.title_bg_color = (220, 220, 220)
        self.text_color = (50, 50, 50)
        
        # Fonts
        try:
            self.font = pygame.font.SysFont("Arial", 12)
            self.title_font = pygame.font.SysFont("Arial", 12, bold=True)
        except:
            self.font = pygame.font.Font(None, 16)
            self.title_font = pygame.font.Font(None, 16)
    
    def get_rect(self) -> pygame.Rect:
        """Get the panel's rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_content_rect(self) -> pygame.Rect:
        """Get the content area rectangle (excluding title bar)."""
        title_height = 25 if self.title else 0
        return pygame.Rect(
            self.x + 2, 
            self.y + title_height + 2, 
            self.width - 4, 
            self.height - title_height - 4
        )
    
    def resize(self, width: int, height: int):
        """Resize the panel."""
        if self.resizable:
            self.width = max(width, self.min_width)
            self.height = max(height, self.min_height)
    
    def move(self, x: int, y: int):
        """Move the panel to a new position."""
        self.x = x
        self.y = y
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within the panel."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a pygame event.
        
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if not self.visible:
            return False
            
        # Override in subclasses for specific event handling
        return False
    
    def render(self, surface: pygame.Surface):
        """Render the panel to the surface."""
        if not self.visible:
            return
            
        # Draw panel background
        pygame.draw.rect(surface, self.bg_color, self.get_rect())
        pygame.draw.rect(surface, self.border_color, self.get_rect(), 1)
        
        # Draw title bar if title exists
        if self.title:
            title_rect = pygame.Rect(self.x, self.y, self.width, 25)
            pygame.draw.rect(surface, self.title_bg_color, title_rect)
            pygame.draw.line(surface, self.border_color, 
                           (self.x, self.y + 25), (self.x + self.width, self.y + 25))
            
            # Render title text
            title_surface = self.title_font.render(self.title, True, self.text_color)
            surface.blit(title_surface, (self.x + 8, self.y + 6))
        
        # Render panel content
        self.render_content(surface)
    
    @abstractmethod
    def render_content(self, surface: pygame.Surface):
        """Render the panel's content. Override in subclasses."""
        pass
    
    def update(self, dt: float):
        """Update the panel. Override in subclasses if needed."""
        pass


class SplitterHandle:
    """
    A splitter handle for resizing panels.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, vertical: bool = True):
        """Initialize the splitter handle."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vertical = vertical  # True for vertical splitter (resize horizontally)
        
        self.dragging = False
        self.drag_offset = 0
        
        # Colors
        self.color = (200, 200, 200)
        self.hover_color = (180, 180, 180)
        self.drag_color = (160, 160, 160)
        
        # Cursor states
        self.hovered = False
    
    def get_rect(self) -> pygame.Rect:
        """Get the splitter's rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within the splitter."""
        return self.get_rect().collidepoint(x, y)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the splitter."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains_point(event.pos[0], event.pos[1])
            
            if self.dragging:
                if self.vertical:
                    self.x = event.pos[0] - self.drag_offset
                else:
                    self.y = event.pos[1] - self.drag_offset
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos[0], event.pos[1]):
                self.dragging = True
                if self.vertical:
                    self.drag_offset = event.pos[0] - self.x
                else:
                    self.drag_offset = event.pos[1] - self.y
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                self.dragging = False
                return True
        
        return False
    
    def render(self, surface: pygame.Surface):
        """Render the splitter handle."""
        if self.dragging:
            color = self.drag_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color
            
        pygame.draw.rect(surface, color, self.get_rect())
        
        # Draw splitter lines
        if self.vertical:
            center_x = self.x + self.width // 2
            pygame.draw.line(surface, (160, 160, 160), 
                           (center_x - 1, self.y + 10), 
                           (center_x - 1, self.y + self.height - 10))
            pygame.draw.line(surface, (160, 160, 160), 
                           (center_x + 1, self.y + 10), 
                           (center_x + 1, self.y + self.height - 10))
        else:
            center_y = self.y + self.height // 2
            pygame.draw.line(surface, (160, 160, 160), 
                           (self.x + 10, center_y - 1), 
                           (self.x + self.width - 10, center_y - 1))
            pygame.draw.line(surface, (160, 160, 160), 
                           (self.x + 10, center_y + 1), 
                           (self.x + self.width - 10, center_y + 1))
    
    def get_cursor_type(self) -> str:
        """Get the appropriate cursor type for this splitter."""
        if self.vertical:
            return "resize_horizontal"
        else:
            return "resize_vertical"
