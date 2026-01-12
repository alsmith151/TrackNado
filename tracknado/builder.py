from __future__ import annotations
import pathlib
from typing import Callable, Any, Optional
import pandas as pd
from .models import Track, TrackGroup
from .schemas import TrackDataFrameSchema, TrackDesignSchema
from .api import TrackDesign, HubGenerator
from loguru import logger

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

    tracks: list[Track] = Field(default_factory=list)
    group_by_cols: list[str] = Field(default_factory=list)
    supergroup_by_cols: list[str] = Field(default_factory=list)
    overlay_by_cols: list[str] = Field(default_factory=list)
    color_by_col: str | None = Field(None)
    color_palette: str = Field("tab20")
    
    # Conversion settings
    convert_files: bool = Field(False)
    chrom_sizes: Optional[pathlib.Path] = Field(None)
    custom_genome_config: dict[str, Any] = Field(default_factory=dict)
    
    # Non-serialized field for extractors (functions can't be JSON serialized easily)
    metadata_extractors: list[Callable[[pathlib.Path], dict[str, str]]] = Field(default_factory=list, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        
    def add_tracks(self, paths: list[str] | list[pathlib.Path], **common_metadata: str) -> HubBuilder:
        """Add multiple tracks from paths."""
        for p in paths:
            path = pathlib.Path(p)
            self.tracks.append(Track(path=path, metadata=common_metadata.copy()))
        return self
        
    def add_tracks_from_df(self, df: pd.DataFrame, fn_col: str = 'fn') -> HubBuilder:
        """Add tracks from a pandas DataFrame."""
        df = df.copy()
        if fn_col in df.columns and 'ext' not in df.columns:
            df['ext'] = df[fn_col].apply(lambda x: pathlib.Path(x).suffix.strip("."))
            
        try:
            df = TrackDataFrameSchema.validate(df)
        except Exception as e:
            logger.warning(f"DataFrame validation failed: {e}")

        for _, row in df.iterrows():
            path = pathlib.Path(row[fn_col])
            metadata = {k: str(v) for k, v in row.items() if k not in [fn_col, 'ext', 'path', 'name']}
            track = Track(path=path, metadata=metadata)
            if 'name' in row and pd.notna(row['name']): track.name = row['name']
            if 'ext' in row and pd.notna(row['ext']): track.track_type = row['ext']
            self.tracks.append(track)
        return self
        
    def with_metadata_extractor(self, fn: Callable[[pathlib.Path], dict[str, str]]) -> HubBuilder:
        """Add a metadata extractor function."""
        self.metadata_extractors.append(fn)
        return self
        
    def group_by(self, *columns: str, as_supertrack: bool = False) -> 'HubBuilder':
        """Specify columns to group by. If as_supertrack is True, these columns
        will be used for SuperTracks instead of dimensions in a CompositeTrack.
        """
        if as_supertrack:
            self.supergroup_by_cols.extend(columns)
        else:
            self.group_by_cols.extend(columns)
        return self
        
    def with_custom_genome(
        self, 
        name: str, 
        twobit_file: str | pathlib.Path, 
        organism: str, 
        default_position: str = "chr1:1000-2000"
    ) -> 'HubBuilder':
        """Configure a custom genome (Assembly Hub) for this hub."""
        self.custom_genome_config = {
            "custom_genome": True,
            "genome_twobit": str(twobit_file),
            "genome_organism": organism,
            "genome_default_position": default_position
        }
        return self
        
    def color_by(self, column: str, palette: str = 'tab20') -> HubBuilder:
        """Specify column for track coloring."""
        self.color_by_col = column
        self.color_palette = palette
        return self
        
    def overlay_by(self, *columns: str) -> HubBuilder:
        """Specify columns for overlay tracks."""
        self.overlay_by_cols.extend(columns)
        return self

    def with_convert_files(self, enabled: bool = True) -> HubBuilder:
        """Enable or disable implicit track conversion."""
        self.convert_files = enabled
        return self
        
    def with_chrom_sizes(self, path: Union[str, pathlib.Path]) -> HubBuilder:
        """Set the chrom.sizes file for track conversion."""
        self.chrom_sizes = pathlib.Path(path)
        return self
        
    def merge(self, *others: 'HubBuilder') -> HubBuilder:
        """Merge other HubBuilders into this one, reconciling settings."""
        for other in others:
            self.tracks.extend(other.tracks)
            # Union of grouping columns
            self.group_by_cols = sorted(list(set(self.group_by_cols + other.group_by_cols)))
            self.supergroup_by_cols = sorted(list(set(self.supergroup_by_cols + other.supergroup_by_cols)))
            self.overlay_by_cols = sorted(list(set(self.overlay_by_cols + other.overlay_by_cols)))
            # Merge extractors
            for ex in other.metadata_extractors:
                if ex not in self.metadata_extractors:
                    self.metadata_extractors.append(ex)
            # Colors: use other's if not set here
            if not self.color_by_col:
                self.color_by_col = other.color_by_col
                self.color_palette = other.color_palette
        return self

    def to_json(self, path: str | pathlib.Path | None = None) -> str:
        """Serialize state to JSON string or file."""
        data = self.model_dump_json(indent=2, by_alias=True)
        if path:
            with open(path, 'w') as f:
                f.write(data)
        return data
        
    @classmethod
    def from_json(cls, path_or_data: str | pathlib.Path) -> HubBuilder:
        """Reconstruct builder from JSON string or file path."""
        p = pathlib.Path(path_or_data)
        if p.exists() and p.is_file():
            with open(p, 'r') as f:
                data = f.read()
        else:
            data = path_or_data
        return cls.model_validate_json(data)
        
    def _extract_metadata(self):
        """Extract metadata for all tracks using registered extractors."""
        if not self.metadata_extractors:
            return
            
        for track in self.tracks:
            # Use original path if it exists for extraction, as it might have more metadata in its name/path
            # than a temporary converted path.
            path_to_extract = getattr(track, "_original_path", track.path)
            for extractor in self.metadata_extractors:
                extracted = extractor(path_to_extract)
                track.metadata.update(extracted)
                
    def _convert_tracks(self, outdir: pathlib.Path):
        """Convert tracks to UCSC formats (e.g. BED -> BigBed)."""
        from .converters import convert_bed_to_bigbed, convert_gtf_to_biggenepred
        
        if not self.chrom_sizes or not self.chrom_sizes.exists():
            raise ValueError("chrom_sizes must be provided and exist for track conversion")

        conv_dir = outdir / "converted"
        conv_dir.mkdir(parents=True, exist_ok=True)
        
        for track in self.tracks:
            if track.path.suffix.lower() == ".bed":
                logger.info(f"Converting {track.path.name} to BigBed")
                dest = conv_dir / track.path.with_suffix(".bb").name
                # Save original path for metadata extraction if needed later
                track._original_path = track.path
                new_path = convert_bed_to_bigbed(
                    track.path, 
                    self.chrom_sizes, 
                    dest
                )
                track.path = new_path
                track.track_type = "bigBed"
            elif track.path.suffix.lower() in [".gtf", ".gff"]:
                logger.info(f"Converting {track.path.name} to BigGenePred")
                dest = conv_dir / track.path.with_suffix(".bb").name
                track._original_path = track.path
                new_path = convert_gtf_to_biggenepred(
                    track.path,
                    self.chrom_sizes,
                    dest
                )
                track.path = new_path
                track.track_type = "bigGenePred"
        
    def _prepare_design_df(self) -> pd.DataFrame:
        """Convert tracks to the DataFrame format used by TrackDesign."""
        self._extract_metadata()
        
        extension_mapping = {
            "bw": "bigWig",
            "bb": "bigBed",
            "bigbed": "bigBed",
            "bigwig": "bigWig",
            "bed": "bigBed", # Default for .bed is bigBed (assuming conversion)
            "gtf": "bigGenePred",
            "gff": "bigGenePred",
            "biggenepred": "bigGenePred",
            "narrowpeak": "narrowPeak",
            "broadpeak": "broadPeak",
        }
        
        data = []
        for track in self.tracks:
            # Metadata is already extracted in build()
            
            ext = track.track_type or track.path.suffix.lstrip(".")
            ext = extension_mapping.get(ext.lower(), ext)
            
            row = {
                "fn": str(track.path),
                "path": str(track.path.absolute().resolve()),
                "name": track.name or track.path.stem,
                "ext": ext
            }
            row.update(track.metadata)
            data.append(row)
            
        return pd.DataFrame(data)
        
    def build(self, name: str, genome: str, outdir: str | pathlib.Path, hub_email: str = "", **kwargs) -> Any:
        """Build the hub and export sidecar config."""
        outdir = pathlib.Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        
        # 1. Handle conversions
        if self.convert_files:
            self._convert_tracks(outdir)

        # 2. Save sidecar config
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
            **self.custom_genome_config,
            **kwargs
        )
        
        return hub
