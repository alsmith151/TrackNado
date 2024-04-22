import os
import pathlib
import pickle
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict, namedtuple
from typing import Dict, List, Union
import hashlib
import json
from loguru import logger
import pandas as pd
import trackhub

def fix_duplicate_names(df: pd.DataFrame):
    duplicate_counts = defaultdict(int)

    for row in df.itertuples():
        duplicate_counts[row.basename] += 1
        if duplicate_counts[row.basename] > 1:
            name = f"{row.name}_{duplicate_counts[row.basename]}"
            basename = f"{row.basename}_{duplicate_counts[row.basename]}.{row.ext}"
            df.loc[row.Index, "name"] = name
            df.loc[row.Index, "basename"] = basename

def get_hash(obj: object) -> str:
    """Get hash of object"""
    return hashlib.md5(json.dumps(obj).encode("utf-8")).hexdigest()

def get_hash_for_df(df: pd.DataFrame, columns: Union[List[str], pd.Index] = None) -> List[str]:

    if columns is None:
        columns = df.columns
    
    hashes = []
    for row in df.itertuples():
        x = tuple([getattr(row, x) for x in columns])
        hash = get_hash(x)
        hashes.append(hash)
    
    return hashes

class TrackFiles:
    def __init__(
        self,
        files: Union[List[str], List[pathlib.Path], pd.DataFrame],
        infer_subgroups: bool = False,
        infer_attributes: bool = False,
        deduplicate: bool = False,
        convert_files: bool = False,
        chromosome_sizes: Union[pathlib.Path, str] = "",
        convert_extensions: bool = True,
        **kwargs,
    ) -> None:

        self.files = self.get_file_attributes(files)  # type: ignore

        if (self.files["ext"] == "bed").any() and not convert_files:
            raise ValueError(
                "BED files detected. Please set convert_files=True to convert to BigBed"
            )
        else:
            self.convert_tracks_to_ucsc_format(chrom_sizes=chromosome_sizes, outdir=".")

        if deduplicate:
            self.fix_duplicate_names()

        if infer_attributes:
            self.files = self.infer_attributes_from_file_names()

        self.subgroup_columns = (
            self.infer_subgroup_columns() if infer_subgroups else None
        )

    def get_file_attributes(
        self, files: Union[pd.DataFrame, List[Union[str, pathlib.Path]]]
    ) -> pd.DataFrame:

        if isinstance(files, pd.DataFrame):
            assert "fn" in files.columns, "DataFrame must have a column named 'fn'"
            df = files
        else:
            df = pd.Series(files).to_frame("fn")

        paths = [pathlib.Path(fn) for fn in df["fn"].values]

        if not "path" in df.columns:
            df["path"] = [str(p.absolute().resolve()) for p in paths]
        
        if not "basename" in df.columns:
            df["basename"] = [p.name for p in paths]
        
        if not "name" in df.columns:
            df["name"] = [p.stem for p in paths]
        
        if not "ext" in df.columns:
            df["ext"] = [p.suffix.strip(".") for p in paths]


        extension_mapping = {
            "bw": "bigWig",
            "bb": "bigBed",
            "bigbed": "bigBed",
            "bigwig": "bigWig",
        }

        df["ext"] = df["ext"].replace(extension_mapping)

        return df

    def infer_subgroup_columns(self) -> List[str]:
        return self.files.columns.difference(
            ["fn", "path", "basename", "name", "ext"]
        ).tolist()

    def fix_duplicate_names(self):
        duplicate_counts = defaultdict(int)

        for row in self.files.itertuples():
            duplicate_counts[row.basename] += 1
            if duplicate_counts[row.basename] > 1:
                name = f"{row.name}_{duplicate_counts[row.basename]}"
                basename = f"{row.basename}_{duplicate_counts[row.basename]}.{row.ext}"
                self.files.loc[row.Index, "name"] = name
                self.files.loc[row.Index, "basename"] = basename

    def convert_tracks_to_ucsc_format(
        self, chrom_sizes: Union[str, pathlib.Path], outdir: Union[str, pathlib.Path]
    ) -> None:
        """Convert tracks to UCSC format"""

        from tracknado.utils import has_valid_chromsizes, has_tracks_to_convert

        if has_tracks_to_convert(self.files):


            if not has_valid_chromsizes(chrom_sizes):
                raise ValueError(
                    f"Chromosome sizes file {chrom_sizes} does not exist")

            outdir = pathlib.Path(outdir)
            outdir.mkdir(exist_ok=True)

            # convert bed to bigBed
            bed_files = self.files[self.files["ext"] == "bed"]
            for bed_file in bed_files.itertuples():

                print(f"Converting {bed_file.name} to BigBed format")

                bed_file_path = pathlib.Path(bed_file.path).absolute()
                bed_file_basename = bed_file_path.name.removesuffix(".bed")


                cmd_sort = [
                    "sort",
                    "-k1,1",
                    "-k2,2n",
                    str(bed_file_path),
                    "-o",
                    bed_file_path.with_suffix(".sorted.bed"),
                ]

                cmd_convert = [
                    "bedToBigBed",
                    str(bed_file_path.with_suffix(".sorted.bed")),
                    str(chrom_sizes),
                    f"{outdir.joinpath(bed_file_basename)}.bigBed",
                ]

                subprocess.run(cmd_sort, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(cmd_convert, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Remove the sorted bed file
                bed_file_path.with_suffix(".sorted.bed").unlink()

                # Update the file name in the dataframe
                self.files.loc[bed_file.Index, "path"] = outdir.joinpath(bed_file_basename).with_suffix(".bigBed")
                self.files.loc[bed_file.Index, "ext"] =  "bigBed"
                self.files.loc[bed_file.Index, "fn"] = self.files.loc[bed_file.Index, "path"]        


    def infer_attributes_from_file_names(
        self,
        regex: str = r"(?P<sample_name>.*?)(?:_(?P<antibody>.*?))?(?:_(?P<replicate>[0-9]+))?$",
    ) -> pd.DataFrame:
        """Infer attributes from file names using a regex"""

        df = self.files.copy()
        df_attributes = df["name"].str.extract(regex)

        # Remove any columns that are all NaN
        df_attributes = df_attributes.loc[:, df_attributes.notnull().any()]

        return df.join(df_attributes)
    
    def __add__(self, other):
        """Combine two TrackFiles objects"""
            
        assert isinstance(other, TrackFiles), "Can only combine TrackFiles objects"

        files = pd.concat([self.files, other.files], ignore_index=True)
        files = files.drop_duplicates(subset=["path"])
        files = files.reset_index(drop=True)

        return TrackFiles(files)

class TrackDesign:
    def __init__(
        self,
        details: pd.DataFrame,
        color_by: List[str] = None,
        subgroup_by: List[str] = None,
        overlay_by: List[str] = None,
        supergroup_by: List[str] = None,
        **kwargs,
    ):

        self.details = details
        self._supertrack_columns = list(supergroup_by) if supergroup_by else list()
        self._overlay_columns = list(overlay_by) if overlay_by else list()
        self._subgroup_columns = list(subgroup_by) if subgroup_by else list()
        self.subgroup_definitions = list() if subgroup_by else None
        self._color_columns = list(color_by) if color_by else list()

        self._add_subgroupings(supergroup_by=self._supertrack_columns, subgroup_by=self._subgroup_columns)

        self.super_tracks = self._get_super_tracks()
        self._add_supertrack_indicators()

        self.composite_tracks = self._get_composite_tracks()
        self._add_composite_track_indicators()

        self.overlay_tracks = self._get_overlay_tracks()
        self._add_overlay_track_indicators()

        self._add_track_colors(color_by=color_by)

    @classmethod
    def from_files(cls, files: List[pathlib.Path], **kwargs) -> "TrackDesign":
        hub_files = TrackFiles(files, **kwargs)

        extra_kwargs = dict()
        if hub_files.subgroup_columns:
            extra_kwargs["subgroup_by"] = hub_files.subgroup_columns


        return cls(hub_files.files, **kwargs, **extra_kwargs)

    @classmethod
    def from_design(cls, design: pd.DataFrame, **kwargs) -> "TrackDesign":
        design = design.copy()
        design = TrackFiles(design, **kwargs).files
        return cls(design, **kwargs)
    
    @classmethod
    def from_pickle(cls, pickle_file: pathlib.Path) -> "TrackDesign":
        with open(pickle_file, "rb") as f:
            return pickle.load(f)

    def _add_track_colors(
        self,
        color_by: Union[str, List[str]] = None,
        pallet: str = "tab20",
        color_column: str = None,
    ) -> None:

        """Add a column to the details dataframe with a color for each track"""

        from PIL import ImageColor

        if color_by:
            if isinstance(color_by, str):
                color_by = [color_by]

            assert all([c in self.details.columns for c in color_by]), f"Color-By columns {color_by} missing"  # type: ignore

            try:
                # Get a pallette with enough colors for the unique groups in the details
                import seaborn as sns
                n_colors = len(self.details[color_by].drop_duplicates())
                colors = sns.color_palette(pallet, n_colors=n_colors).as_hex()  # type: ignore

                # Assign a color to each group
                color_dict = {}
                for i, group in enumerate(
                    self.details[color_by].drop_duplicates().itertuples()
                ):
                    color_dict[tuple([getattr(group, c) for c in color_by])] = colors[i]  # type: ignore

                # Add a column to the details dataframe with the color for each track
                self.details["color"] = self.details[color_by].apply(
                    lambda row: ImageColor.getrgb(color_dict[tuple([c for c in row])]),
                    axis=1,
                )

            except NameError:
                raise NameError(
                    "Pallette not found. Try one of the following: 'tab20', 'tab20b', 'tab20c'"
                )

        elif color_column:

            assert (
                color_column in self.details.columns
            ), f"Color column {color_column} missing"

            colors = []
            for i, color in enumerate(self.details[color_column]):
                if isinstance(color, tuple):
                    c = color
                elif isinstance(color, str):
                    if color.startswith("#"):
                        c = ImageColor.getrgb(color)
                    else:
                        c = color.split(",")
                        c = tuple([int(x) for x in c])
                else:
                    raise ValueError(
                        f"Color column {color_column} must be a tuple or string"
                    )

                colors.append(c)

            self.details["color"] = colors

    def _add_subgroup_definitions_to_df(
        self, df: pd.DataFrame, subgroup_by: List[str] = None
    ) -> pd.DataFrame:
        """Add a column to the details dataframe with a `trackhub.SubGroupDefinition` for each track"""

        assert all(
            [c in df.columns for c in subgroup_by]
        ), f"Subgroup-By columns {subgroup_by} missing"
        df = df.copy()

        # Loop through all columns provided and generate a subgroup definition for each
        subgroup_definitions = []
        for column in subgroup_by:
            # Get a list of unique values in the column
            unique_values = df[column].unique()
            subgroup_definition = trackhub.SubGroupDefinition(
                name=column,
                label=column,
                mapping={value: value for value in unique_values},
            )
            subgroup_definitions.append(subgroup_definition)

        # Add a column to the details dataframe with the subgroup definition for each track
        df["subgroup_names"] = [
            tuple([col for col in subgroup_by]) for i in range(df.shape[0])
        ]
        df["subgroup_definition"] = [subgroup_definitions for i in range(df.shape[0])]

        self.subgroup_definitions.extend(subgroup_definitions)

        return df

    def _add_subgroupings(
        self, supergroup_by: List[str] = None, subgroup_by: List[str] = None
    ) -> None:
        """Add a column to the details dataframe with a `trackhub.SubGroupDefinition` for each track.

        If `supergroup_by` is provided, the subgroup definitions will be added to the dataframe
        grouped by the supergroup columns.

        If `supergroup_by` is not provided, the subgroup definitions will be added to the dataframe
        as a single group.
        """

        if subgroup_by:

            assert all(
                [c in self.details.columns for c in subgroup_by]
            ), f"Subgroup-By columns {subgroup_by} missing"

            if supergroup_by:
                assert not any(
                    subgroup in supergroup_by for subgroup in subgroup_by
                ), f"SubGroup columns {subgroup_by} cannot be in SuperGroup columns {supergroup_by}"
          
                self.details = self.details.groupby(supergroup_by).apply(
                    self._add_subgroup_definitions_to_df, subgroup_by=subgroup_by
                )
            else:
                self.details = self._add_subgroup_definitions_to_df(
                    self.details, subgroup_by=subgroup_by
                )

    def _get_super_tracks(self) -> Dict[str, trackhub.SuperTrack]:
        """Generate a dictionary of SuperTracks from the details dataframe"""

        if self._supertrack_columns:
            assert all(
                [c in self.details.columns for c in self._supertrack_columns]
            ), f"SuperTrack columns {self._supertrack_columns} missing"

            supertracks = dict()
            for grouping, df in self.details.reset_index(drop=True).groupby(self._supertrack_columns, as_index=False):
                

                if isinstance(grouping, str):
                    track_id = (grouping,)
                elif len(grouping) == 1:
                    track_id = grouping
                else:
                    track_id = tuple(grouping)
                
                if len(track_id) == 1:
                    track_name = track_id[0]
                else:
                    track_name = "_".join(track_id)


                supertracks[get_hash(track_id)] = trackhub.SuperTrack(
                    name=track_name,
                )

        else:
            supertracks = dict()

        return supertracks

    def _add_supertrack_indicators(self):
        """Add a column to the details dataframe with a SuperTrack indicator for each track"""

        if self._supertrack_columns:
            assert all(
                [c in self.details.columns for c in self._supertrack_columns]
            ), f"SuperTrack columns {self._supertrack_columns} missing"

            self.details["supertrack"] = get_hash_for_df(self.details, self._supertrack_columns)
    
    def _get_composite_tracks(self) -> Dict[str, trackhub.CompositeTrack]:
        """Generate a dictionary of CompositeTracks from the details dataframe"""

        composite_tracks = dict()
        dimensions = dict(
                    zip(
                        [f"dim{d}" for d in ["X", "Y", "A", "B", "C", "D"]],
                        self._subgroup_columns,
                    )
                )
        
        if "supertrack" in self.details.columns:
            for (supertrack, ext) , df in self.details.groupby(["supertrack", "ext"]):
                

                supertrack_name = self.super_tracks[supertrack].name
                composite_name = "_".join([supertrack_name, ext])


                composite = trackhub.CompositeTrack(
                    name=composite_name,
                    tracktype=ext,
                    dimensions=" ".join([f"{k}={v}" for k, v in dimensions.items()])
                    if dimensions
                    else None,
                    sortOrder=" ".join([f"{k}=+" for k in self._subgroup_columns]),
                    visibility="hide",
                    dragAndDrop="subTracks",
                )

                composite.add_subgroups(self.subgroup_definitions)

                self.super_tracks[supertrack].add_tracks(composite)
                composite_tracks[get_hash((supertrack, ext))] = composite

        elif self._subgroup_columns:
            for ext, df in self.details.groupby("ext"):
                composite = trackhub.CompositeTrack(
                    name=ext,
                    tracktype=ext,
                    visibility="hide",
                    dragAndDrop="subTracks",
                    dimensions=" ".join([f"{k}={v}" for k, v in dimensions.items()])
                    if dimensions
                    else None,
                    sortOrder=" ".join([f"{k}=+" for k in self._subgroup_columns]),
                )

                composite.add_subgroups(self.subgroup_definitions)
                composite_tracks[get_hash((ext,))] = composite
        
        else:
            composite_tracks = dict()

        return composite_tracks

    def _add_composite_track_indicators(self):
        """Add a column to the details dataframe with a CompositeTrack indicator for each track"""

        if self.composite_tracks:
            composite_columns = ["supertrack"] if self._supertrack_columns else []
            composite_columns.append("ext")

            self.details["composite"] = get_hash_for_df(self.details, composite_columns)

            assert self.details["composite"].isin(self.composite_tracks.keys()).all(), (
                "Composite tracks not found in details dataframe"
            )

    def _get_overlay_tracks(self):
        """Generate a dictionary of OverlayTracks from the details dataframe"""

        if self._overlay_columns:
            assert all(
                [c in self.details.columns for c in self._overlay_columns]
            ), f"Overlay columns {self._overlay_columns} missing"

            overlay_tracks = dict()
            overlay_columns = list(self._overlay_columns) if not isinstance(self._overlay_columns, str) else [self._overlay_columns,]

            if "supertrack" in self.details.columns:

                for (supertrack, overlay) , df in self.details.groupby(
                    ["supertrack", *self._overlay_columns]
                ):
                    
                    supertrack_name = self.super_tracks[supertrack].name

                    if isinstance(overlay, str):
                        overlay_name = "_".join([supertrack_name, overlay]) + "_overlay"
                    else:
                        overlay_name = "_".join([supertrack_name, *overlay]) + "_overlay"

                    overlay_track = trackhub.AggregateTrack(
                        aggregate="transparentOverlay",
                        name=overlay_name,
                        tracktype="bigWig",
                    )

                    self.super_tracks[supertrack].add_tracks(overlay_track)
                    overlay_tracks[get_hash(tuple([supertrack, overlay]))] = overlay_track

            else:
                for overlay, df in self.details.groupby(self._overlay_columns):

                    overlay_name = "_".join(overlay) if isinstance(overlay, tuple) else overlay
                    overlay_id = tuple(overlay) if isinstance(overlay, tuple) else (overlay,)

                    overlay_track = trackhub.AggregateTrack(
                        aggregate="transparentOverlay",
                        name=overlay_name,
                        tracktype="bigWig",
                    )
                    overlay_tracks[get_hash(overlay_id)] = overlay_track

        else:
            overlay_tracks = dict()

        return overlay_tracks

    def _add_overlay_track_indicators(self):
        """Add a column to the details dataframe with an OverlayTrack indicator for each track"""

        if self._overlay_columns:

            overlay_columns = (
                ["supertrack"] if self._supertrack_columns else []
            )
            overlay_columns.extend(self._overlay_columns)

            self.details["overlay"] = get_hash_for_df(self.details, overlay_columns)

            assert self.details["overlay"].isin(self.overlay_tracks.keys()).all(), (
                "Overlay tracks not found in details dataframe"
            )


    def __add__(self, other):
        """Combine two HubDesign objects"""
            
        assert isinstance(other, TrackDesign), "Can only combine HubDesign objects"

        self.details = pd.concat([self.details, other.details], ignore_index=True)
        fix_duplicate_names(self.details)

        if any([self._supertrack_columns, other._supertrack_columns]):
            self._supertrack_columns = sorted(
                list(set(self._supertrack_columns + other._supertrack_columns))
            )
            self._add_supertrack_indicators()


        if any([self._subgroup_columns, other._subgroup_columns]):
            self._subgroup_columns = sorted(
                list(set(self._subgroup_columns + other._subgroup_columns))
            )
            self._add_composite_track_indicators()

        
        if any([self._overlay_columns, other._overlay_columns]):
            self._overlay_columns = sorted(
                list(set(self._overlay_columns + other._overlay_columns))
            )
            self._add_overlay_track_indicators()

        return self

    def to_pickle(self, path: str) -> None:
        """Save the design to a pickle file"""
        with open(path, "wb") as f:
            pickle.dump(self, f)


class HubGenerator:
    def __init__(
        self,
        hub_name: str,
        genome: str,
        track_design: TrackDesign,
        outdir: pathlib.Path,
        description_html: pathlib.Path = None,
        hub_email: str = "",
        custom_genome: bool = False,
        genome_twobit: pathlib.Path = None,
        genome_organism: str = None,
        genome_default_position: str = "chr1:10000-20000",
    ):

        # Basic parameters for hub creation
        self.hub_name = hub_name
        self.genome_name = genome
        self.track_design = track_design
        self.outdir = outdir
        self.custom_genome = custom_genome
        self.description_url_path = description_html

        # Parameters for custom genomes
        self._genome_twobit = genome_twobit
        self._genome_organism = genome_organism
        self._genome_default_position = genome_default_position

        # Create the basic hub
        self._hub = trackhub.Hub(
            hub_name, short_label=hub_name, long_label=hub_name, email=hub_email
        )
        
        self.trackdb = trackhub.TrackDb()
        _genome = self._get_genome_file()  # type: ignore
        _genomes_file = trackhub.GenomesFile()

        # Add these to the hub
        _genome.add_trackdb(self.trackdb)
        self._hub.add_genomes_file(_genomes_file)
        _genomes_file.add_genome(_genome)

        self._add_tracks_to_hub()

    def _add_tracks_to_hub(self) -> None:
        # Loop through each entry in the details dataframe
        
        for row in self.track_design.details.itertuples():

            has_composite = False
            has_overlay = False

            # If the row has a "composite" attribute
            if hasattr(row, "composite"):
                has_composite = True
                composite_track = self.track_design.composite_tracks[row.composite]
                # Create a new track and add it as a subtrack to the composite track
                track = self._get_track(row, suffix=f"_{composite_track.name}")
                composite_track.add_subtrack(track)

            # If the row has an "overlay" attribute
            if hasattr(row, "overlay"):
                has_overlay = True
                overlay_track = self.track_design.overlay_tracks[row.overlay]
                # Create a new track and add it to the overlay track
                track = self._get_track(row, suffix=f"_{overlay_track.name}")

                # Ignore the track if it is not a signal track e.g. bigWig
                if track.tracktype not in ["bigWig", ]:
                    logger.warning(f"Track {track.name} is not a signal track and will be ignored for the overlay track {overlay_track.name}")
                else:
                    overlay_track.add_subtrack(track)

            # If the row doesn't have a "supertrack" attribute
            if not hasattr(row, "supertrack") and not has_composite and not has_overlay:
                # Create a new track and add it to the trackdb
                track = self._get_track(row)
                self.trackdb.add_tracks(track)

        # Add the supertracks or composite/overlay tracks to the trackdb
        if self.track_design.super_tracks:
            tracks = self.track_design.super_tracks.values()
            
            # Ensure the composite and/or overlay tracks have the group attribute set
            if self.custom_genome:
                for t in [*self.track_design.composite_tracks.values(), *self.track_design.overlay_tracks.values()]:
                    t.add_params(group=self._hub.hub)

        else:
            tracks = [*self.track_design.composite_tracks.values(), *self.track_design.overlay_tracks.values()]

        # Add the composite/overlay and supertracks to the trackdb
        for ii, track in enumerate(tracks):
            # Add group if custom genome
            if self.custom_genome:
                track.add_params(group=self._hub.hub)
            self.trackdb.add_tracks(track)

    

    def _get_track(self, track: namedtuple, suffix: str = "") -> trackhub.Track:
        """Generate a trackhub.Track object from a row in the details dataframe"""


        extra_kwargs = dict()
        if hasattr(track, "color"):
            extra_kwargs["color"] = ",".join([str(x) for x in track.color])
        
        if hasattr(track, "subgroup_names"):
            extra_kwargs["subgroups"] = {subgroup_name: getattr(track, subgroup_name) 
                                         for subgroup_name in track.subgroup_names}

        if self.custom_genome:
            extra_kwargs["group"] = self._hub.hub

        if track.ext == "bigWig":
            extra_kwargs.update(
                {
                    "maxHeightPixels": "100:50:11",
                    "visibility": "full",
                    "viewLimits": "0:100",
                    "autoScale": "on",
                    "windowingFunction": "mean",
                }
            )
        
        elif track.ext == "bigBed":
            extra_kwargs.update(
                {
                    "visibility": "pack",
                }
            )
        
        return  trackhub.Track(
                name="".join([trackhub.helpers.sanitize(track.name), suffix]),
                shortLabel=" ".join(re.split(r"[.|_|\s+|-]", track.name)),
                longLabel=" ".join(re.split(r"[.|_|\s+|-]", track.name)),
                source=str(track.path),
                tracktype=track.ext,
                **extra_kwargs,
               
            )
      
    def _get_genome_file(self) -> trackhub.Genome:

        if not self.custom_genome:
            genome = trackhub.Genome(self.genome_name)
            groups_file = None
        else:
            genome = trackhub.Assembly(
                genome=self.genome_name,
                twobit_file=self._genome_twobit,
                organism=self._genome_organism,
                defaultPos=self._genome_default_position,
            )

            groups_file = trackhub.GroupsFile(
                [
                    trackhub.GroupDefinition(
                        name=self.hub_name, priority=1, default_is_closed=False
                    ),
                ]
            )

            genome.add_groups(groups_file)

        return genome


    def stage_hub(
        self,
    ):

        with tempfile.TemporaryDirectory() as tmpdir:
            trackhub.upload.stage_hub(self._hub, staging=tmpdir)

            if self.description_url_path:
                description_basename = os.path.basename(self.description_url_path)
                with open(os.path.join(tmpdir, f"{self._hub.hub}.hub.txt"), "a") as hubtxt:
                    hubtxt.write("\n")
                    hubtxt.write(f"descriptionUrl {self.genome_name}/{description_basename}\n")

                shutil.copy(
                    self.description_url_path,
                    os.path.join(tmpdir, self.genome_name),
                )

            # Copy to the new location
            shutil.copytree(
                tmpdir,
                self.outdir,
                dirs_exist_ok=True,
                symlinks=False,
            )

            subprocess.run(["chmod", "-R", "2755", self.outdir])
        
    
    def to_pickle(self, path: str) -> None:
        """Save the hub to a pickle file"""
        with open(path, "wb") as f:
            pickle.dump(self, f)
            
            
    
   

        
    
    