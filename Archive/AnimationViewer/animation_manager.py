#!/usr/bin/env python3
"""
Animation Manager - Core Animation Discovery and Management System

This module handles the discovery, organization, and management of animation files
across multiple folders. It provides the foundation for the multi-spritesheet
animation library system.

Classes:
    AnimationEntry: Represents individual animation metadata
    AnimationFolder: Manages folder paths and animation discovery
    AnimationManager: Core management system for folders and animations

Author: AI Assistant
Project: Sprite Animation Tool - Phase 2
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class AnimationEntry:
    """Represents individual animation metadata from JSON files."""
    
    def __init__(self, filepath: str):
        """Initialize animation entry from filepath.
        
        Args:
            filepath: Absolute path to the animation JSON file
        """
        self.filepath = filepath
        self.name = ""
        self.spritesheet_path = ""
        self.frame_count = 0
        self.creation_date = datetime.now()
        self.metadata = {}
        self.thumbnail = None  # pygame.Surface - Optional first frame preview
        
        # Load metadata from file
        self._load_metadata()
    
    def _load_metadata(self):
        """Load and cache metadata from the animation JSON file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract basic information
            self.name = data.get('animation', os.path.splitext(os.path.basename(self.filepath))[0])
            self.spritesheet_path = data.get('sheet', '')
            self.frame_count = len(data.get('frames', []))
            self.metadata = data
            
            # Get file creation date
            stat = os.stat(self.filepath)
            self.creation_date = datetime.fromtimestamp(stat.st_mtime)
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"Warning: Failed to load animation metadata from {self.filepath}: {e}")
            # Set fallback values
            self.name = os.path.splitext(os.path.basename(self.filepath))[0]
            self.spritesheet_path = ""
            self.frame_count = 0
            self.metadata = {}
    
    def is_valid(self) -> bool:
        """Check if the animation entry has valid metadata."""
        return bool(self.metadata and 'frames' in self.metadata and self.frame_count > 0)
    
    def get_relative_spritesheet_path(self, base_dir: str) -> str:
        """Get spritesheet path relative to a base directory."""
        if not self.spritesheet_path:
            return ""
        
        # Convert relative path in metadata to absolute path
        if not os.path.isabs(self.spritesheet_path):
            # Resolve relative to animation file location
            animation_dir = os.path.dirname(self.filepath)
            abs_spritesheet = os.path.abspath(os.path.join(animation_dir, self.spritesheet_path))
        else:
            abs_spritesheet = self.spritesheet_path
        
        # Return path relative to base_dir
        try:
            return os.path.relpath(abs_spritesheet, base_dir)
        except ValueError:
            # Different drives on Windows - return absolute path
            return abs_spritesheet


class AnimationFolder:
    """Manages folder paths and animation discovery."""
    
    def __init__(self, path: str, name: str = None):
        """Initialize animation folder.
        
        Args:
            path: Absolute path to the folder
            name: Display name (defaults to folder basename)
        """
        self.path = os.path.abspath(path)
        self.name = name or os.path.basename(self.path)
        self.animations: List[AnimationEntry] = []
        self.is_expanded = True  # UI state for collapsible folders
        self.color_band = (70, 130, 180)  # Default blue color
        self.last_scan = datetime.min  # For change detection
        
    def scan_for_animations(self) -> int:
        """Scan folder for animation JSON files and update animations list.
        
        Returns:
            Number of valid animations found
        """
        old_count = len(self.animations)
        self.animations.clear()
        
        if not os.path.exists(self.path) or not os.path.isdir(self.path):
            print(f"Warning: Animation folder does not exist: {self.path}")
            return 0
        
        try:
            # Search for JSON files in the folder
            for filename in os.listdir(self.path):
                if filename.lower().endswith('.json'):
                    filepath = os.path.join(self.path, filename)
                    
                    # Validate it's an animation file
                    if validate_animation_file(filepath):
                        animation_entry = AnimationEntry(filepath)
                        if animation_entry.is_valid():
                            self.animations.append(animation_entry)
            
            # Sort animations by name for consistent display
            self.animations.sort(key=lambda a: a.name.lower())
            
            # Update scan timestamp
            self.last_scan = datetime.now()
            
            new_count = len(self.animations)
            if new_count != old_count:
                print(f"Folder '{self.name}': Found {new_count} animations (was {old_count})")
            
            return new_count
            
        except Exception as e:
            print(f"Error scanning folder {self.path}: {e}")
            return 0
    
    def get_animation_by_name(self, name: str) -> Optional[AnimationEntry]:
        """Get animation entry by name."""
        for animation in self.animations:
            if animation.name == name:
                return animation
        return None
    
    def needs_rescan(self, threshold_seconds: int = 30) -> bool:
        """Check if folder needs rescanning based on time threshold."""
        elapsed = (datetime.now() - self.last_scan).total_seconds()
        return elapsed > threshold_seconds


class AnimationManager:
    """Core management system for animation folders and discovery."""
    
    def __init__(self):
        """Initialize the animation manager."""
        self.folders: List[AnimationFolder] = []
        self.animation_cache: Dict[str, AnimationEntry] = {}  # filepath -> entry
        self._folder_colors = [
            (70, 130, 180),   # Steel Blue
            (60, 179, 113),   # Medium Sea Green  
            (255, 140, 0),    # Dark Orange
            (147, 112, 219),  # Medium Purple
            (220, 20, 60),    # Crimson
            (32, 178, 170),   # Light Sea Green
            (255, 69, 0),     # Red Orange
            (138, 43, 226)    # Blue Violet
        ]
        self._next_color_index = 0
    
    def add_folder(self, folder_path: str, folder_name: str = None) -> Optional[AnimationFolder]:
        """Add new folder to watch list and scan for animations.
        
        Args:
            folder_path: Absolute path to the folder
            folder_name: Optional display name for the folder
            
        Returns:
            AnimationFolder instance if successful, None if failed
        """
        # Validate folder exists and is readable
        if not os.path.exists(folder_path):
            print(f"Error: Folder does not exist: {folder_path}")
            return None
        
        if not os.path.isdir(folder_path):
            print(f"Error: Path is not a directory: {folder_path}")
            return None
        
        # Check if folder is already being watched
        abs_path = os.path.abspath(folder_path)
        for existing_folder in self.folders:
            if existing_folder.path == abs_path:
                print(f"Folder already being watched: {abs_path}")
                return existing_folder
        
        # Create new AnimationFolder instance
        folder = AnimationFolder(abs_path, folder_name)
        
        # Assign color band
        folder.color_band = self._folder_colors[self._next_color_index % len(self._folder_colors)]
        self._next_color_index += 1
        
        # Scan for animations
        animation_count = folder.scan_for_animations()
        
        # Add to folders list
        self.folders.append(folder)
        
        # Update animation cache
        for animation in folder.animations:
            self.animation_cache[animation.filepath] = animation
        
        print(f"Added folder '{folder.name}' with {animation_count} animations")
        return folder
    
    def remove_folder(self, folder_path: str) -> bool:
        """Remove folder from watch list.
        
        Args:
            folder_path: Path to the folder to remove
            
        Returns:
            True if folder was removed, False if not found
        """
        abs_path = os.path.abspath(folder_path)
        
        for i, folder in enumerate(self.folders):
            if folder.path == abs_path:
                # Remove animations from cache
                for animation in folder.animations:
                    self.animation_cache.pop(animation.filepath, None)
                
                # Remove folder from list
                self.folders.pop(i)
                print(f"Removed folder: {folder.name}")
                return True
        
        print(f"Folder not found for removal: {abs_path}")
        return False
    
    def get_animation_by_path(self, filepath: str) -> Optional[AnimationEntry]:
        """Cached retrieval of animation metadata.
        
        Args:
            filepath: Absolute path to animation JSON file
            
        Returns:
            AnimationEntry if found, None otherwise
        """
        return self.animation_cache.get(filepath)
    
    def get_all_animations(self) -> List[AnimationEntry]:
        """Get all animations from all folders."""
        all_animations = []
        for folder in self.folders:
            all_animations.extend(folder.animations)
        return all_animations
    
    def scan_folder(self, folder: AnimationFolder) -> List[AnimationEntry]:
        """Scan specific folder for animation files and update cache.
        
        Args:
            folder: AnimationFolder to scan
            
        Returns:
            List of AnimationEntry objects found
        """
        # Remove old animations from cache
        for animation in folder.animations:
            self.animation_cache.pop(animation.filepath, None)
        
        # Rescan folder
        folder.scan_for_animations()
        
        # Add new animations to cache
        for animation in folder.animations:
            self.animation_cache[animation.filepath] = animation
        
        return folder.animations
    
    def rescan_all_folders(self) -> int:
        """Rescan all folders for changes.
        
        Returns:
            Total number of animations found across all folders
        """
        total_animations = 0
        for folder in self.folders:
            total_animations += len(self.scan_folder(folder))
        
        print(f"Rescanned all folders: {total_animations} total animations found")
        return total_animations
    
    def has_folder(self, folder_path: str) -> bool:
        """Check if folder path is already being watched."""
        abs_path = os.path.abspath(folder_path)
        return any(folder.path == abs_path for folder in self.folders)
    
    def get_folder_by_path(self, folder_path: str) -> Optional[AnimationFolder]:
        """Get folder by path."""
        abs_path = os.path.abspath(folder_path)
        for folder in self.folders:
            if folder.path == abs_path:
                return folder
        return None
    
    def is_folder_tracked(self, folder_path: str) -> bool:
        """Check if a folder is already being tracked."""
        return self.has_folder(folder_path)
    
    def refresh_folder(self, folder_path: str) -> bool:
        """Refresh animations in a specific folder.
        
        Args:
            folder_path: Path to the folder to refresh
            
        Returns:
            True if folder was found and refreshed, False otherwise
        """
        folder = self.get_folder_by_path(folder_path)
        if not folder:
            return False
        
        # Remove old animations from cache
        for animation in folder.animations:
            self.animation_cache.pop(animation.filepath, None)
        
        # Rescan folder
        animation_count = folder.scan_for_animations()
        
        # Update cache with new animations
        for animation in folder.animations:
            self.animation_cache[animation.filepath] = animation
        
        print(f"Refreshed folder '{folder.name}': {animation_count} animations")
        return True
    
    def validate_animation_file(self, filepath: str) -> bool:
        """Validate that a file contains valid animation data."""
        return validate_animation_file(filepath)


def validate_animation_file(filepath: str) -> bool:
    """Validate JSON file contains valid animation structure.
    
    Args:
        filepath: Path to JSON file to validate
        
    Returns:
        True if file contains valid animation data, False otherwise
    """
    required_fields = ["animation", "sheet", "frame_size", "frames"]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required fields exist
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate frames is a non-empty list
        frames = data.get("frames", [])
        if not isinstance(frames, list) or len(frames) == 0:
            return False
        
        # Validate at least one frame has required frame fields
        if frames:
            first_frame = frames[0]
            required_frame_fields = ["x", "y", "w", "h"]
            for field in required_frame_fields:
                if field not in first_frame:
                    return False
        
        return True
        
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return False


def extract_animation_metadata(filepath: str) -> dict:
    """Extract key metadata without loading full animation.
    
    Args:
        filepath: Path to animation JSON file
        
    Returns:
        Dictionary with extracted metadata
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'name': data.get('animation', 'Unnamed'),
            'spritesheet_path': data.get('sheet', ''),
            'frame_count': len(data.get('frames', [])),
            'frame_size': data.get('frame_size', [0, 0]),
            'margin': data.get('margin', 0),
            'spacing': data.get('spacing', 0),
            'order': data.get('order', 'selection-order')
        }
        
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return {
            'name': 'Invalid',
            'spritesheet_path': '',
            'frame_count': 0,
            'frame_size': [0, 0],
            'margin': 0,
            'spacing': 0,
            'order': 'unknown'
        }


# Test function for development
def test_animation_manager():
    """Test function for the animation manager system."""
    print("Testing Animation Manager System")
    print("=" * 40)
    
    # Create manager
    manager = AnimationManager()
    
    # Test with current directory (should be safe)
    test_dir = os.getcwd()
    print(f"Testing with directory: {test_dir}")
    
    # Add folder
    folder = manager.add_folder(test_dir, "Test Folder")
    if folder:
        print(f"Successfully added folder: {folder.name}")
        print(f"Found {len(folder.animations)} animations")
        
        for animation in folder.animations[:3]:  # Show first 3
            print(f"  - {animation.name} ({animation.frame_count} frames)")
    
    print("Animation Manager test completed!")


if __name__ == "__main__":
    # Run test when executed directly
    test_animation_manager()
