"""
SpriteSheet class and related utilities for handling sprite sheet loading, 
validation, and frame management.
"""
import os
import sys
from typing import Tuple, List, Optional, Dict, Any
import pygame


class SpriteSheetValidationError(Exception):
    """Raised when sprite sheet validation fails."""
    pass


class SpriteSheet:
    """
    Represents a sprite sheet with tile-based frame organization.
    
    Handles loading, validation, grid computation, and frame analysis
    for individual sprite sheets in the animation tool.
    """
    
    def __init__(self, filepath: str, tile_size: Tuple[int, int], 
                 margin: int = 0, spacing: int = 0, name: str = None):
        """
        Initialize a sprite sheet.
        
        Args:
            filepath: Path to the sprite sheet image file
            tile_size: (width, height) of each frame/tile
            margin: Margin around the entire sprite sheet
            spacing: Spacing between individual tiles
            name: Display name for the sprite sheet (auto-generated if None)
        """
        self.filepath = os.path.abspath(filepath)
        self.tile_size = tile_size
        self.margin = margin
        self.spacing = spacing
        self.name = name or os.path.splitext(os.path.basename(filepath))[0]
        
        # Loaded sprite sheet surface
        self._surface: Optional[pygame.Surface] = None
        self._tiles: List[pygame.Surface] = []
        
        # Grid properties
        self._cols: int = 0
        self._rows: int = 0
        self._total_tiles: int = 0
        
        # Analysis cache for trim and pivot data
        self._analysis_cache: Dict[Tuple[int, int], Any] = {}
        
        # Load and validate the sprite sheet
        self._load_and_validate()
    
    @property
    def surface(self) -> pygame.Surface:
        """Get the loaded sprite sheet surface."""
        return self._surface
    
    @property
    def width(self) -> int:
        """Get sprite sheet width."""
        return self._surface.get_width() if self._surface else 0
    
    @property
    def height(self) -> int:
        """Get sprite sheet height."""
        return self._surface.get_height() if self._surface else 0
    
    @property
    def cols(self) -> int:
        """Get number of columns in the grid."""
        return self._cols
    
    @property
    def rows(self) -> int:
        """Get number of rows in the grid."""
        return self._rows
    
    @property
    def total_tiles(self) -> int:
        """Get total number of tiles in the sprite sheet."""
        return self._total_tiles
    
    def _load_and_validate(self):
        """Load the sprite sheet and validate its format."""
        try:
            # Check if file exists
            if not os.path.exists(self.filepath):
                raise SpriteSheetValidationError(f"File not found: {self.filepath}")
            
            # Check file permissions
            if not os.access(self.filepath, os.R_OK):
                raise SpriteSheetValidationError(f"No read permission: {self.filepath}")
            
            # Load the image
            try:
                self._surface = pygame.image.load(self.filepath)
            except pygame.error as e:
                raise SpriteSheetValidationError(f"Failed to load image: {e}")
            
            # Validate image dimensions
            if self.width <= 0 or self.height <= 0:
                raise SpriteSheetValidationError("Image has invalid dimensions")
            
            # Check if image is too large (memory protection)
            max_size = 8192  # 8K max dimension
            if self.width > max_size or self.height > max_size:
                raise SpriteSheetValidationError(
                    f"Image too large: {self.width}x{self.height} (max: {max_size}x{max_size})"
                )
            
            # Compute grid dimensions
            self._compute_grid()
            
            # Validate grid produces reasonable results
            if self._cols <= 0 or self._rows <= 0:
                raise SpriteSheetValidationError(
                    f"Invalid grid configuration produces {self._cols}x{self._rows} tiles"
                )
            
            # Convert surface for better performance
            self._surface = self._surface.convert_alpha()
            
        except Exception as e:
            if isinstance(e, SpriteSheetValidationError):
                raise
            else:
                raise SpriteSheetValidationError(f"Unexpected error loading sprite sheet: {e}")
    
    def _compute_grid(self):
        """Compute the grid dimensions based on tile size and spacing."""
        fw, fh = self.tile_size
        
        # Grid computation: n <= floor((image_w - margin + spacing) / (fw + spacing))
        self._cols = max(0, (self.width - self.margin + self.spacing) // (fw + self.spacing))
        self._rows = max(0, (self.height - self.margin + self.spacing) // (fh + self.spacing))
        self._total_tiles = self._cols * self._rows

    def reconfigure_grid(self, tile_size: Tuple[int, int], margin: int = None, spacing: int = None):
        """
        Reconfigure the sprite sheet's grid with new parameters.
        
        Args:
            tile_size: New (width, height) for each frame/tile
            margin: New margin around sprite sheet (keeps current if None)
            spacing: New spacing between tiles (keeps current if None)
        """
        self.tile_size = tile_size
        if margin is not None:
            self.margin = margin
        if spacing is not None:
            self.spacing = spacing
        
        # Recompute grid with new parameters
        self._compute_grid()
        
        # Clear any cached tile surfaces since grid changed
        self._tiles.clear()
    
    def get_frame_rect(self, row: int, col: int) -> pygame.Rect:
        """
        Get the rectangle for a specific frame in the sprite sheet.
        
        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            
        Returns:
            pygame.Rect for the frame
            
        Raises:
            IndexError: If row or col is out of bounds
        """
        if not (0 <= row < self._rows and 0 <= col < self._cols):
            raise IndexError(f"Frame ({row}, {col}) out of bounds (grid: {self._rows}x{self._cols})")
        
        fw, fh = self.tile_size
        x = self.margin + col * (fw + self.spacing)
        y = self.margin + row * (fh + self.spacing)
        return pygame.Rect(x, y, fw, fh)
    
    def get_frame_surface(self, row: int, col: int) -> pygame.Surface:
        """
        Extract a single frame as a surface.
        
        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            
        Returns:
            pygame.Surface containing the frame
        """
        rect = self.get_frame_rect(row, col)
        
        # Validate rect is within image bounds
        if (rect.right > self.width or rect.bottom > self.height or 
            rect.x < 0 or rect.y < 0):
            raise IndexError(f"Frame ({row}, {col}) extends beyond image boundaries")
        
        return self._surface.subsurface(rect).copy()
    
    def load_all_tiles(self) -> List[pygame.Surface]:
        """
        Load all tiles as individual surfaces.
        
        Returns:
            List of pygame.Surface objects for all tiles
        """
        if self._tiles:
            return self._tiles
        
        self._tiles = []
        for row in range(self._rows):
            for col in range(self._cols):
                try:
                    tile = self.get_frame_surface(row, col)
                    self._tiles.append(tile)
                except IndexError:
                    # Handle partial tiles at edges gracefully
                    continue
        
        return self._tiles
    
    def analyze_frame(self, row: int, col: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a frame for trim bounds and pivot point.
        
        Args:
            row: Row index (0-based) 
            col: Column index (0-based)
            
        Returns:
            Dictionary with analysis results or None if analysis fails:
            {
                'trim_rect': (x, y, width, height),  # Trimmed bounds
                'pivot': (x, y),                     # Pivot point (relative to trim)
                'offset': (x, y),                    # Offset from original to trim
                'original_rect': pygame.Rect         # Original frame rect
            }
        """
        cache_key = (row, col, *self.tile_size, self.margin, self.spacing)
        
        # Return cached result if available
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        
        try:
            # Get original frame rect and surface
            orig_rect = self.get_frame_rect(row, col)
            frame_surface = self.get_frame_surface(row, col)
            
            # Analyze for non-transparent pixels
            w, h = frame_surface.get_size()
            threshold = 16  # Alpha threshold for "opaque"
            
            min_x, min_y = w, h
            max_x, max_y = -1, -1
            
            # Scan pixels for content bounds
            for y in range(h):
                for x in range(w):
                    pixel = frame_surface.get_at((x, y))
                    if len(pixel) > 3 and pixel[3] > threshold:  # Check alpha
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
            
            # Calculate results
            if max_x == -1:
                # No opaque pixels - use full frame
                trim_rect = (orig_rect.x, orig_rect.y, orig_rect.w, orig_rect.h)
                pivot_x = orig_rect.w // 2
                pivot_y = orig_rect.h - 1
                offset = (0, 0)
            else:
                # Calculate trimmed bounds
                trim_w = max_x - min_x + 1
                trim_h = max_y - min_y + 1
                trim_rect = (orig_rect.x + min_x, orig_rect.y + min_y, trim_w, trim_h)
                pivot_x = trim_w // 2
                pivot_y = trim_h - 1
                offset = (min_x, min_y)
            
            result = {
                'trim_rect': trim_rect,
                'pivot': (pivot_x, pivot_y),
                'offset': offset,
                'original_rect': orig_rect
            }
            
            # Cache the result
            self._analysis_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"Warning: Frame analysis failed for ({row}, {col}): {e}")
            self._analysis_cache[cache_key] = None
            return None
    
    def clear_analysis_cache(self):
        """Clear the frame analysis cache."""
        self._analysis_cache.clear()
    
    def validate_format(self) -> List[str]:
        """
        Validate the sprite sheet format and return any warnings.
        
        Returns:
            List of warning messages (empty if no issues)
        """
        warnings = []
        
        # Check for unusual aspect ratios
        fw, fh = self.tile_size
        aspect = fw / fh if fh > 0 else 1.0
        if aspect < 0.2 or aspect > 5.0:
            warnings.append(f"Unusual tile aspect ratio: {aspect:.2f}")
        
        # Check for partial tiles at edges
        expected_w = self.margin * 2 + self._cols * fw + (self._cols - 1) * self.spacing
        expected_h = self.margin * 2 + self._rows * fh + (self._rows - 1) * self.spacing
        
        if expected_w < self.width:
            warnings.append("Sprite sheet has extra pixels on right edge")
        if expected_h < self.height:
            warnings.append("Sprite sheet has extra pixels on bottom edge")
        
        # Check for very small or large tile counts
        if self._total_tiles < 1:
            warnings.append("No valid tiles found")
        elif self._total_tiles > 1000:
            warnings.append(f"Very large tile count: {self._total_tiles}")
        
        return warnings
    
    def get_tile_count(self) -> int:
        """Get total number of tiles."""
        return self._total_tiles
    
    def __str__(self) -> str:
        """String representation of the sprite sheet."""
        return (f"SpriteSheet('{self.name}', {self.width}x{self.height}, "
                f"tiles: {self._rows}x{self._cols}, size: {self.tile_size})")
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"SpriteSheet(filepath='{self.filepath}', tile_size={self.tile_size}, "
                f"margin={self.margin}, spacing={self.spacing}, name='{self.name}')")
