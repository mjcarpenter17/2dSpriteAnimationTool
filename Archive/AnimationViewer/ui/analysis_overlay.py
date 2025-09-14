"""
Visual Analysis Overlay System
Provides visual feedback for frame analysis results including trimmed bounds and pivot points.
"""
import pygame
from typing import Optional, Tuple, List
from core.frame_analyzer import FrameAnalysisResult


class AnalysisOverlay:
    """
    Handles visual overlays for frame analysis display.
    """
    
    def __init__(self):
        """Initialize the analysis overlay system."""
        # Overlay colors
        self.original_frame_color = (240, 220, 60)    # Yellow - existing
        self.trimmed_frame_color = (50, 210, 255)     # Cyan - trimmed bounds
        self.pivot_color = (255, 80, 180)             # Pink - pivot point
        self.no_content_color = (120, 120, 120)       # Gray - empty frames
        
        # Overlay styles
        self.line_width = 2
        self.pivot_size = 8
        self.dash_length = 4
        
        # State
        self.show_overlays = False
        self.show_original = True
        self.show_trimmed = True
        self.show_pivot = True
        self.show_info = True
        
    def set_overlay_visibility(self, show_overlays: bool):
        """Set overall overlay visibility."""
        self.show_overlays = show_overlays
        
    def set_component_visibility(self, original: bool = None, trimmed: bool = None, 
                               pivot: bool = None, info: bool = None):
        """Set visibility of individual overlay components."""
        if original is not None:
            self.show_original = original
        if trimmed is not None:
            self.show_trimmed = trimmed
        if pivot is not None:
            self.show_pivot = pivot
        if info is not None:
            self.show_info = info
            
    def render_frame_analysis(self, screen: pygame.Surface, analysis_result: FrameAnalysisResult,
                            viewport_offset: Tuple[int, int], scale: float, header_height: int = 0):
        """
        Render analysis overlays for a single frame.
        
        Args:
            screen: Surface to render to
            analysis_result: Frame analysis data
            viewport_offset: (scroll_x, scroll_y) viewport offset
            scale: Display scale factor
            header_height: Height of header area to offset rendering
        """
        if not self.show_overlays or not analysis_result:
            return
            
        scroll_x, scroll_y = viewport_offset
        
        # Render original frame outline (yellow)
        if self.show_original:
            self._render_frame_rect(screen, analysis_result.original_rect, 
                                  self.original_frame_color, scroll_x, scroll_y, 
                                  scale, header_height, line_width=3)
                                  
        # Render trimmed frame outline (cyan)
        if self.show_trimmed and analysis_result.has_content:
            self._render_frame_rect(screen, analysis_result.trimmed_rect, 
                                  self.trimmed_frame_color, scroll_x, scroll_y, 
                                  scale, header_height)
                                  
        # Render pivot point (pink cross)
        if self.show_pivot and analysis_result.has_content:
            pivot_sheet_x = analysis_result.trimmed_rect.x + analysis_result.pivot_point[0]
            pivot_sheet_y = analysis_result.trimmed_rect.y + analysis_result.pivot_point[1]
            
            self._render_pivot_point(screen, (pivot_sheet_x, pivot_sheet_y),
                                   scroll_x, scroll_y, scale, header_height)
                                   
        # Render no-content indicator for empty frames
        if not analysis_result.has_content:
            self._render_empty_frame_indicator(screen, analysis_result.original_rect,
                                             scroll_x, scroll_y, scale, header_height)
                                             
    def _render_frame_rect(self, screen: pygame.Surface, rect: pygame.Rect, 
                          color: Tuple[int, int, int], scroll_x: int, scroll_y: int, 
                          scale: float, header_height: int, line_width: int = None):
        """Render a frame rectangle with proper scaling and viewport offset."""
        if line_width is None:
            line_width = self.line_width
            
        # Convert to viewport coordinates
        x = int(rect.x * scale) - scroll_x
        y = int(rect.y * scale) - scroll_y + header_height
        w = int(rect.w * scale)
        h = int(rect.h * scale)
        
        # Create viewport rect
        viewport_rect = pygame.Rect(x, y, w, h)
        
        # Check if rect is visible
        screen_rect = screen.get_rect()
        if viewport_rect.colliderect(screen_rect):
            pygame.draw.rect(screen, color, viewport_rect, line_width)
            
    def _render_pivot_point(self, screen: pygame.Surface, pivot_pos: Tuple[int, int],
                          scroll_x: int, scroll_y: int, scale: float, header_height: int):
        """Render pivot point as a cross."""
        pivot_x, pivot_y = pivot_pos
        
        # Convert to viewport coordinates
        x = int(pivot_x * scale) - scroll_x
        y = int(pivot_y * scale) - scroll_y + header_height
        
        # Check if pivot is visible
        screen_rect = screen.get_rect()
        pivot_area = pygame.Rect(x - self.pivot_size, y - self.pivot_size, 
                                self.pivot_size * 2, self.pivot_size * 2)
        
        if pivot_area.colliderect(screen_rect):
            # Draw cross
            half_size = self.pivot_size // 2
            
            # Horizontal line
            pygame.draw.line(screen, self.pivot_color, 
                           (x - half_size, y), (x + half_size, y), 2)
            
            # Vertical line  
            pygame.draw.line(screen, self.pivot_color,
                           (x, y - half_size), (x, y + half_size), 2)
                           
    def _render_empty_frame_indicator(self, screen: pygame.Surface, rect: pygame.Rect,
                                    scroll_x: int, scroll_y: int, scale: float, header_height: int):
        """Render indicator for frames with no content."""
        # Convert to viewport coordinates
        x = int(rect.x * scale) - scroll_x
        y = int(rect.y * scale) - scroll_y + header_height
        w = int(rect.w * scale)
        h = int(rect.h * scale)
        
        viewport_rect = pygame.Rect(x, y, w, h)
        
        # Check if rect is visible
        screen_rect = screen.get_rect()
        if viewport_rect.colliderect(screen_rect):
            # Draw dashed border
            self._draw_dashed_rect(screen, viewport_rect, self.no_content_color)
            
            # Draw X in center
            center_x = x + w // 2
            center_y = y + h // 2
            quarter_w = w // 4
            quarter_h = h // 4
            
            pygame.draw.line(screen, self.no_content_color,
                           (center_x - quarter_w, center_y - quarter_h),
                           (center_x + quarter_w, center_y + quarter_h), 2)
                           
            pygame.draw.line(screen, self.no_content_color,
                           (center_x + quarter_w, center_y - quarter_h),
                           (center_x - quarter_w, center_y + quarter_h), 2)
                           
    def _draw_dashed_rect(self, screen: pygame.Surface, rect: pygame.Rect, 
                         color: Tuple[int, int, int]):
        """Draw a dashed rectangle."""
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        
        # Top edge
        self._draw_dashed_line(screen, (x, y), (x + w, y), color)
        # Right edge
        self._draw_dashed_line(screen, (x + w, y), (x + w, y + h), color)
        # Bottom edge
        self._draw_dashed_line(screen, (x + w, y + h), (x, y + h), color)
        # Left edge
        self._draw_dashed_line(screen, (x, y + h), (x, y), color)
        
    def _draw_dashed_line(self, screen: pygame.Surface, start: Tuple[int, int], 
                         end: Tuple[int, int], color: Tuple[int, int, int]):
        """Draw a dashed line between two points."""
        x1, y1 = start
        x2, y2 = end
        
        # Calculate line vector
        dx = x2 - x1
        dy = y2 - y1
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 1:
            return
            
        # Normalize direction
        unit_x = dx / distance
        unit_y = dy / distance
        
        # Draw dashes
        current_distance = 0
        while current_distance < distance:
            dash_start_x = int(x1 + unit_x * current_distance)
            dash_start_y = int(y1 + unit_y * current_distance)
            
            dash_end_distance = min(current_distance + self.dash_length, distance)
            dash_end_x = int(x1 + unit_x * dash_end_distance)
            dash_end_y = int(y1 + unit_y * dash_end_distance)
            
            pygame.draw.line(screen, color, (dash_start_x, dash_start_y), 
                           (dash_end_x, dash_end_y), 1)
            
            current_distance += self.dash_length * 2  # Skip space between dashes
            
    def format_analysis_info(self, analysis_result: FrameAnalysisResult) -> List[str]:
        """
        Format analysis result information for display.
        
        Args:
            analysis_result: Frame analysis data
            
        Returns:
            List of formatted info strings
        """
        if not analysis_result:
            return ["No analysis data available"]
            
        info_lines = []
        
        # Original frame info
        orig = analysis_result.original_rect
        info_lines.append(f"Original: ({orig.x}, {orig.y}, {orig.w}, {orig.h})")
        
        if analysis_result.has_content:
            # Trimmed frame info
            trim = analysis_result.trimmed_rect
            info_lines.append(f"Trimmed: ({trim.x}, {trim.y}, {trim.w}, {trim.h})")
            
            # Pivot info
            pivot = analysis_result.pivot_point
            info_lines.append(f"Pivot: ({pivot[0]}, {pivot[1]})")
            
            # Offset info
            offset = analysis_result.offset
            info_lines.append(f"Offset: ({offset[0]}, {offset[1]})")
            
            # Size savings
            orig_area = orig.w * orig.h
            trim_area = trim.w * trim.h
            savings = orig_area - trim_area
            savings_percent = (savings / orig_area * 100) if orig_area > 0 else 0
            
            info_lines.append(f"Space saved: {savings} pixels ({savings_percent:.1f}%)")
        else:
            info_lines.append("Empty frame (no content detected)")
            
        return info_lines
