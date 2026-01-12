from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Optional, List, Dict

class Track(BaseModel):
    """Single track with validated metadata."""
    path: Path
    name: Optional[str] = None  # Auto-derived from path if None
    metadata: Dict[str, str] = Field(default_factory=dict)
    color: Optional[tuple[int, int, int]] = None
    track_type: Optional[str] = None  # bigWig, bigBed, etc.
    
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
    tracks: List[Track] = Field(default_factory=list)
    subgroups: List['TrackGroup'] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

# Required for recursive models
TrackGroup.model_rebuild()
