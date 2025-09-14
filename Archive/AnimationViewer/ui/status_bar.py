"""
Comprehensive status bar component for the sprite animation tool.
This implements Phase 1.9 Status Bar and User Feedback with real-time information display.
"""
import pygame
import psutil
import os
from typing import Optional, Dict, Any, Tuple, List
import time
import threading


class StatusSection:
    """Individual section of the status bar."""
    
    def __init__(self, name: str, min_width: int = 100, max_width: int = 300):
        self.name = name
        self.text = ""
        self.min_width = min_width
        self.max_width = max_width
        self.rect = pygame.Rect(0, 0, min_width, 25)
        self.visible = True
        self.clickable = False
        self.callback = None
    
    def set_text(self, text: str):
        """Set the text for this section."""
        self.text = text
    
    def set_clickable(self, callback):
        """Make this section clickable with a callback."""
        self.clickable = True
        self.callback = callback


class StatusBar:
    """
    Comprehensive status bar with multiple information sections and real-time updates.
    """
    
    def __init__(self, height: int = 25):
        """Initialize the comprehensive status bar."""
        self.height = height
        self.rect = pygame.Rect(0, 0, 0, height)
        
        # Status sections
        self.sections = {}
        self._setup_sections()
        
        # Temporary messages
        self.temp_message = ""
        self.temp_message_time = 0
        self.temp_message_duration = 3.0
        self.temp_message_color = (70, 70, 70)
        
        # Operation progress
        self.operation_text = ""
        self.progress_value = 0.0  # 0.0 to 1.0
        self.show_progress = False
        self.progress_color = (100, 150, 200)
        
        # Memory monitoring
        self.memory_usage_mb = 0
        self.memory_update_time = 0
        self.memory_update_interval = 2.0  # seconds
        
        # Status tracking attributes
        self.sprite_sheet_name = ""
        self.tile_count = 0
        self.selected_count = 0
        self.total_frames = None
        self.mouse_pos = (0, 0)
        self.frame_pos = None
        self.frame_index = None
        self.current_frame_info = ""
        
        # Colors and styling
        self.bg_color = (248, 248, 248)
        self.border_color = (200, 200, 200)
        self.text_color = (70, 70, 70)
        self.separator_color = (220, 220, 220)
        self.highlight_color = (240, 240, 240)
        
        # Message type colors
        self.info_color = (70, 70, 70)
        self.success_color = (46, 125, 50)
        self.warning_color = (245, 124, 0)
        self.error_color = (211, 47, 47)
        
        # Fonts
        try:
            self.font = pygame.font.SysFont("Segoe UI", 9)
            self.bold_font = pygame.font.SysFont("Segoe UI", 9, bold=True)
        except:
            self.font = pygame.font.Font(None, 12)
            self.bold_font = pygame.font.Font(None, 12)
        
        # Animation for smooth updates
        self.last_update_time = time.time()
    
    def _setup_sections(self):
        """Set up the status bar sections."""
        # Main status section (left side)
        self.sections["main"] = StatusSection("main", 200, 400)
        
        # Sprite sheet info
        self.sections["sheet_info"] = StatusSection("sheet_info", 150, 300)
        
        # Selection info
        self.sections["selection"] = StatusSection("selection", 100, 200)
        
        # Mouse/Frame info
        self.sections["mouse_info"] = StatusSection("mouse_info", 120, 250)
        
        # Operation status
        self.sections["operation"] = StatusSection("operation", 100, 250)
        
        # Memory usage (right side)
        self.sections["memory"] = StatusSection("memory", 80, 120)
        
        # Current time (rightmost)
        self.sections["time"] = StatusSection("time", 60, 80)
    
    def set_sprite_sheet_info(self, name: str, tile_count: int, dimensions: Tuple[int, int] = None):
        """Set sprite sheet information."""
        if dimensions:
            info_text = f"Sheet: {name} ({tile_count} tiles, {dimensions[0]}x{dimensions[1]})"
        else:
            info_text = f"Sheet: {name} ({tile_count} tiles)"
        
        self.sections["sheet_info"].set_text(info_text)
    
    def set_selection_info(self, selected_count: int, total_frames: int = None):
        """Set frame selection information."""
        if total_frames and total_frames > 0:
            percentage = (selected_count / total_frames) * 100
            text = f"Selected: {selected_count}/{total_frames} ({percentage:.1f}%)"
        else:
            text = f"Selected: {selected_count} frames"
        
        self.sections["selection"].set_text(text)
    
    def set_mouse_info(self, mouse_pos: Tuple[int, int], frame_pos: Tuple[int, int] = None, 
                       frame_index: int = None):
        """Set mouse position and current frame information."""
        if frame_pos is not None:
            if frame_index is not None:
                text = f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]}) | Frame: ({frame_pos[0]}, {frame_pos[1]}) #{frame_index}"
            else:
                text = f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]}) | Frame: ({frame_pos[0]}, {frame_pos[1]})"
        else:
            text = f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]})"
        
        self.sections["mouse_info"].set_text(text)
    
    def set_operation_status(self, operation: str, details: str = ""):
        """Set current operation status."""
        if details:
            text = f"{operation}: {details}"
        else:
            text = operation
        
        self.sections["operation"].set_text(text)
    
    def clear_operation_status(self):
        """Clear the operation status."""
        self.sections["operation"].set_text("")
    
    def show_progress(self, operation: str, progress: float):
        """Show progress bar for long operations."""
        self.operation_text = operation
        self.progress_value = max(0.0, min(1.0, progress))
        self.show_progress = True
    
    def hide_progress(self):
        """Hide the progress bar."""
        self.show_progress = False
        self.operation_text = ""
        self.progress_value = 0.0
    
    def show_temporary_message(self, message: str, duration: float = 3.0, 
                             message_type: str = "info"):
        """Show a temporary message with type-based coloring."""
        self.temp_message = message
        self.temp_message_time = time.time()
        self.temp_message_duration = duration
        
        # Set color based on message type
        color_map = {
            "info": self.info_color,
            "success": self.success_color,
            "warning": self.warning_color,
            "error": self.error_color
        }
        self.temp_message_color = color_map.get(message_type, self.info_color)
    
    def show_info(self, message: str):
        """Show an info message."""
        self.show_temporary_message(message, 2.0, "info")
    
    def show_success(self, message: str):
        """Show a success message."""
        self.show_temporary_message(message, 3.0, "success")
    
    def show_warning(self, message: str):
        """Show a warning message."""
        self.show_temporary_message(message, 4.0, "warning")
    
    def show_error(self, message: str):
        """Show an error message."""
        self.show_temporary_message(message, 5.0, "error")
    
    def update_memory_usage(self):
        """Update memory usage information."""
        current_time = time.time()
        if current_time - self.memory_update_time > self.memory_update_interval:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                self.memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                
                # Format memory usage
                if self.memory_usage_mb > 1024:
                    memory_text = f"Mem: {self.memory_usage_mb/1024:.1f}GB"
                else:
                    memory_text = f"Mem: {self.memory_usage_mb:.0f}MB"
                
                self.sections["memory"].set_text(memory_text)
                self.memory_update_time = current_time
                
            except Exception:
                self.sections["memory"].set_text("Mem: N/A")
    
    def update_time_display(self):
        """Update the current time display."""
        current_time = time.strftime("%H:%M:%S")
        self.sections["time"].set_text(current_time)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for clickable sections."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for section in self.sections.values():
                if section.clickable and section.rect.collidepoint(event.pos):
                    if section.callback:
                        section.callback()
                    return True
        return False
    
    def update(self):
        """Update status bar state and animations."""
        self.update_memory_usage()
        self.update_time_display()
        
        # Clear expired temporary messages
        if (self.temp_message and 
            time.time() - self.temp_message_time > self.temp_message_duration):
            self.temp_message = ""
    
    def resize(self, width: int):
        """Resize the status bar to fit the window width."""
        self.rect.width = width
        self._layout_sections()
    
    def _layout_sections(self):
        """Layout the sections within the status bar."""
        available_width = self.rect.width - 20  # Padding
        section_padding = 10
        
        # Calculate positions from left to right
        x = 10
        
        # Left side sections
        left_sections = ["sheet_info", "selection", "mouse_info", "operation"]
        for section_name in left_sections:
            if section_name in self.sections:
                section = self.sections[section_name]
                if section.visible and section.text:
                    text_width = self.font.size(section.text)[0]
                    section_width = min(max(text_width + 10, section.min_width), section.max_width)
                    section.rect = pygame.Rect(x, self.rect.y + 2, section_width, self.height - 4)
                    x += section_width + section_padding
        
        # Right side sections (from right to left)
        right_sections = ["time", "memory"]
        right_x = self.rect.width - 10
        
        for section_name in reversed(right_sections):
            if section_name in self.sections:
                section = self.sections[section_name]
                if section.visible:
                    text_width = self.font.size(section.text)[0] if section.text else 0
                    section_width = min(max(text_width + 10, section.min_width), section.max_width)
                    right_x -= section_width
                    section.rect = pygame.Rect(right_x, self.rect.y + 2, section_width, self.height - 4)
                    right_x -= section_padding
        
        # Main section takes remaining space
        if "main" in self.sections:
            main_width = max(100, right_x - x - section_padding)
            self.sections["main"].rect = pygame.Rect(x, self.rect.y + 2, main_width, self.height - 4)
    
    def render(self, surface: pygame.Surface):
        """Render the comprehensive status bar."""
        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.line(surface, self.border_color, 
                        (self.rect.left, self.rect.top), 
                        (self.rect.right, self.rect.top))
        
        # Layout sections
        self._layout_sections()
        
        # Render progress bar if active
        if self.show_progress:
            self._render_progress_bar(surface)
        
        # Render temporary message if active
        elif self.temp_message:
            self._render_temporary_message(surface)
        
        # Render normal sections
        else:
            self._render_sections(surface)
    
    def _render_progress_bar(self, surface: pygame.Surface):
        """Render the progress bar."""
        progress_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 5, 
                                  self.rect.width - 20, self.rect.height - 10)
        
        # Background
        pygame.draw.rect(surface, (230, 230, 230), progress_rect)
        pygame.draw.rect(surface, (180, 180, 180), progress_rect, 1)
        
        # Progress fill
        if self.progress_value > 0:
            fill_width = int(progress_rect.width * self.progress_value)
            fill_rect = pygame.Rect(progress_rect.x, progress_rect.y, fill_width, progress_rect.height)
            pygame.draw.rect(surface, self.progress_color, fill_rect)
        
        # Progress text
        if self.operation_text:
            progress_text = f"{self.operation_text} ({self.progress_value*100:.0f}%)"
            text_surface = self.font.render(progress_text, True, self.text_color)
            text_x = progress_rect.centerx - text_surface.get_width() // 2
            text_y = progress_rect.centery - text_surface.get_height() // 2
            surface.blit(text_surface, (text_x, text_y))
    
    def _render_temporary_message(self, surface: pygame.Surface):
        """Render temporary message."""
        if self.temp_message:
            text_surface = self.font.render(self.temp_message, True, self.temp_message_color)
            text_x = self.rect.x + 10
            text_y = self.rect.centery - text_surface.get_height() // 2
            surface.blit(text_surface, (text_x, text_y))
    
    def _render_sections(self, surface: pygame.Surface):
        """Render all status sections."""
        for i, section in enumerate(self.sections.values()):
            if section.visible and section.text:
                # Highlight clickable sections on hover
                if section.clickable:
                    mouse_pos = pygame.mouse.get_pos()
                    if section.rect.collidepoint(mouse_pos):
                        pygame.draw.rect(surface, self.highlight_color, section.rect)
                
                # Render text
                text_surface = self.font.render(section.text, True, self.text_color)
                text_x = section.rect.x + 5
                text_y = section.rect.centery - text_surface.get_height() // 2
                surface.blit(text_surface, (text_x, text_y))
                
                # Draw separator (except for last section)
                if i < len(self.sections) - 1 and section.rect.right < self.rect.width - 100:
                    separator_x = section.rect.right + 5
                    pygame.draw.line(surface, self.separator_color,
                                   (separator_x, self.rect.y + 3),
                                   (separator_x, self.rect.bottom - 3))
    
    def show_mouse_pos(self, pos: Tuple[int, int]):
        """Update mouse position (for backward compatibility)."""
        self.set_mouse_info(pos)
    
    def set_main_status(self, text: str):
        """Set the main status text."""
        self.sections["main"].set_text(text)
        
        # Sections
        self.sections: Dict[str, Any] = {}
    
    def set_sprite_sheet_info(self, name: str, tile_count: int, dimensions: Tuple[int, int] = None):
        """Set sprite sheet information."""
        self.sprite_sheet_name = name
        self.tile_count = tile_count
        
        if dimensions:
            info_text = f"Sheet: {name} ({tile_count} tiles, {dimensions[0]}x{dimensions[1]})"
        else:
            info_text = f"Sheet: {name} ({tile_count} tiles)"
        
        if "sheet" in self.sections:
            self.sections["sheet"].set_text(info_text)
    
    def set_selection_info(self, selected_count: int, total_frames: int = None):
        """Set frame selection information."""
        self.selected_count = selected_count
        self.total_frames = total_frames
        
        if total_frames:
            percentage = (selected_count / total_frames) * 100 if total_frames > 0 else 0
            selection_text = f"Selection: {selected_count}/{total_frames} ({percentage:.1f}%)"
        else:
            selection_text = f"Selection: {selected_count} frames"
        
        if "selection" in self.sections:
            self.sections["selection"].set_text(selection_text)
    
    def set_mouse_info(self, mouse_pos: Tuple[int, int], frame_pos: Tuple[int, int] = None, 
                       frame_index: int = None):
        """Set mouse position and current frame information."""
        self.mouse_pos = mouse_pos
        self.frame_pos = frame_pos
        self.frame_index = frame_index
        
        if frame_pos is not None:
            if frame_index is not None:
                text = f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]}) | Frame: ({frame_pos[0]}, {frame_pos[1]}) #{frame_index}"
            else:
                text = f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]}) | Frame: ({frame_pos[0]}, {frame_pos[1]})"
        else:
            text = f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]})"
        
        if "mouse" in self.sections:
            self.sections["mouse"].set_text(text)
    
    def show_temporary_message(self, message: str, duration: float = 3.0):
        """Show a temporary message."""
        self.temp_message = message
        self.temp_message_time = time.time()
        self.temp_message_duration = duration
    
    def set_operation_progress(self, operation: str, progress: float):
        """Set operation progress (0.0 to 1.0)."""
        self.operation_text = operation
        self.progress_value = max(0.0, min(1.0, progress))
        self.show_progress = True
        
        # Auto-hide when complete
        if progress >= 1.0:
            self.show_temporary_message(f"{operation} completed")
            # Hide progress after a short delay
            pygame.time.set_timer(pygame.USEREVENT + 1, 500)  # Hide after 500ms
    
    def hide_progress(self):
        """Hide the progress indicator."""
        self.show_progress = False
        self.operation_text = ""
        self.progress_value = 0.0
    
    def set_memory_usage(self, mb: float):
        """Set memory usage in MB."""
        self.memory_usage_mb = mb
    
    def update(self):
        """Update the status bar (call each frame)."""
        # Clear expired temporary messages
        if self.temp_message and time.time() - self.temp_message_time > self.temp_message_duration:
            self.temp_message = ""
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for the status bar."""
        if event.type == pygame.USEREVENT + 1:
            # Hide progress indicator
            self.hide_progress()
            return True
        return False
    
    def render(self, surface: pygame.Surface, window_width: int, y_position: int):
        """Render the status bar."""
        # Create status bar rectangle
        status_rect = pygame.Rect(0, y_position, window_width, self.height)
        
        # Draw background
        pygame.draw.rect(surface, self.bg_color, status_rect)
        pygame.draw.line(surface, self.border_color, 
                        (0, y_position), (window_width, y_position))
        
        # Update status
        self.update()
        
        # Left section: Sprite sheet info
        left_text = self._build_left_text()
        if left_text:
            left_surface = self.font.render(left_text, True, self.text_color)
            surface.blit(left_surface, (8, y_position + 6))
        
        # Center section: Temporary messages or operation progress
        center_text = self._get_center_content()
        if center_text:
            center_surface = self.font.render(center_text, True, self.text_color)
            center_x = (window_width - center_surface.get_width()) // 2
            surface.blit(center_surface, (center_x, y_position + 6))
        
        # Progress bar if active
        if self.show_progress:
            self._render_progress_bar(surface, window_width, y_position)
        
        # Right section: Mouse info and memory usage
        right_text = self._build_right_text()
        if right_text:
            right_surface = self.font.render(right_text, True, self.text_color)
            right_x = window_width - right_surface.get_width() - 8
            surface.blit(right_surface, (right_x, y_position + 6))
    
    def _build_left_text(self) -> str:
        """Build the left section text."""
        parts = []
        
        if self.sprite_sheet_name:
            parts.append(f"Sheet: {self.sprite_sheet_name}")
        
        if self.tile_count > 0:
            parts.append(f"{self.tile_count} tiles")
        
        if self.selected_count > 0:
            parts.append(f"{self.selected_count} selected")
        
        return " • ".join(parts)
    
    def _get_center_content(self) -> str:
        """Get the center content text."""
        if self.temp_message:
            return self.temp_message
        elif self.show_progress and self.operation_text:
            progress_percent = int(self.progress_value * 100)
            return f"{self.operation_text}... {progress_percent}%"
        return ""
    
    def _build_right_text(self) -> str:
        """Build the right section text."""
        parts = []
        
        # Mouse position and frame info
        if self.current_frame_info:
            parts.append(self.current_frame_info)
        elif self.mouse_pos != (0, 0):
            parts.append(f"({self.mouse_pos[0]}, {self.mouse_pos[1]})")
        
        # Memory usage if significant
        if self.memory_usage_mb > 50:  # Only show if using more than 50MB
            parts.append(f"{self.memory_usage_mb:.1f}MB")
        
        return " • ".join(parts)
    
    def _render_progress_bar(self, surface: pygame.Surface, window_width: int, y_position: int):
        """Render the progress bar."""
        if not self.show_progress:
            return
        
        # Progress bar dimensions
        bar_width = 200
        bar_height = 6
        bar_x = (window_width - bar_width) // 2
        bar_y = y_position + self.height - bar_height - 3
        
        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, self.progress_bg_color, bg_rect)
        pygame.draw.rect(surface, self.border_color, bg_rect, 1)
        
        # Fill
        if self.progress_value > 0:
            fill_width = int(bar_width * self.progress_value)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(surface, self.progress_fill_color, fill_rect)
    
    # Convenience methods for common operations
    def show_loading(self, operation: str):
        """Show a loading message."""
        self.set_operation_progress(operation, 0.0)
    
    def update_loading(self, progress: float):
        """Update loading progress."""
        if self.show_progress:
            self.progress_value = max(0.0, min(1.0, progress))
    
    def show_success(self, message: str):
        """Show a success message."""
        self.hide_progress()
        self.show_temporary_message(f"✓ {message}")
    
    def show_error(self, message: str):
        """Show an error message."""
        self.hide_progress()
        self.show_temporary_message(f"✗ {message}", duration=5.0)
    
    def show_info(self, message: str):
        """Show an info message."""
        self.show_temporary_message(f"ℹ {message}")
    
    def clear_all(self):
        """Clear all status information."""
        self.sprite_sheet_name = ""
        self.tile_count = 0
        self.selected_count = 0
        self.mouse_pos = (0, 0)
        self.current_frame_info = ""
        self.temp_message = ""
        self.hide_progress()
        self.memory_usage_mb = 0
