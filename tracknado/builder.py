from __future__ import annotations
import pathlib
from typing import Callable, Any, Optional, Union
import pandas as pd
from .models import Track
from .schemas import TrackDataFrameSchema
from .api import TrackDesign, HubGenerator
from loguru import logger

from pydantic import BaseModel, Field, ConfigDict


class HubBuilder(BaseModel):
    """Fluent API for building UCSC track hubs.

    Now a Pydantic model for EASY serialization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

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
    sort_metadata: bool = Field(False)
    missing_group_label: str | None = Field(None)
    missing_group_columns: list[str] = Field(default_factory=list)

    # Non-serialized field for extractors (functions can't be JSON serialized easily)
    metadata_extractors: list[Callable[[pathlib.Path], dict[str, str]]] = Field(
        default_factory=list, exclude=True
    )

    def __init__(self, **data):
        super().__init__(**data)

    def add_tracks(
        self, paths: list[str] | list[pathlib.Path], **common_metadata: str
    ) -> HubBuilder:
        """Add multiple tracks from paths."""
        for p in paths:
            path = pathlib.Path(p)
            self.tracks.append(Track(path=path, metadata=common_metadata.copy()))
        return self

    def add_tracks_from_df(
        self, df: pd.DataFrame, file_path_col: str = "file_path"
    ) -> HubBuilder:
        """Add tracks from a pandas DataFrame."""
        df = df.copy()
        if file_path_col not in df.columns:
            raise ValueError(
                f"Track metadata must include a '{file_path_col}' column."
            )
        if file_path_col in df.columns and "ext" not in df.columns:
            df["ext"] = df[file_path_col].apply(
                lambda x: pathlib.Path(x).suffix.strip(".")
            )

        try:
            df = TrackDataFrameSchema.validate(df)
        except Exception as e:
            logger.warning(f"DataFrame validation failed: {e}")

        for _, row in df.iterrows():
            path = pathlib.Path(row[file_path_col])
            metadata = {
                k: str(v)
                for k, v in row.items()
                if k not in [file_path_col, "ext", "path", "name"] and pd.notna(v)
            }
            track = Track(path=path, metadata=metadata)
            if "name" in row and pd.notna(row["name"]):
                track.name = row["name"]
            if "ext" in row and pd.notna(row["ext"]):
                track.track_type = row["ext"]
            self.tracks.append(track)
        return self

    def with_metadata_extractor(
        self, fn: Callable[[pathlib.Path], dict[str, str]]
    ) -> HubBuilder:
        """Add a metadata extractor function."""
        self.metadata_extractors.append(fn)
        return self

    def with_grouping_regex(self, pattern: str) -> HubBuilder:
        """Extract grouping fields from file names using a regex pattern."""
        from .extractors import from_filename_pattern

        self.metadata_extractors.append(from_filename_pattern(pattern))
        return self

    def group_by(self, *columns: str, as_supertrack: bool = False) -> "HubBuilder":
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
        default_position: str = "chr1:10000-20000",
    ) -> "HubBuilder":
        """Configure a custom genome (Assembly Hub) for this hub."""
        self.custom_genome_config = {
            "custom_genome": True,
            "genome_twobit": str(twobit_file),
            "genome_organism": organism,
            "genome_default_position": default_position,
        }
        return self

    def color_by(self, column: str, palette: str = "tab20") -> HubBuilder:
        """Specify column for track coloring."""
        self.color_by_col = column
        self.color_palette = palette
        return self

    def overlay_by(self, *columns: str) -> HubBuilder:
        """Specify columns for overlay tracks."""
        self.overlay_by_cols.extend(columns)
        return self

    def with_sort_metadata(self, enabled: bool = True) -> HubBuilder:
        """Enable or disable sorting of metadata columns in output."""
        self.sort_metadata = enabled
        return self

    def with_convert_files(self, enabled: bool = True) -> HubBuilder:
        """Enable or disable implicit track conversion."""
        self.convert_files = enabled
        return self

    def with_missing_groups(
        self, label: str = "NA", *columns: str
    ) -> HubBuilder:
        """Replace missing grouping values with a label before hub generation.

        If `columns` are not provided, applies to all active grouping columns.
        """
        self.missing_group_label = label
        self.missing_group_columns = list(columns)
        return self

    def with_chrom_sizes(self, path: Union[str, pathlib.Path]) -> HubBuilder:
        """Set the chrom.sizes file for track conversion."""
        self.chrom_sizes = pathlib.Path(path)
        return self

    def merge(self, *others: "HubBuilder") -> HubBuilder:
        """Merge other HubBuilders into this one, reconciling settings."""
        for other in others:
            self.tracks.extend(other.tracks)
            # Union of grouping columns
            self.group_by_cols = sorted(
                list(set(self.group_by_cols + other.group_by_cols))
            )
            self.supergroup_by_cols = sorted(
                list(set(self.supergroup_by_cols + other.supergroup_by_cols))
            )
            self.overlay_by_cols = sorted(
                list(set(self.overlay_by_cols + other.overlay_by_cols))
            )
            if not self.convert_files:
                self.convert_files = other.convert_files
            if not self.chrom_sizes:
                self.chrom_sizes = other.chrom_sizes
            if not self.custom_genome_config:
                self.custom_genome_config = other.custom_genome_config.copy()
            if not self.missing_group_label:
                self.missing_group_label = other.missing_group_label
            if not self.missing_group_columns:
                self.missing_group_columns = list(other.missing_group_columns)
            # Merge extractors
            for ex in other.metadata_extractors:
                if ex not in self.metadata_extractors:
                    self.metadata_extractors.append(ex)
            # Colors: use other's if not set here
            if not self.color_by_col:
                self.color_by_col = other.color_by_col
                self.color_palette = other.color_palette
            # Merge sort_metadata: True if either is True
            self.sort_metadata = self.sort_metadata or other.sort_metadata
        return self

    def to_json(self, path: str | pathlib.Path | None = None) -> str:
        """Serialize state to JSON string or file."""
        data = self.model_dump_json(indent=2, by_alias=True)
        if path:
            with open(path, "w") as f:
                f.write(data)
        return data

    @classmethod
    def from_json(cls, path_or_data: str | pathlib.Path) -> HubBuilder:
        """Reconstruct builder from JSON string or file path."""
        p = pathlib.Path(path_or_data)
        if p.exists() and p.is_file():
            with open(p, "r") as f:
                data = f.read()
        else:
            data = path_or_data
        return cls.model_validate_json(data)

    def _extract_metadata(self):
        """Extract metadata for all tracks using registered extractors."""
        if not self.metadata_extractors:
            return

        for track in self.tracks:
            # Skip if metadata has already been extracted (marked with _metadata_extracted flag)
            if getattr(track, "_metadata_extracted", False):
                continue
            
            # Use original path if it exists for extraction, as it might have more metadata in its name/path
            # than a temporary converted path.
            path_to_extract = getattr(track, "_original_path", track.path)
            for extractor in self.metadata_extractors:
                extracted = extractor(path_to_extract)
                track.metadata.update(extracted)
            
            # Mark this track as having metadata extracted
            track._metadata_extracted = True

    def _convert_tracks(self, outdir: pathlib.Path):
        """Convert tracks to UCSC formats (e.g. BED -> BigBed)."""
        from .converters import convert_bed_to_bigbed, convert_gtf_to_biggenepred

        if not self.chrom_sizes or not self.chrom_sizes.exists():
            raise ValueError(
                "chrom_sizes must be provided and exist for track conversion"
            )

        conv_dir = outdir / "converted"
        conv_dir.mkdir(parents=True, exist_ok=True)

        for track in self.tracks:
            if track.path.suffix.lower() == ".bed":
                logger.info(f"Converting {track.path.name} to BigBed")
                dest = conv_dir / track.path.with_suffix(".bb").name
                # Save original path for metadata extraction if needed later
                track._original_path = track.path
                new_path = convert_bed_to_bigbed(track.path, self.chrom_sizes, dest)
                track.path = new_path
                track.track_type = "bigBed"
            elif track.path.suffix.lower() in [".gtf", ".gff"]:
                logger.info(f"Converting {track.path.name} to BigGenePred")
                dest = conv_dir / track.path.with_suffix(".bb").name
                track._original_path = track.path
                new_path = convert_gtf_to_biggenepred(
                    track.path, self.chrom_sizes, dest
                )
                track.path = new_path
                track.track_type = "bigGenePred"

    def to_dataframe(self) -> pd.DataFrame:
        """Return the current tracks (with any extracted metadata) as an editable DataFrame."""
        return self._prepare_design_df()

    def _prepare_design_df(self) -> pd.DataFrame:
        """Convert tracks to the DataFrame format used by TrackDesign."""
        # Metadata extraction is idempotent and safe to call multiple times
        # It will be a no-op if already extracted
        self._extract_metadata()

        extension_mapping = {
            "bw": "bigWig",
            "bb": "bigBed",
            "bigbed": "bigBed",
            "bigwig": "bigWig",
            "bed": "bigBed",  # Default for .bed is bigBed (assuming conversion)
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
                "file_path": str(track.path),
                "path": str(track.path.absolute().resolve()),
                "name": track.name or track.path.stem,
                "ext": ext,
            }
            row.update(track.metadata)
            data.append(row)

        df = pd.DataFrame(data)
        self._ensure_unique_track_names(df)
        self._fill_missing_group_values(df)
        
        # Sort columns alphabetically if requested (keeping standard columns first)
        if self.sort_metadata:
            standard_cols = ["file_path", "path", "name", "ext"]
            existing_standard = [c for c in standard_cols if c in df.columns]
            other_cols = sorted([c for c in df.columns if c not in existing_standard])
            df = df[existing_standard + other_cols]
        
        return df

    @staticmethod
    def _validate_index_files(df: pd.DataFrame) -> None:
        """Ensure companion index files exist for track types that need them.

        UCSC hubs stage BAM tracks alongside a same-named '.bai' index
        (e.g. 'sample.bam' -> 'sample.bam.bai'); without it, staging fails
        deep inside the trackhub library with an opaque error. Fail fast here
        with an actionable message instead.
        """
        if "ext" not in df.columns:
            return

        missing = []
        for file_path in df.loc[df["ext"] == "bam", "file_path"]:
            bam_path = pathlib.Path(file_path)
            bai_path = bam_path.with_name(bam_path.name + ".bai")
            if not bai_path.exists():
                missing.append(str(bai_path))

        if missing:
            raise ValueError(
                "Missing BAM index file(s). Each '.bam' track needs a same-named "
                "'.bai' index next to it (e.g. 'sample.bam' -> 'sample.bam.bai'). "
                f"Run 'samtools index <file.bam>' to generate it. Missing: {', '.join(missing)}"
            )

    @staticmethod
    def _normalize_name(value: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")

    @classmethod
    def _append_path_suffix(cls, base: str, path: pathlib.Path, depth: int) -> str:
        parents = list(path.parents)
        # parents[0] is the immediate parent directory
        parts = [p.name for p in parents[:depth] if p.name]
        if not parts:
            parts = [path.name]
        suffix = "__".join(reversed(parts))
        suffix = cls._normalize_name(suffix)
        return f"{base}__{suffix}" if suffix else base

    @classmethod
    def _ensure_unique_track_names(cls, df: pd.DataFrame) -> None:
        """Ensure `name` is unique while keeping names readable."""
        if df.empty or "name" not in df.columns:
            return

        names = df["name"].astype(str).tolist()
        paths = [pathlib.Path(p) for p in df["file_path"].tolist()]
        counts = pd.Series(names).value_counts()
        used: set[str] = set()

        for i, name in enumerate(names):
            candidate = name
            if counts[name] > 1 or candidate in used:
                path = paths[i]
                depth = 1
                while candidate in used:
                    candidate = cls._append_path_suffix(name, path, depth)
                    depth += 1
                    if depth > len(path.parents) + 1:
                        candidate = f"{name}__{i + 1}"
                        break
            used.add(candidate)
            names[i] = candidate

        df["name"] = names

    def _fill_missing_group_values(self, df: pd.DataFrame) -> None:
        """Fill NA/empty values in grouping columns with a configured label."""
        if not self.missing_group_label:
            return

        if self.missing_group_columns:
            target_columns = list(dict.fromkeys(self.missing_group_columns))
        else:
            target_columns = list(
                dict.fromkeys(
                    [
                        *self.group_by_cols,
                        *self.supergroup_by_cols,
                        *self.overlay_by_cols,
                    ]
                )
            )

        for col in target_columns:
            if col not in df.columns:
                continue
            df[col] = df[col].replace("", pd.NA).fillna(self.missing_group_label)

    def build(
        self,
        name: str,
        genome: str,
        outdir: str | pathlib.Path,
        hub_email: str = "",
        **kwargs,
    ) -> Any:
        """Build the hub and export sidecar config."""
        outdir = pathlib.Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        # 1. Handle conversions
        if self.convert_files:
            self._convert_tracks(outdir)

        # 2. Extract metadata BEFORE saving config so extracted data is included
        self._extract_metadata()

        # 3. Save sidecar config (now with extracted metadata)
        self.to_json(outdir / "tracknado_config.json")

        df = self._prepare_design_df()
        self._validate_index_files(df)

        design = TrackDesign.from_design(
            df,
            color_by=self.color_by_col,
            subgroup_by=self.group_by_cols if self.group_by_cols else None,
            supergroup_by=self.supergroup_by_cols if self.supergroup_by_cols else None,
            overlay_by=self.overlay_by_cols if self.overlay_by_cols else None,
            **kwargs,
        )

        hub = HubGenerator(
            hub_name=name,
            genome=genome,
            track_design=design,
            outdir=outdir,
            hub_email=hub_email,
            **self.custom_genome_config,
            **kwargs,
        )

        return hub


def configure_builder_from_inputs(
    input_files: list[str] | list[pathlib.Path] | None = None,
    metadata: str | pathlib.Path | None = None,
    seqnado: bool = False,
    grouping_regex: str | None = None,
    convert: bool = False,
    chrom_sizes: str | pathlib.Path | None = None,
    supergroup_by: list[str] | None = None,
    subgroup_by: list[str] | None = None,
    overlay_by: list[str] | None = None,
    color_by: str | None = None,
    sort_metadata: bool = False,
    custom_genome: bool = False,
    twobit: str | pathlib.Path | None = None,
    organism: str | None = None,
    default_pos: str = "chr1:10000-20000",
) -> HubBuilder:
    """Build a HubBuilder from the same inputs accepted by the CLI."""
    builder = HubBuilder().with_convert_files(convert)

    if not metadata and not seqnado and not grouping_regex:
        logger.warning(
            "No metadata source was provided, so no grouping can be performed."
        )

    if chrom_sizes:
        builder.with_chrom_sizes(chrom_sizes)

    if metadata:
        df = pd.read_csv(metadata, sep=None, engine="python")
        builder.add_tracks_from_df(df)
    elif input_files:
        builder.add_tracks(input_files)
    else:
        raise ValueError("Must provide input_files or metadata")

    if seqnado:
        from .extractors import from_seqnado_path

        builder.with_metadata_extractor(from_seqnado_path)

    if grouping_regex:
        builder.with_grouping_regex(grouping_regex)

    if supergroup_by:
        builder.group_by(*supergroup_by, as_supertrack=True)
    if subgroup_by:
        builder.group_by(*subgroup_by)
    if overlay_by:
        builder.overlay_by(*overlay_by)
    if color_by:
        builder.color_by(color_by)
    if sort_metadata:
        builder.with_sort_metadata()

    if custom_genome or twobit:
        if not twobit or not organism:
            raise ValueError("twobit and organism are required for custom genomes")
        builder.with_custom_genome(
            name="HUB",
            twobit_file=twobit,
            organism=organism,
            default_position=default_pos,
        )

    return builder
