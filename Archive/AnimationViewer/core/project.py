"""
Project management system for sprite animation projects.
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .sprite_manager import SpriteSheetManager
from .animation import AnimationManager


@dataclass
class ProjectSettings:
    """Project-wide settings and preferences."""
    name: str
    version: str
    created: datetime
    modified: datetime
    default_export_path: str
    default_fps: int
    auto_save: bool
    recent_files: List[str]


class AnimationProject:
    """
    Manages an animation project with multiple sprite sheets and animations.
    """
    
    def __init__(self, name: str = "Untitled Project"):
        """
        Initialize a new animation project.
        
        Args:
            name: Project name
        """
        self.settings = ProjectSettings(
            name=name,
            version="1.0",
            created=datetime.now(),
            modified=datetime.now(),
            default_export_path="exports/",
            default_fps=10,
            auto_save=True,
            recent_files=[]
        )
        
        # Core managers
        self.sprite_manager = SpriteSheetManager()
        self.animation_manager = AnimationManager()
        
        # Project state
        self.project_filepath: Optional[str] = None
        self.has_unsaved_changes: bool = False
    
    def create_new_project(self, name: str):
        """
        Create a new project, clearing all existing data.
        
        Args:
            name: New project name
        """
        # Clear existing data
        self.sprite_manager.clear_all_sheets()
        self.animation_manager = AnimationManager()
        
        # Reset settings
        self.settings = ProjectSettings(
            name=name,
            version="1.0",
            created=datetime.now(),
            modified=datetime.now(),
            default_export_path="exports/",
            default_fps=10,
            auto_save=True,
            recent_files=[]
        )
        
        self.project_filepath = None
        self.has_unsaved_changes = True
    
    def load_project(self, filepath: str) -> bool:
        """
        Load a project from a file.
        
        Args:
            filepath: Project file path
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load project settings
            project_data = data.get("project", {})
            self.settings.name = project_data.get("name", "Loaded Project")
            self.settings.version = project_data.get("version", "1.0")
            
            # Parse dates
            if "created" in project_data:
                self.settings.created = datetime.fromisoformat(project_data["created"])
            if "modified" in project_data:
                self.settings.modified = datetime.fromisoformat(project_data["modified"])
            
            # Load preferences
            prefs = data.get("preferences", {})
            self.settings.default_export_path = prefs.get("default_export_path", "exports/")
            self.settings.default_fps = prefs.get("default_fps", 10)
            self.settings.auto_save = prefs.get("auto_save", True)
            
            # Clear existing data
            self.sprite_manager.clear_all_sheets()
            self.animation_manager = AnimationManager()
            
            # Load sprite sheets
            for sheet_data in data.get("spritesheets", []):
                self._load_spritesheet_from_data(sheet_data)
            
            # Load animations
            for anim_data in data.get("animations", []):
                self._load_animation_from_data(anim_data)
            
            self.project_filepath = filepath
            self.has_unsaved_changes = False
            
            return True
            
        except Exception as e:
            print(f"Failed to load project {filepath}: {e}")
            return False
    
    def _load_spritesheet_from_data(self, sheet_data: Dict[str, Any]):
        """Load a sprite sheet from project data."""
        filepath = sheet_data.get("filepath", "")
        name = sheet_data.get("name", "")
        tile_size = tuple(sheet_data.get("tile_size", [32, 32]))
        margin = sheet_data.get("margin", 0)
        spacing = sheet_data.get("spacing", 0)
        
        # Try to load the sprite sheet
        if os.path.exists(filepath):
            self.sprite_manager.load_sprite_sheet(filepath, tile_size, margin, spacing, name)
        else:
            print(f"Warning: Sprite sheet not found: {filepath}")
    
    def _load_animation_from_data(self, anim_data: Dict[str, Any]):
        """Load an animation from project data."""
        anim_id = anim_data.get("id", "")
        name = anim_data.get("name", "")
        spritesheet_id = anim_data.get("spritesheet_id", "")
        anim_filepath = anim_data.get("filepath", "")
        
        # Try to load the animation file
        if os.path.exists(anim_filepath):
            loaded_id = self.animation_manager.load_animation(anim_filepath)
            if loaded_id:
                print(f"Loaded animation: {name}")
        else:
            print(f"Warning: Animation file not found: {anim_filepath}")
    
    def save_project(self, filepath: str = None) -> bool:
        """
        Save the project to a file.
        
        Args:
            filepath: File path (uses existing if None)
            
        Returns:
            True if successful
        """
        if filepath is None:
            filepath = self.project_filepath
            if not filepath:
                return False
        
        try:
            # Prepare project data
            project_data = {
                "project": {
                    "name": self.settings.name,
                    "version": self.settings.version,
                    "created": self.settings.created.isoformat(),
                    "modified": datetime.now().isoformat()
                },
                "spritesheets": self._serialize_spritesheets(),
                "animations": self._serialize_animations(),
                "preferences": {
                    "default_export_path": self.settings.default_export_path,
                    "default_fps": self.settings.default_fps,
                    "auto_save": self.settings.auto_save
                }
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write project file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)
            
            self.project_filepath = filepath
            self.has_unsaved_changes = False
            
            return True
            
        except Exception as e:
            print(f"Failed to save project {filepath}: {e}")
            return False
    
    def _serialize_spritesheets(self) -> List[Dict[str, Any]]:
        """Serialize sprite sheets for project saving."""
        sheets_data = []
        for sheet_id in self.sprite_manager.get_all_sheet_ids():
            sheet_info = self.sprite_manager.get_sheet_info(sheet_id)
            if sheet_info:
                sheets_data.append({
                    "id": sheet_id,
                    "filepath": sheet_info["filepath"],
                    "name": sheet_info["name"],
                    "tile_size": list(sheet_info["tile_size"]),
                    "margin": sheet_info["margin"],
                    "spacing": sheet_info["spacing"]
                })
        return sheets_data
    
    def _serialize_animations(self) -> List[Dict[str, Any]]:
        """Serialize animations for project saving."""
        anims_data = []
        for anim_id in self.animation_manager.get_all_animation_ids():
            metadata = self.animation_manager.get_animation_metadata(anim_id)
            if metadata:
                anims_data.append({
                    "id": anim_id,
                    "name": metadata.name,
                    "spritesheet_id": metadata.spritesheet_id,
                    "filepath": metadata.filepath
                })
        return anims_data
    
    def discover_animations(self, directory: str = None) -> int:
        """
        Discover animations in a directory.
        
        Args:
            directory: Directory to scan (uses current directory if None)
            
        Returns:
            Number of animations discovered
        """
        if directory is None:
            directory = os.getcwd()
        
        animation_files = self.animation_manager.scan_directory(directory)
        loaded_count = 0
        
        for filepath in animation_files:
            animation_id = self.animation_manager.load_animation(filepath)
            if animation_id:
                loaded_count += 1
        
        if loaded_count > 0:
            self.has_unsaved_changes = True
        
        return loaded_count
    
    def add_recent_file(self, filepath: str):
        """Add a file to recent files list."""
        if filepath in self.settings.recent_files:
            self.settings.recent_files.remove(filepath)
        
        self.settings.recent_files.insert(0, filepath)
        
        # Keep only last 10 recent files
        self.settings.recent_files = self.settings.recent_files[:10]
        
        # Remove non-existent files
        self.settings.recent_files = [f for f in self.settings.recent_files if os.path.exists(f)]
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics."""
        return {
            "sprite_sheets": len(self.sprite_manager),
            "animations": len(self.animation_manager.get_all_animation_ids()),
            "memory_usage": self.sprite_manager.get_memory_usage(),
            "has_unsaved_changes": self.has_unsaved_changes,
            "project_filepath": self.project_filepath
        }
    
    def validate_project(self) -> List[str]:
        """
        Validate the project and return any issues found.
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check sprite sheets
        validation_results = self.sprite_manager.validate_all_sheets()
        for sheet_id, warnings in validation_results.items():
            for warning in warnings:
                issues.append(f"Sprite sheet '{sheet_id}': {warning}")
        
        # Check for animations without sprite sheets
        for anim_id in self.animation_manager.get_all_animation_ids():
            metadata = self.animation_manager.get_animation_metadata(anim_id)
            if metadata and metadata.spritesheet_id not in self.sprite_manager:
                issues.append(f"Animation '{metadata.name}' references missing sprite sheet")
        
        return issues
    
    def export_animation(self, animation_id: str, export_path: str, 
                        format_type: str = "json") -> bool:
        """
        Export an animation to file.
        
        Args:
            animation_id: Animation to export
            export_path: Export file path
            format_type: Export format ("json", "python", etc.)
            
        Returns:
            True if successful
        """
        animation = self.animation_manager.get_animation(animation_id)
        if not animation:
            return False
        
        # Get associated sprite sheet
        sprite_sheet = None
        for sheet_id in self.sprite_manager.get_all_sheet_ids():
            sheet_info = self.sprite_manager.get_sheet_info(sheet_id)
            if sheet_info and sheet_info["filepath"] == animation.spritesheet_id:
                sprite_sheet = self.sprite_manager.get_sprite_sheet(sheet_id)
                break
        
        if not sprite_sheet:
            print(f"Cannot export animation: sprite sheet not found")
            return False
        
        try:
            if format_type == "json":
                return self._export_animation_json(animation, sprite_sheet, export_path)
            elif format_type == "python":
                return self._export_animation_python(animation, sprite_sheet, export_path)
            else:
                print(f"Unsupported export format: {format_type}")
                return False
                
        except Exception as e:
            print(f"Failed to export animation: {e}")
            return False
    
    def _export_animation_json(self, animation, sprite_sheet, filepath: str) -> bool:
        """Export animation as JSON (legacy format)."""
        # Build frame data with analysis
        frames_data = []
        for row, col in animation.frames:
            analysis = sprite_sheet.analyze_frame(row, col)
            if analysis:
                frame_rect = sprite_sheet.get_frame_rect(row, col)
                frames_data.append({
                    "x": frame_rect.x,
                    "y": frame_rect.y,
                    "w": frame_rect.width,
                    "h": frame_rect.height,
                    "row": row,
                    "col": col,
                    "trimmed": {
                        "x": analysis["trim_rect"][0],
                        "y": analysis["trim_rect"][1],
                        "w": analysis["trim_rect"][2],
                        "h": analysis["trim_rect"][3]
                    },
                    "offset": {
                        "x": analysis["offset"][0],
                        "y": analysis["offset"][1]
                    },
                    "pivot": {
                        "x": analysis["pivot"][0],
                        "y": analysis["pivot"][1]
                    }
                })
        
        export_data = {
            "animation": animation.name,
            "sheet": os.path.relpath(sprite_sheet.filepath, os.path.dirname(filepath)),
            "frame_size": list(sprite_sheet.tile_size),
            "margin": sprite_sheet.margin,
            "spacing": sprite_sheet.spacing,
            "rows": sprite_sheet.rows,
            "cols": sprite_sheet.cols,
            "order": "selection-order",
            "frames": frames_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        return True
    
    def _export_animation_python(self, animation, sprite_sheet, filepath: str) -> bool:
        """Export animation as Python module (legacy format)."""
        # This would implement the Python export format from the original viewer
        # For now, just create a basic Python file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Auto-generated animation: {animation.name}\n")
            f.write(f"ANIMATION = '{animation.name}'\n")
            f.write(f"SHEET = '{sprite_sheet.filepath}'\n")
            f.write(f"FRAME_SIZE = {sprite_sheet.tile_size}\n")
            f.write(f"FRAMES = {animation.frames}\n")
        
        return True
