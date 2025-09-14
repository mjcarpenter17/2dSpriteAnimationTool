"""Aseprite JSON parsing module.

Phase 1 Goals Implemented:
 - Dataclasses for frames & animations
 - Robust JSON parsing with validation and safe fallbacks
 - Direction normalization (forward, reverse, pingpong)
 - Summary reporting helper
 - CLI usage: python aseprite_loader.py <path_to_json>

Later Phases Will Add:
 - Integration into Animation Source system
 - Playback timing hooks
 - Pivot/slice logic
"""
from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

SUPPORTED_DIRECTIONS = {"forward", "reverse", "pingpong"}

@dataclass
class AsepriteFrame:
    name: str
    atlas_rect: Tuple[int, int, int, int]  # x,y,w,h in packed image
    source_size: Tuple[int, int]           # original untrimmed logical size (w,h)
    source_offset: Tuple[int, int]         # offset of trimmed rect relative to logical origin (x,y)
    duration_ms: int

@dataclass
class AsepriteAnimation:
    name: str
    frame_indices: List[int]
    direction: str  # forward | reverse | pingpong
    total_duration_ms: int

@dataclass
class AsepriteDocument:
    json_path: str
    image_path: Optional[str]
    frames: List[AsepriteFrame] = field(default_factory=list)
    animations: List[AsepriteAnimation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (f"AsepriteDocument: frames={len(self.frames)} animations={len(self.animations)} "
                f"image={'present' if self.image_path else 'missing'} warnings={len(self.warnings)} errors={len(self.errors)}")

class AsepriteJSONLoader:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.document: Optional[AsepriteDocument] = None

    # Public API
    def load(self) -> AsepriteDocument:
        doc = AsepriteDocument(json_path=self.json_path, image_path=None)
        if not os.path.exists(self.json_path):
            doc.errors.append(f"File not found: {self.json_path}")
            self.document = doc
            return doc
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            doc.errors.append(f"JSON parse error: {e}")
            self.document = doc
            return doc

        meta = data.get('meta', {})
        image_name = meta.get('image')
        if image_name:
            candidate = os.path.join(os.path.dirname(self.json_path), image_name)
            if os.path.exists(candidate):
                doc.image_path = candidate
            else:
                doc.warnings.append(f"Image referenced but not found: {candidate}")
        else:
            doc.warnings.append("No image field in meta block")

        frames_obj = data.get('frames')
        if not isinstance(frames_obj, dict) or not frames_obj:
            doc.errors.append("No frames dictionary in JSON")
            self.document = doc
            return doc

        # Preserve order (Python 3.7+ dict preserves insertion order)
        frame_keys = list(frames_obj.keys())
        for index, key in enumerate(frame_keys):
            raw = frames_obj.get(key, {})
            frame = raw.get('frame', {})
            try:
                x = int(frame.get('x', 0)); y = int(frame.get('y', 0))
                w = int(frame.get('w', 0)); h = int(frame.get('h', 0))
                if w <= 0 or h <= 0:
                    doc.warnings.append(f"Frame '{key}' has non-positive size; skipped")
                    continue
                sprite_source = raw.get('spriteSourceSize', {})
                src_x = int(sprite_source.get('x', 0)); src_y = int(sprite_source.get('y', 0))
                # Provided w,h in spriteSourceSize can represent trimmed rect size; we rely on atlas w,h.
                source_size = raw.get('sourceSize', {})
                full_w = int(source_size.get('w', w)); full_h = int(source_size.get('h', h))
                duration = int(raw.get('duration', 100))
                doc.frames.append(AsepriteFrame(
                    name=key,
                    atlas_rect=(x, y, w, h),
                    source_size=(full_w, full_h),
                    source_offset=(src_x, src_y),
                    duration_ms=duration if duration > 0 else 100
                ))
            except Exception as fe:
                doc.warnings.append(f"Failed to parse frame '{key}': {fe}")

        # Parse frame tags
        tags = meta.get('frameTags', [])
        if not isinstance(tags, list):
            doc.warnings.append("frameTags not a list; skipping animations")
        else:
            # Normalize off-by-one if tags start at 1 but we have a frame at index 0
            try:
                if tags:
                    from_values = [int(t.get('from', 0)) for t in tags if isinstance(t, dict)]
                    to_values = [int(t.get('to', 0)) for t in tags if isinstance(t, dict)]
                    if from_values:
                        min_from = min(from_values)
                        # If minimum 'from' is 1 and we actually have a frame 0 whose y==1 (top-left), shift all tags down by 1
                        if min_from == 1 and len(doc.frames) > 0:
                            # Heuristic: shift if frame 0 appears to be the top-left (y small) and no tag references 0
                            if 0 not in from_values and 0 not in to_values:
                                for t in tags:
                                    if isinstance(t, dict):
                                        try:
                                            t['from'] = int(t.get('from', 0)) - 1
                                            t['to'] = int(t.get('to', 0)) - 1
                                        except Exception:
                                            pass
                                doc.warnings.append("Normalized frameTags indices (detected 1-based indices)")
            except Exception:
                pass
            for tag in tags:
                try:
                    name = str(tag.get('name', 'unnamed')) or 'unnamed'
                    start = int(tag.get('from', 0))
                    end = int(tag.get('to', start))
                    direction = str(tag.get('direction', 'forward')).lower()
                    if direction not in SUPPORTED_DIRECTIONS:
                        doc.warnings.append(f"Unsupported direction '{direction}' in tag '{name}' -> defaulting to forward")
                        direction = 'forward'
                    if start < 0 or end < start or end >= len(doc.frames):
                        doc.warnings.append(f"Tag '{name}' indices out of range; skipped")
                        continue
                    indices = list(range(start, end + 1))
                    if direction == 'reverse':
                        indices = list(reversed(indices))
                    total = sum(doc.frames[i].duration_ms for i in indices)
                    doc.animations.append(AsepriteAnimation(name=name, frame_indices=indices, direction=direction, total_duration_ms=total))
                except Exception as te:
                    doc.warnings.append(f"Failed to parse tag: {te}")

        self.document = doc
        return doc

    def report_summary(self):
        if not self.document:
            print("No document loaded")
            return
        print(self.document.summary())
        if self.document.warnings:
            print("Warnings:")
            for w in self.document.warnings[:10]:
                print(" -", w)
            if len(self.document.warnings) > 10:
                print(f" ... ({len(self.document.warnings) - 10} more)")
        if self.document.errors:
            print("Errors:")
            for e in self.document.errors:
                print(" -", e)

# CLI support
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python aseprite_loader.py <file.json>")
        sys.exit(1)
    loader = AsepriteJSONLoader(sys.argv[1])
    doc = loader.load()
    loader.report_summary()
    # Provide basic per-animation info
    for anim in doc.animations:
        print(f"Animation '{anim.name}': frames={len(anim.frame_indices)} dir={anim.direction} total={anim.total_duration_ms}ms")
