import pathlib
from typing import List, Union, Callable, Dict, Any, Optional
import pandas as pd
from .models import Track, TrackGroup
from .schemas import TrackDataFrameSchema, TrackDesignSchema
from .api import TrackDesign, HubGenerator
from loguru import logger

from pydantic import BaseModel, Field
import json

from pydantic import BaseModel, Field, ConfigDict
import json

class HubBuilder(BaseModel):
    """Fluent API for building UCSC track hubs.
    
    Now a Pydantic model for EASY serialization.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    tracks: List[Track] = Field(default_factory=list)
    group_by_cols: List[str] = Field(default_factory=list)
    supergroup_by_cols: List[str] = Field(default_factory=list)
    overlay_by_cols: List[str] = Field(default_factory=list)
    color_by_col: Optional[str] = Field(None)
    color_palette: str = Field("tab20")
    
    # Non-serialized field for extractors (functions can't be JSON serialized easily)
    metadata_extractors: List[Callable[[pathlib.Path], Dict[str, str]]] = Field(default_factory=list, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        
    def add_tracks(self, paths: Union[List[str], List[pathlib.Path]], **common_metadata) -> 'HubBuilder':
        """Add multiple tracks from paths."""
        for p in paths:
            path = pathlib.Path(p)
            self.tracks.append(Track(path=path, metadata=common_metadata.copy()))
        return self
        
    def add_tracks_from_df(self, df: pd.DataFrame, fn_col='fn') -> 'HubBuilder':
        """Add tracks from a pandas DataFrame."""
        try:
            df = TrackDataFrameSchema.validate(df)
        except Exception as e:
            logger.warning(f"DataFrame validation failed: {e}")

        for _, row in df.iterrows():
            path = pathlib.Path(row[fn_col])
            metadata = {k: str(v) for k, v in row.items() if k != fn_col}
            self.tracks.append(Track(path=path, metadata=metadata))
        return self
        
    def with_metadata_extractor(self, fn: Callable[[pathlib.Path], Dict[str, str]]) -> 'HubBuilder':
        """Add a metadata extractor function."""
        self.metadata_extractors.append(fn)
        return self
        
    def group_by(self, *columns: str, as_supertrack: bool = False) -> 'HubBuilder':
        """Specify columns to group by."""
        if as_supertrack:
            self.supergroup_by_cols.extend(columns)
        else:
            self.group_by_cols.extend(columns)
        return self
        
    def color_by(self, column: str, palette: str = 'tab20') -> 'HubBuilder':
        """Specify column for track coloring."""
        self.color_by_col = column
        self.color_palette = palette
        return self
        
    def overlay_by(self, *columns: str) -> 'HubBuilder':
        """Specify columns for overlay tracks."""
        self.overlay_by_cols.extend(columns)
        return self
        
    def merge(self, *others: 'HubBuilder') -> 'HubBuilder':
        """Merge other HubBuilders into this one, reconciliating settings."""
        for other in others:
            self.tracks.extend(other.tracks)
            # Union of grouping columns
            self.group_by_cols = sorted(list(set(self.group_by_cols + other.group_by_cols)))
            self.supergroup_by_cols = sorted(list(set(self.supergroup_by_cols + other.supergroup_by_cols)))
            self.overlay_by_cols = sorted(list(set(self.overlay_by_cols + other.overlay_by_cols)))
            # Colors: use other's if not set here
            if not self.color_by_col:
                self.color_by_col = other.color_by_col
                self.color_palette = other.color_palette
        return self

    def to_json(self, path: Optional[Union[str, pathlib.Path]] = None) -> str:
        """Serialize state to JSON string or file."""
        data = self.model_dump_json(indent=2, by_alias=True)
        if path:
            with open(path, 'w') as f:
                f.write(data)
        return data
        
    @classmethod
    def from_json(cls, path_or_data: Union[str, pathlib.Path]) -> 'HubBuilder':
        """Reconstruct builder from JSON string or file path."""
        p = pathlib.Path(path_or_data)
        if p.exists() and p.is_file():
            with open(p, 'r') as f:
                data = f.read()
        else:
            data = path_or_data
        return cls.model_validate_json(data)
        
    def _prepare_design_df(self) -> pd.DataFrame:
        """Convert tracks to the DataFrame format used by TrackDesign."""
        data = []
        for track in self.tracks:
            track_metadata = track.metadata.copy()
            for extractor in self.metadata_extractors:
                extracted = extractor(track.path)
                track_metadata.update(extracted)
            
            row = {
                "fn": str(track.path),
                "path": str(track.path.absolute().resolve()),
                "name": track.name or track.path.stem,
                "ext": track.track_type or track.path.suffix.strip(".")
            }
            row.update(track_metadata)
            data.append(row)
            
        return pd.DataFrame(data)
        
    def build(self, name: str, genome: str, outdir: Union[str, pathlib.Path], hub_email: str = "", **kwargs) -> Any:
        """Build the hub and export sidecar config."""
        outdir = pathlib.Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        
        # Save sidecar config
        self.to_json(outdir / "tracknado_config.json")
        
        df = self._prepare_design_df()
        
        design = TrackDesign.from_design(
            df,
            color_by=self.color_by_col,
            subgroup_by=self.group_by_cols if self.group_by_cols else None,
            supergroup_by=self.supergroup_by_cols if self.supergroup_by_cols else None,
            overlay_by=self.overlay_by_cols if self.overlay_by_cols else None,
            **kwargs
        )
        
        hub = HubGenerator(
            hub_name=name,
            genome=genome,
            track_design=design,
            outdir=outdir,
            hub_email=hub_email,
            **kwargs
        )
        
        return hub
