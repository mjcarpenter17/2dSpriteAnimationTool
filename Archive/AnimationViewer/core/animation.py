"""
Animation management system for the sprite animation tool.
"""
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnimationMetadata:
    """Metadata for an animation."""
    name: str
    spritesheet_id: str
    frame_count: int
    filepath: str
    created: datetime
    modified: datetime
    tags: List[str]


class Animation:
    """
    Represents an animation with frames, timing, and export settings.
    """
    
    def __init__(self, name: str, spritesheet_id: str):
        """
        Initialize an animation.
        
        Args:
            name: Animation name
            spritesheet_id: ID of the source sprite sheet
        """
        self.name = name
        self.spritesheet_id = spritesheet_id
        self.frames: List[Tuple[int, int]] = []  # List of (row, col) tuples
        self.frame_durations: List[int] = []     # Duration in milliseconds per frame
        self.loop_settings = {
            "loop": True,
            "bounce": False,
            "single_play": False
        }
        self.export_settings = {
            "format": "json",
            "include_trim": True,
            "include_pivots": True
        }
        self.metadata = {
            "created": datetime.now(),
            "modified": datetime.now(),
            "tags": []
        }
    
    def add_frame(self, row: int, col: int, duration: int = 100):
        """
        Add a frame to the animation.
        
        Args:
            row: Frame row in sprite sheet
            col: Frame column in sprite sheet  
            duration: Frame duration in milliseconds
        """
        self.frames.append((row, col))
        self.frame_durations.append(duration)
        self.metadata["modified"] = datetime.now()
    
    def remove_frame(self, index: int):
        """Remove a frame from the animation by index."""
        if 0 <= index < len(self.frames):
            self.frames.pop(index)
            self.frame_durations.pop(index)
            self.metadata["modified"] = datetime.now()
    
    def set_frames(self, frames: List[Tuple[int, int]], default_duration: int = 100):
        """
        Set all frames at once.
        
        Args:
            frames: List of (row, col) tuples
            default_duration: Default duration for all frames
        """
        self.frames = frames.copy()
        self.frame_durations = [default_duration] * len(frames)
        self.metadata["modified"] = datetime.now()
    
    def get_total_duration(self) -> int:
        """Get total animation duration in milliseconds."""
        return sum(self.frame_durations)
    
    def get_fps(self) -> float:
        """Get average FPS of the animation."""
        if not self.frame_durations:
            return 0.0
        avg_duration = sum(self.frame_durations) / len(self.frame_durations)
        return 1000.0 / avg_duration if avg_duration > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert animation to dictionary for serialization."""
        return {
            "name": self.name,
            "spritesheet_id": self.spritesheet_id,
            "frames": self.frames,
            "frame_durations": self.frame_durations,
            "loop_settings": self.loop_settings,
            "export_settings": self.export_settings,
            "metadata": {
                "created": self.metadata["created"].isoformat(),
                "modified": self.metadata["modified"].isoformat(),
                "tags": self.metadata["tags"]
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Animation':
        """Create animation from dictionary."""
        anim = cls(data["name"], data["spritesheet_id"])
        anim.frames = data.get("frames", [])
        anim.frame_durations = data.get("frame_durations", [])
        anim.loop_settings = data.get("loop_settings", anim.loop_settings)
        anim.export_settings = data.get("export_settings", anim.export_settings)
        
        metadata = data.get("metadata", {})
        if "created" in metadata:
            anim.metadata["created"] = datetime.fromisoformat(metadata["created"])
        if "modified" in metadata:
            anim.metadata["modified"] = datetime.fromisoformat(metadata["modified"])
        if "tags" in metadata:
            anim.metadata["tags"] = metadata["tags"]
        
        return anim


class AnimationManager:
    """
    Manages animation discovery, loading, and organization.
    """
    
    def __init__(self):
        """Initialize the animation manager."""
        self.animations: Dict[str, Animation] = {}
        self.animation_files: Dict[str, str] = {}  # animation_id -> filepath
    
    def scan_directory(self, directory: str) -> List[str]:
        """
        Scan directory for animation JSON files.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of discovered animation file paths
        """
        discovered = []
        
        if not os.path.exists(directory):
            return discovered
        
        try:
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    filepath = os.path.join(directory, filename)
                    if self._is_animation_file(filepath):
                        discovered.append(filepath)
        except OSError:
            pass  # Handle permission errors gracefully
        
        return discovered
    
    def _is_animation_file(self, filepath: str) -> bool:
        """Check if a JSON file is a valid animation file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for required animation fields
            required_fields = ["animation", "frames"]
            return all(field in data for field in required_fields)
        except Exception:
            return False
    
    def load_animation(self, filepath: str) -> Optional[str]:
        """
        Load an animation from a JSON file.
        
        Args:
            filepath: Path to animation file
            
        Returns:
            Animation ID if successful, None otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract animation metadata
            name = data.get("animation", os.path.splitext(os.path.basename(filepath))[0])
            spritesheet_path = data.get("sheet", "")
            
            # Create animation object
            animation = Animation(name, spritesheet_path)
            
            # Load frames (convert from old format if needed)
            frames_data = data.get("frames", [])
            if frames_data and isinstance(frames_data[0], dict):
                # New format with frame objects
                frames = [(f.get("row", 0), f.get("col", 0)) for f in frames_data]
            else:
                # Old format - need to compute from frame indices
                frame_size = data.get("frame_size", [90, 37])
                margin = data.get("margin", 0)
                spacing = data.get("spacing", 0)
                frames = self._compute_frames_from_indices(frames_data, frame_size, margin, spacing)
            
            animation.set_frames(frames)
            
            # Generate unique animation ID
            animation_id = f"{name}_{hash(filepath) & 0x7FFFFFFF}"
            
            # Store animation
            self.animations[animation_id] = animation
            self.animation_files[animation_id] = filepath
            
            return animation_id
            
        except Exception as e:
            print(f"Failed to load animation from {filepath}: {e}")
            return None
    
    def _compute_frames_from_indices(self, indices: List[int], frame_size: List[int], 
                                   margin: int, spacing: int) -> List[Tuple[int, int]]:
        """Convert frame indices to (row, col) tuples."""
        # This is a simplified conversion - would need sprite sheet dimensions for accuracy
        frames = []
        for idx in indices:
            # Assume a reasonable grid width for conversion
            col = idx % 10  # Placeholder logic
            row = idx // 10
            frames.append((row, col))
        return frames
    
    def get_animations_by_spritesheet(self, spritesheet_id: str) -> List[str]:
        """
        Get all animation IDs for a specific sprite sheet.
        
        Args:
            spritesheet_id: Sprite sheet identifier
            
        Returns:
            List of animation IDs
        """
        return [aid for aid, anim in self.animations.items() 
                if anim.spritesheet_id == spritesheet_id]
    
    def get_animation_metadata(self, animation_id: str) -> Optional[AnimationMetadata]:
        """Get metadata for an animation."""
        if animation_id not in self.animations:
            return None
        
        anim = self.animations[animation_id]
        filepath = self.animation_files.get(animation_id, "")
        
        return AnimationMetadata(
            name=anim.name,
            spritesheet_id=anim.spritesheet_id,
            frame_count=len(anim.frames),
            filepath=filepath,
            created=anim.metadata["created"],
            modified=anim.metadata["modified"],
            tags=anim.metadata["tags"]
        )
    
    def save_animation(self, animation_id: str, filepath: str = None) -> bool:
        """
        Save an animation to a JSON file.
        
        Args:
            animation_id: Animation to save
            filepath: File path (uses existing if None)
            
        Returns:
            True if successful
        """
        if animation_id not in self.animations:
            return False
        
        if filepath is None:
            filepath = self.animation_files.get(animation_id)
            if not filepath:
                return False
        
        try:
            animation = self.animations[animation_id]
            data = animation.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.animation_files[animation_id] = filepath
            return True
            
        except Exception as e:
            print(f"Failed to save animation {animation_id}: {e}")
            return False
    
    def delete_animation(self, animation_id: str) -> bool:
        """
        Delete an animation.
        
        Args:
            animation_id: Animation to delete
            
        Returns:
            True if successful
        """
        if animation_id in self.animations:
            del self.animations[animation_id]
            if animation_id in self.animation_files:
                del self.animation_files[animation_id]
            return True
        return False
    
    def discover_animations(self, base_directory: str = ".") -> List[Dict[str, Any]]:
        """
        Discover animations in the directory and return their metadata.
        
        Args:
            base_directory: Base directory to scan for animations
            
        Returns:
            List of animation metadata dictionaries
        """
        discovered = []
        
        # Scan for animation files
        animation_files = self.scan_directory(base_directory)
        
        for filepath in animation_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract metadata
                animation_data = {
                    'name': data.get('animation', os.path.splitext(os.path.basename(filepath))[0]),
                    'filepath': filepath,
                    'source_sheet': data.get('sheet', ''),
                    'frame_count': len(data.get('frames', [])),
                    'format': data.get('format', 'unknown'),
                    'modified': os.path.getmtime(filepath) if os.path.exists(filepath) else 0
                }
                
                discovered.append(animation_data)
                
            except Exception as e:
                # Add invalid file info for troubleshooting
                discovered.append({
                    'name': os.path.splitext(os.path.basename(filepath))[0],
                    'filepath': filepath,
                    'source_sheet': '',
                    'frame_count': 0,
                    'format': 'invalid',
                    'error': str(e),
                    'modified': 0
                })
        
        return discovered
    
    def get_all_animation_ids(self) -> List[str]:
        """Get all animation IDs."""
        return list(self.animations.keys())
    
    def get_animation(self, animation_id: str) -> Optional[Animation]:
        """Get an animation object by ID."""
        return self.animations.get(animation_id)
