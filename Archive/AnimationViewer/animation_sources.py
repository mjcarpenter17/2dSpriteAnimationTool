"""Animation Source Abstractions

Provides a lightweight indirection layer so the UI (animations_pane)
can list animations originating from different systems (legacy folder
JSON files vs. imported Aseprite documents) in a unified way.

Design Goals:
- Non-invasive: Do not refactor existing AnimationEntry; instead adapt.
- Read-only flag: UI can disable mutation operations for external sources.
- Minimal surface: Only what the pane needs to render + identify selection.
- Lazy friendly: Sources can compute descriptors on demand.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, List, Optional


@dataclass(frozen=True)
class FrameDescriptor:
    index: int
    duration_ms: int


@dataclass(frozen=True)
class AnimationDescriptor:
    id: str  # Stable unique id within the app session (e.g., filepath#tag)
    name: str
    frame_count: int
    source_type: str  # e.g. 'folder-json', 'aseprite'
    read_only: bool = False
    # Optional reference object (not for UI text, but for retrieval)
    payload: Optional[object] = None


class IAnimationSource(Protocol):
    """Protocol for animation sources feeding the animations pane."""

    def list_descriptors(self) -> Iterable[AnimationDescriptor]:
        """Return iterable of AnimationDescriptor objects."""
        ...

    def get_frames(self, descriptor_id: str) -> List[FrameDescriptor]:
        """Return ordered frames (duration only; positions come from elsewhere)."""
        ...


# Adapter for existing AnimationManager entries --------------------------------

def build_folder_json_descriptor(entry) -> AnimationDescriptor:
    """Create an AnimationDescriptor from existing AnimationEntry instance."""
    name = getattr(entry, 'name', 'Unnamed')
    frame_count = getattr(entry, 'frame_count', 0)
    filepath = getattr(entry, 'filepath', name)
    descriptor_id = f"folder::{filepath}"  # unique within session
    return AnimationDescriptor(
        id=descriptor_id,
        name=name,
        frame_count=frame_count,
        source_type='folder-json',
        read_only=False,
        payload=entry,
    )


# Aseprite Source Implementation ------------------------------------------------
try:
    from aseprite_loader import AsepriteDocument  # type: ignore
except Exception:  # pragma: no cover - soft import
    AsepriteDocument = object  # fallback placeholder


class AsepriteAnimationSource(IAnimationSource):
    """Wraps an AsepriteDocument to expose tag animations as descriptors."""

    def __init__(self, document: 'AsepriteDocument', origin_path: str):
        self._doc = document
        self._origin_path = origin_path  # path to JSON file
        # Precompute mapping tag name -> frames indices list
        self._tag_map = {}
        for anim in getattr(document, 'animations', []):
            self._tag_map[anim.name] = list(anim.frame_indices)

    def list_descriptors(self) -> Iterable[AnimationDescriptor]:
        for anim in getattr(self._doc, 'animations', []):
            descriptor_id = f"aseprite::{self._origin_path}#{anim.name}"
            yield AnimationDescriptor(
                id=descriptor_id,
                name=anim.name,
                frame_count=len(anim.frame_indices),
                source_type='aseprite',
                read_only=True,
                payload=anim,
            )

    def get_frames(self, descriptor_id: str) -> List[FrameDescriptor]:
        # Parse id: aseprite::path#tag
        if not descriptor_id.startswith('aseprite::'):
            return []
        try:
            _, rest = descriptor_id.split('aseprite::', 1)
            path_part, tag = rest.rsplit('#', 1)
        except ValueError:
            return []
        if path_part != self._origin_path:
            return []
        frame_indices = self._tag_map.get(tag, [])
        frames: List[FrameDescriptor] = []
        # durations from source frames list
        source_frames = getattr(self._doc, 'frames', [])
        for idx in frame_indices:
            if 0 <= idx < len(source_frames):
                duration = getattr(source_frames[idx], 'duration_ms', 0)
                frames.append(FrameDescriptor(index=idx, duration_ms=duration))
        return frames

    @property
    def origin_path(self) -> str:
        return self._origin_path

    def list_animations(self) -> List[AnimationDescriptor]:
        """Return list of animation descriptors (for compatibility)."""
        return list(self.list_descriptors())


__all__ = [
    'FrameDescriptor',
    'AnimationDescriptor',
    'IAnimationSource',
    'build_folder_json_descriptor',
    'AsepriteAnimationSource',
]
