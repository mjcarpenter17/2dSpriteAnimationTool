"""
Frame Analysis System for Sprite Animation Tool
Provides pixel scanning, trimming, and pivot point calculation functionality.
"""
import pygame
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class FrameAnalysisResult:
    """Container for frame analysis results."""
    original_rect: pygame.Rect
    trimmed_rect: pygame.Rect
    pivot_point: Tuple[int, int]
    offset: Tuple[int, int]
    has_content: bool
    

class FrameAnalyzer:
    """
    Advanced frame analysis system with pixel scanning and optimization.
    """
    
    def __init__(self, alpha_threshold: int = 16):
        """Initialize the frame analyzer."""
        self.alpha_threshold = alpha_threshold
        self.analysis_cache: Dict[str, FrameAnalysisResult] = {}
        
    def clear_cache(self):
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        
    def set_alpha_threshold(self, threshold: int):
        """Set the alpha threshold for transparency detection."""
        self.alpha_threshold = max(0, min(255, threshold))
        self.clear_cache()  # Clear cache when threshold changes
        
    def analyze_frame(self, sprite_sheet: pygame.Surface, frame_rect: pygame.Rect, 
                      sheet_id: str = "", row: int = 0, col: int = 0) -> Optional[FrameAnalysisResult]:
        """
        Analyze a frame from a sprite sheet to determine trimmed bounds and pivot point.
        
        Args:
            sprite_sheet: The sprite sheet surface
            frame_rect: Rectangle defining the frame within the sprite sheet
            sheet_id: Identifier for caching purposes
            row: Frame row for caching
            col: Frame column for caching
            
        Returns:
            FrameAnalysisResult or None if analysis fails
        """
        # Create cache key
        cache_key = f"{sheet_id}_{row}_{col}_{frame_rect.x}_{frame_rect.y}_{frame_rect.w}_{frame_rect.h}_{self.alpha_threshold}"
        
        # Check cache first
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
            
        try:
            # Validate frame rect bounds
            if (frame_rect.x < 0 or frame_rect.y < 0 or 
                frame_rect.right > sprite_sheet.get_width() or 
                frame_rect.bottom > sprite_sheet.get_height()):
                return None
                
            # Extract frame subsurface
            frame_surface = sprite_sheet.subsurface(frame_rect).copy().convert_alpha()
            
            # Perform pixel scanning
            result = self._scan_frame_pixels(frame_surface, frame_rect)
            
            # Cache the result
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"Frame analysis error: {e}")
            return None
            
    def _scan_frame_pixels(self, frame_surface: pygame.Surface, 
                          original_rect: pygame.Rect) -> FrameAnalysisResult:
        """
        Scan frame pixels to find the minimal bounding box of non-transparent content.
        """
        width, height = frame_surface.get_size()
        
        # Initialize bounds
        min_x = width
        min_y = height
        max_x = -1
        max_y = -1
        
        # Scan all pixels
        for y in range(height):
            for x in range(width):
                pixel_color = frame_surface.get_at((x, y))
                
                # Check if pixel is above alpha threshold
                if pixel_color.a > self.alpha_threshold:
                    if x < min_x:
                        min_x = x
                    if y < min_y:
                        min_y = y
                    if x > max_x:
                        max_x = x
                    if y > max_y:
                        max_y = y
                        
        # Check if any content was found
        if max_x == -1:
            # No opaque pixels found - use full frame
            trimmed_rect = pygame.Rect(original_rect.x, original_rect.y, 
                                     original_rect.w, original_rect.h)
            pivot_x = original_rect.w // 2
            pivot_y = original_rect.h - 1
            offset = (0, 0)
            has_content = False
        else:
            # Calculate trimmed dimensions
            trimmed_w = max_x - min_x + 1
            trimmed_h = max_y - min_y + 1
            
            # Create trimmed rect in sprite sheet coordinates
            trimmed_rect = pygame.Rect(original_rect.x + min_x, original_rect.y + min_y,
                                     trimmed_w, trimmed_h)
            
            # Calculate pivot point (bottom-center of trimmed rect)
            pivot_x = trimmed_w // 2
            pivot_y = trimmed_h - 1
            
            # Calculate offset from original frame
            offset = (min_x, min_y)
            has_content = True
            
        return FrameAnalysisResult(
            original_rect=original_rect,
            trimmed_rect=trimmed_rect,
            pivot_point=(pivot_x, pivot_y),
            offset=offset,
            has_content=has_content
        )
        
    def batch_analyze_frames(self, sprite_sheet: pygame.Surface, 
                           frame_rects: list, sheet_id: str = "") -> Dict[Tuple[int, int], FrameAnalysisResult]:
        """
        Analyze multiple frames in batch for efficiency.
        
        Args:
            sprite_sheet: The sprite sheet surface
            frame_rects: List of (rect, row, col) tuples
            sheet_id: Identifier for caching purposes
            
        Returns:
            Dictionary mapping (row, col) to FrameAnalysisResult
        """
        results = {}
        
        for frame_rect, row, col in frame_rects:
            result = self.analyze_frame(sprite_sheet, frame_rect, sheet_id, row, col)
            if result:
                results[(row, col)] = result
                
        return results
        
    def get_pivot_in_sheet_coordinates(self, analysis_result: FrameAnalysisResult) -> Tuple[int, int]:
        """
        Get pivot point coordinates in sprite sheet space.
        
        Args:
            analysis_result: Result from analyze_frame
            
        Returns:
            (x, y) coordinates in sprite sheet space
        """
        pivot_x = analysis_result.trimmed_rect.x + analysis_result.pivot_point[0]
        pivot_y = analysis_result.trimmed_rect.y + analysis_result.pivot_point[1]
        return (pivot_x, pivot_y)
        
    def optimize_animation_frames(self, analysis_results: Dict[Tuple[int, int], FrameAnalysisResult]) -> Dict[str, Any]:
        """
        Analyze animation frames for optimization opportunities.
        
        Args:
            analysis_results: Dictionary of frame analysis results
            
        Returns:
            Dictionary with optimization statistics and suggestions
        """
        if not analysis_results:
            return {}
            
        total_frames = len(analysis_results)
        frames_with_content = sum(1 for result in analysis_results.values() if result.has_content)
        empty_frames = total_frames - frames_with_content
        
        # Calculate size statistics
        original_sizes = [result.original_rect.w * result.original_rect.h for result in analysis_results.values()]
        trimmed_sizes = [result.trimmed_rect.w * result.trimmed_rect.h for result in analysis_results.values() if result.has_content]
        
        original_total = sum(original_sizes)
        trimmed_total = sum(trimmed_sizes)
        
        space_savings = original_total - trimmed_total if original_total > 0 else 0
        savings_percent = (space_savings / original_total * 100) if original_total > 0 else 0
        
        # Find common frame sizes
        size_counts = {}
        for result in analysis_results.values():
            if result.has_content:
                size = (result.trimmed_rect.w, result.trimmed_rect.h)
                size_counts[size] = size_counts.get(size, 0) + 1
                
        most_common_size = max(size_counts.items(), key=lambda x: x[1])[0] if size_counts else None
        
        return {
            "total_frames": total_frames,
            "frames_with_content": frames_with_content,
            "empty_frames": empty_frames,
            "original_total_pixels": original_total,
            "trimmed_total_pixels": trimmed_total,
            "space_savings_pixels": space_savings,
            "space_savings_percent": savings_percent,
            "most_common_trimmed_size": most_common_size,
            "size_distribution": size_counts
        }
