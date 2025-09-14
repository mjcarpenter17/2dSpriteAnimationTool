"""
Sprite sheet management system for handling multiple sprite sheets.
"""
import os
from typing import Dict, List, Optional, Tuple, Any
import pygame
from .spritesheet import SpriteSheet, SpriteSheetValidationError


class SpriteSheetManager:
    """
    Manages multiple sprite sheets with loading, validation, and switching capabilities.
    """
    
    def __init__(self):
        """Initialize the sprite sheet manager."""
        self.sprite_sheets: Dict[str, SpriteSheet] = {}
        self.active_sheet_id: Optional[str] = None
        self.sheet_counter = 0  # For generating unique IDs
    
    def load_sprite_sheet(self, filepath: str, tile_size: Tuple[int, int], 
                         margin: int = 0, spacing: int = 0, 
                         name: str = None) -> Optional[str]:
        """
        Load a new sprite sheet.
        
        Args:
            filepath: Path to sprite sheet image
            tile_size: (width, height) of each tile
            margin: Margin around sprite sheet
            spacing: Spacing between tiles
            name: Display name (auto-generated if None)
            
        Returns:
            Sprite sheet ID if successful, None otherwise
        """
        try:
            # Create sprite sheet instance
            sprite_sheet = SpriteSheet(filepath, tile_size, margin, spacing, name)
            
            # Generate unique ID
            sheet_id = self._generate_sheet_id(sprite_sheet.name)
            
            # Store sprite sheet
            self.sprite_sheets[sheet_id] = sprite_sheet
            
            # Set as active if it's the first one
            if self.active_sheet_id is None:
                self.active_sheet_id = sheet_id
            
            return sheet_id
            
        except SpriteSheetValidationError as e:
            print(f"Failed to load sprite sheet {filepath}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error loading sprite sheet {filepath}: {e}")
            return None
    
    def _generate_sheet_id(self, base_name: str) -> str:
        """Generate a unique sprite sheet ID."""
        self.sheet_counter += 1
        return f"{base_name}_{self.sheet_counter}"
    
    def remove_sprite_sheet(self, sheet_id: str) -> bool:
        """
        Remove a sprite sheet.
        
        Args:
            sheet_id: ID of sprite sheet to remove
            
        Returns:
            True if successful
        """
        if sheet_id not in self.sprite_sheets:
            return False
        
        # Remove the sprite sheet
        del self.sprite_sheets[sheet_id]
        
        # Update active sheet if needed
        if self.active_sheet_id == sheet_id:
            # Set active to another sheet or None
            remaining_ids = list(self.sprite_sheets.keys())
            self.active_sheet_id = remaining_ids[0] if remaining_ids else None
        
        return True
    
    def set_active_sheet(self, sheet_id: str) -> bool:
        """
        Set the active sprite sheet.
        
        Args:
            sheet_id: ID of sprite sheet to activate
            
        Returns:
            True if successful
        """
        if sheet_id in self.sprite_sheets:
            self.active_sheet_id = sheet_id
            return True
        return False
    
    def get_active_sheet(self) -> Optional[SpriteSheet]:
        """Get the currently active sprite sheet."""
        if self.active_sheet_id:
            return self.sprite_sheets.get(self.active_sheet_id)
        return None
    
    def get_sprite_sheet(self, sheet_id: str) -> Optional[SpriteSheet]:
        """Get a sprite sheet by ID."""
        return self.sprite_sheets.get(sheet_id)
    
    def get_all_sheet_ids(self) -> List[str]:
        """Get all sprite sheet IDs."""
        return list(self.sprite_sheets.keys())
    
    def get_sheet_info(self, sheet_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a sprite sheet.
        
        Args:
            sheet_id: Sprite sheet ID
            
        Returns:
            Dictionary with sheet information or None
        """
        sheet = self.get_sprite_sheet(sheet_id)
        if not sheet:
            return None
        
        return {
            "id": sheet_id,
            "name": sheet.name,
            "filepath": sheet.filepath,
            "dimensions": (sheet.width, sheet.height),
            "tile_size": sheet.tile_size,
            "grid_size": (sheet.rows, sheet.cols),
            "total_tiles": sheet.total_tiles,
            "margin": sheet.margin,
            "spacing": sheet.spacing,
            "warnings": sheet.validate_format()
        }
    
    def get_all_sheet_info(self) -> List[Dict[str, Any]]:
        """Get information for all loaded sprite sheets."""
        return [self.get_sheet_info(sheet_id) for sheet_id in self.get_all_sheet_ids()]
    
    def validate_all_sheets(self) -> Dict[str, List[str]]:
        """
        Validate all loaded sprite sheets.
        
        Returns:
            Dictionary mapping sheet_id to list of warnings
        """
        validation_results = {}
        for sheet_id, sheet in self.sprite_sheets.items():
            validation_results[sheet_id] = sheet.validate_format()
        return validation_results
    
    def clear_all_sheets(self):
        """Remove all sprite sheets."""
        self.sprite_sheets.clear()
        self.active_sheet_id = None
        self.sheet_counter = 0
    
    def suggest_tile_size(self, filepath: str) -> Optional[Tuple[int, int]]:
        """
        Analyze an image and suggest optimal tile size.
        
        Args:
            filepath: Path to image file
            
        Returns:
            Suggested (width, height) or None if analysis fails
        """
        try:
            # Load image to analyze
            surface = pygame.image.load(filepath)
            width, height = surface.get_size()
            
            # Common sprite sizes to test
            common_sizes = [
                (16, 16), (32, 32), (64, 64),  # Square sprites
                (24, 24), (48, 48), (96, 96),
                (16, 24), (32, 48), (24, 32),  # Rectangular sprites
                (90, 37),  # Based on existing sprite sheet
            ]
            
            best_score = 0
            best_size = None
            
            for tile_w, tile_h in common_sizes:
                # Calculate how well this tile size fits
                cols = width // tile_w
                rows = height // tile_h
                coverage = (cols * tile_w * rows * tile_h) / (width * height)
                
                # Prefer sizes that use more of the image
                score = coverage * (cols + rows)  # Favor more tiles too
                
                if score > best_score:
                    best_score = score
                    best_size = (tile_w, tile_h)
            
            return best_size
            
        except Exception as e:
            print(f"Failed to analyze image {filepath}: {e}")
            return None
    
    def has_unsaved_changes(self) -> bool:
        """Check if any sprite sheets have unsaved changes."""
        # For now, sprite sheets don't have unsaved changes
        # This will be relevant when we add editing capabilities
        return False
    
    def get_memory_usage(self) -> int:
        """
        Get approximate memory usage of all loaded sprite sheets in bytes.
        
        Returns:
            Estimated memory usage in bytes
        """
        total_bytes = 0
        for sheet in self.sprite_sheets.values():
            if sheet.surface:
                # Approximate: width * height * 4 bytes per pixel (RGBA)
                total_bytes += sheet.width * sheet.height * 4
        return total_bytes
    
    def __len__(self) -> int:
        """Get number of loaded sprite sheets."""
        return len(self.sprite_sheets)
    
    def __contains__(self, sheet_id: str) -> bool:
        """Check if a sprite sheet ID exists."""
        return sheet_id in self.sprite_sheets
    
    def __iter__(self):
        """Iterate over sprite sheet IDs."""
        return iter(self.sprite_sheets.keys())
