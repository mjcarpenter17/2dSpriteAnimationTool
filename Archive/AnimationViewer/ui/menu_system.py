"""
Menu system for the sprite animation tool.
"""
import pygame
from typing import Dict, List, Callable, Optional, Tuple, Any


class MenuItem:
    """A single menu item."""
    
    def __init__(self, text: str, action: Optional[Callable] = None, 
                 shortcut: str = "", submenu: Optional['Menu'] = None, 
                 enabled: bool = True, separator: bool = False):
        """Initialize a menu item."""
        self.text = text
        self.action = action
        self.shortcut = shortcut
        self.submenu = submenu
        self.enabled = enabled
        self.separator = separator
        self.rect: Optional[pygame.Rect] = None
        self.hovered = False
    
    def execute(self):
        """Execute the menu item's action."""
        if self.enabled and self.action:
            self.action()


class Menu:
    """A menu with items."""
    
    def __init__(self, items: List[MenuItem]):
        """Initialize a menu."""
        self.items = items
        self.rect: Optional[pygame.Rect] = None
        self.visible = False
        self.font = None
        self.selected_index = -1
        
        # Colors
        self.bg_color = (240, 240, 240)
        self.border_color = (180, 180, 180)
        self.text_color = (50, 50, 50)
        self.disabled_color = (150, 150, 150)
        self.hover_color = (200, 220, 240)
        self.separator_color = (200, 200, 200)
    
    def show_at(self, x: int, y: int):
        """Show the menu at the specified position."""
        self.visible = True
        self.calculate_size()
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        # Ensure font is initialized
        if not self.font:
            try:
                self.font = pygame.font.SysFont("Arial", 12)
            except:
                self.font = pygame.font.Font(None, 16)
    
    def hide(self):
        """Hide the menu."""
        self.visible = False
        self.selected_index = -1
    
    def calculate_size(self):
        """Calculate menu size based on items."""
        if not self.font:
            try:
                self.font = pygame.font.SysFont("Arial", 12)
            except:
                self.font = pygame.font.Font(None, 16)
        
        max_width = 0
        height = 0
        
        for item in self.items:
            if item.separator:
                height += 5
            else:
                text_width = self.font.size(item.text)[0]
                shortcut_width = self.font.size(item.shortcut)[0] if item.shortcut else 0
                item_width = text_width + shortcut_width + 60  # Padding
                max_width = max(max_width, item_width)
                height += 25
        
        self.width = max(150, max_width)
        self.height = height + 4  # Border padding
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for the menu."""
        if not self.visible or not self.rect:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                # Calculate which item is hovered
                relative_y = event.pos[1] - self.rect.y - 2
                item_index = 0
                y_offset = 0
                
                for i, item in enumerate(self.items):
                    if item.separator:
                        y_offset += 5
                    else:
                        if y_offset <= relative_y < y_offset + 25:
                            self.selected_index = i
                            break
                        y_offset += 25
                else:
                    self.selected_index = -1
                return True
            else:
                self.selected_index = -1
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.rect.collidepoint(event.pos):
                    if 0 <= self.selected_index < len(self.items):
                        item = self.items[self.selected_index]
                        if not item.separator and item.enabled:
                            item.execute()
                            self.hide()
                    return True
                else:
                    # Click outside menu - hide it
                    self.hide()
                    return False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
        
        return False
    
    def render(self, surface: pygame.Surface):
        """Render the menu."""
        if not self.visible or not self.rect:
            return
        
        # Draw menu background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)
        
        # Draw menu items
        y_offset = self.rect.y + 2
        for i, item in enumerate(self.items):
            if item.separator:
                # Draw separator line
                sep_y = y_offset + 2
                pygame.draw.line(surface, self.separator_color,
                               (self.rect.x + 5, sep_y),
                               (self.rect.right - 5, sep_y))
                y_offset += 5
            else:
                # Draw menu item
                item_rect = pygame.Rect(self.rect.x + 1, y_offset, 
                                       self.rect.width - 2, 25)
                
                # Highlight if selected
                if i == self.selected_index:
                    pygame.draw.rect(surface, self.hover_color, item_rect)
                
                # Choose text color
                text_color = self.text_color if item.enabled else self.disabled_color
                
                # Draw item text
                text_surface = self.font.render(item.text, True, text_color)
                surface.blit(text_surface, (item_rect.x + 8, item_rect.y + 4))
                
                # Draw shortcut if exists
                if item.shortcut:
                    shortcut_surface = self.font.render(item.shortcut, True, text_color)
                    shortcut_x = item_rect.right - shortcut_surface.get_width() - 8
                    surface.blit(shortcut_surface, (shortcut_x, item_rect.y + 4))
                
                # Draw submenu arrow if exists
                if item.submenu:
                    arrow_x = item_rect.right - 15
                    arrow_y = item_rect.y + 12
                    pygame.draw.polygon(surface, text_color, [
                        (arrow_x, arrow_y - 4),
                        (arrow_x + 6, arrow_y),
                        (arrow_x, arrow_y + 4)
                    ])
                
                y_offset += 25


class MenuBar:
    """Main menu bar for the application."""
    
    def __init__(self, height: int = 25):
        """Initialize the menu bar."""
        self.height = height
        self.menus: Dict[str, Menu] = {}
        self.menu_titles: List[str] = []
        self.menu_rects: Dict[str, pygame.Rect] = {}
        self.active_menu: Optional[str] = None
        self.hovered_menu: Optional[str] = None
        
        # Colors
        self.bg_color = (245, 245, 245)
        self.border_color = (200, 200, 200)
        self.text_color = (50, 50, 50)
        self.hover_color = (225, 225, 225)
        self.active_color = (200, 220, 240)
        
        # Font
        try:
            self.font = pygame.font.SysFont("Arial", 12)
        except:
            self.font = pygame.font.Font(None, 16)
    
    def add_menu(self, title: str, menu: Menu):
        """Add a menu to the menu bar."""
        self.menus[title] = menu
        if title not in self.menu_titles:
            self.menu_titles.append(title)
    
    def calculate_layout(self, window_width: int):
        """Calculate the layout of menu items."""
        x_offset = 5
        
        for title in self.menu_titles:
            text_width = self.font.size(title)[0]
            menu_width = text_width + 20  # Padding
            
            self.menu_rects[title] = pygame.Rect(x_offset, 0, menu_width, self.height)
            x_offset += menu_width
    
    def handle_event(self, event: pygame.event.Event, window_width: int) -> bool:
        """Handle events for the menu bar."""
        self.calculate_layout(window_width)
        
        # First, let active menu handle events
        if self.active_menu and self.active_menu in self.menus:
            if self.menus[self.active_menu].handle_event(event):
                return True
            
            # If menu became invisible, clear active menu
            if not self.menus[self.active_menu].visible:
                self.active_menu = None
        
        if event.type == pygame.MOUSEMOTION:
            # Update hover state
            self.hovered_menu = None
            for title, rect in self.menu_rects.items():
                if rect.collidepoint(event.pos):
                    self.hovered_menu = title
                    break
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicked on menu bar
                for title, rect in self.menu_rects.items():
                    if rect.collidepoint(event.pos):
                        if self.active_menu == title:
                            # Close active menu
                            self.menus[title].hide()
                            self.active_menu = None
                        else:
                            # Open new menu
                            if self.active_menu:
                                self.menus[self.active_menu].hide()
                            
                            self.menus[title].show_at(rect.x, rect.bottom)
                            self.active_menu = title
                        return True
                
                # If clicked outside menu bar and no active menu handled it,
                # close any active menu
                if self.active_menu:
                    self.menus[self.active_menu].hide()
                    self.active_menu = None
        
        return False
    
    def render(self, surface: pygame.Surface, window_width: int):
        """Render the menu bar."""
        self.calculate_layout(window_width)
        
        # Draw menu bar background
        menu_rect = pygame.Rect(0, 0, window_width, self.height)
        pygame.draw.rect(surface, self.bg_color, menu_rect)
        pygame.draw.line(surface, self.border_color, 
                        (0, self.height - 1), (window_width, self.height - 1))
        
        # Draw menu titles
        for title in self.menu_titles:
            rect = self.menu_rects[title]
            
            # Highlight if hovered or active
            if title == self.active_menu:
                pygame.draw.rect(surface, self.active_color, rect)
            elif title == self.hovered_menu:
                pygame.draw.rect(surface, self.hover_color, rect)
            
            # Draw title text
            text_surface = self.font.render(title, True, self.text_color)
            text_x = rect.x + (rect.width - text_surface.get_width()) // 2
            text_y = rect.y + (rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))
        
        # Render active menu
        if self.active_menu and self.active_menu in self.menus:
            self.menus[self.active_menu].render(surface)
