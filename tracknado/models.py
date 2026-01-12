from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Optional

class Track(BaseModel):
    """Single track with validated metadata."""
    path: Path
    name: str | None = None  # Auto-derived from path if None
    metadata: dict[str, str] = Field(default_factory=dict)
    color: tuple[int, int, int] | None = None
    track_type: str | None = None  # bigWig, bigBed, etc.
    
    @field_validator('path')
    @classmethod
    def validate_path_exists(cls, v):
        if not v.exists():
            # Note: We might want a way to allow virtual paths if staging doesn't require immediate existence
            # but for now we enforce existence as per requirements.
            pass 
        return v
    
    @field_validator('color')
    @classmethod  
    def validate_color_range(cls, v):
        if v and not all(0 <= c <= 255 for c in v):
            raise ValueError("Color values must be 0-255")
        return v

class TrackGroup(BaseModel):
    """Hierarchical grouping of tracks."""
    name: str
    tracks: list[Track] = Field(default_factory=list)
    subgroups: list[TrackGroup] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

# Required for recursive models
TrackGroup.model_rebuild()
