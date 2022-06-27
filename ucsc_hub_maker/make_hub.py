import os
import pathlib
import shutil
import re
from typing import Dict, Tuple, Union

import numpy as np
import pandas as pd
import seaborn as sns
import trackhub


def get_file_attributes(files: Tuple):
    df = pd.Series(files).to_frame("fn")
    paths = [pathlib.Path(fn) for fn in df["fn"].values]
    df["path"] = [str(p.absolute().resolve()) for p in paths]
    df["basename"] = [p.name for p in paths]
    df["name"] = [p.stem for p in paths]
    df["ext"] = [p.suffix.strip(".") for p in paths]
    return df


def get_groups_from_regex(df_file_attributes: pd.DataFrame, pattern: str):

    groups = df_file_attributes["basename"].str.extract(pattern).reset_index()
    return pd.concat([df_file_attributes, groups], axis=1)


def get_groups_from_design_matrix(
    df_file_attributes: pd.DataFrame, df_design: pd.DataFrame
):
    return (
        df_file_attributes
        .set_index("fn")
        .join(df_design)
        .reset_index()
        .rename(columns={"index": "fn"})
    )


def get_genome_file(genome_name: str, custom_genome: bool = False, **kwargs):

    if not custom_genome:
        genome = trackhub.Genome(genome_name)
        groups_file = None
    else:
        genome = trackhub.Assembly(
            genome=genome_name,
            twobit_file=kwargs["genome_twobit"],
            organism=kwargs["genome_organism"],
            defaultPos=kwargs.get("hub_default_position", "chr1:1000-2000"),
        )

        groups_file = trackhub.GroupsFile(
            [
                trackhub.GroupDefinition(
                    name=kwargs["hub_name"], priority=1, default_is_closed=False
                ),
            ]
        )

        genome.add_groups(groups_file)

    return genome


def get_subgroup_definitions(
    df_file_attributes: pd.DataFrame, grouping_column: str = None
):

    columns_to_drop = ["fn", "path", "basename", "ext", "name"]

    if grouping_column:
        columns_to_drop.append(grouping_column)

    group_members = (
        df_file_attributes
        .drop(columns=columns_to_drop, errors="ignore")
        .apply(lambda ser: ser.unique())
        .to_dict()
    )

    subgroups = {
        grouping: trackhub.SubGroupDefinition(
            name=grouping,
            label=grouping.capitalize(),
            mapping={g.lower(): g for g in group},
        )
        for grouping, group in group_members.items()
    }

    return subgroups


def get_colors(df_file_attributes: pd.DataFrame, palette: str):
    unique_samples = df_file_attributes["samplename"].unique()
    colors = sns.color_palette(palette=palette, n_colors=len(unique_samples))
    color_mapping = dict(zip(unique_samples, colors))
    return color_mapping


def get_track_subgroups(
    track_details: tuple,
    subgroup_definitions: Dict[str, trackhub.SubGroupDefinition],
):
    return "_".join([getattr(track_details, subgroup).lower()
                     for subgroup in subgroup_definitions])


def add_composite_tracks_for_group(
    group_name: str,
    hub: trackhub.Hub,
    container: trackhub.TrackDb,
    track_details: pd.DataFrame,
    subgroup_definitions: Dict[str, trackhub.SubGroupDefinition],
    color_mapping: Dict[str, Tuple[float, float, float]],
    custom_genome: bool = False,
):

    dimensions = dict(
        zip([f"dim{d}" for d in ["X", "Y", "A", "B", "C", "D"]],
            subgroup_definitions)
    )

    for track_type, df in track_details.groupby("ext"):

        # Make composite for grouping
        composite = trackhub.CompositeTrack(
            name=f"{group_name}_{track_type}",
            short_label=f"{group_name}-{track_type}",
            dimensions=" ".join([f"{k}={v}" for k, v in dimensions.items()]),
            sortOrder=" ".join([f"{k}=+" for k in subgroup_definitions]),
            tracktype=track_type,
            visibility="hide",
            dragAndDrop="subTracks",
            allButtonPair="off",
        )

        # Need to add group if custom genome
        if custom_genome:
            composite.add_params(group=hub.hub)

        # Add the subgroup definitions
        composite.add_subgroups(
            [definition for definition in subgroup_definitions.values()])

        for track_file in df.itertuples():

            track_name_base = trackhub.helpers.sanitize(track_file.name)
            track_groupings = get_track_subgroups(
                track_file, subgroup_definitions)

            track = trackhub.Track(
                name=f"{track_name_base}_{track_groupings}",
                shortLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
                longLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
                source=track_file.path,
                autoScale="on",
                tracktype=track_type,
                windowingFunction="mean",
                subgroups={
                    subgroup: getattr(track_file, subgroup).lower()
                    for subgroup in subgroup_definitions
                },
                color=",".join(
                    [str(int(x * 255))
                     for x in color_mapping[track_file.samplename]]
                ),
            )

            # Add group to track if custom genome
            if custom_genome:
                track.add_params(group=hub.hub)

            # Append track to composite
            composite.add_subtrack(track)

        # Add to trackdb
        container.add_tracks(composite)


def add_composite_track(hub: trackhub.Hub,
                        container: trackhub.TrackDb,
                        track_details: pd.DataFrame,
                        subgroup_definitions: Dict[str, trackhub.SubGroupDefinition],
                        color_mapping: Dict[str, Tuple[float, float, float]],
                        custom_genome: bool = False,):
    
    dimensions = dict(
        zip([f"dim{d}" for d in ["X", "Y", "A", "B", "C", "D"]],
            subgroup_definitions)
    )

    for track_type, df in track_details.groupby("ext"):

        track_types = {"bigwig": "Signal_Pileup",
                       "bigbed": "Peaks_or_Regions_of_Interest"}

        # Make composite for each file type
        composite = trackhub.CompositeTrack(
            name=f"{track_types.get(track_type.lower(), 'Tracks')}",
            short_label=f"{track_type}",
            dimensions=" ".join([f"{k}={v}" for k, v in dimensions.items()]),
            sortOrder=" ".join([f"{k}=+" for k in subgroup_definitions]),
            tracktype=track_type,
            visibility="hide",
            dragAndDrop="subTracks",
            allButtonPair="off",
        )

        # Need to add group if custom genome
        if custom_genome:
            composite.add_params(group=hub.hub)

        # Add the subgroup definitions
        composite.add_subgroups(
            [definition for definition in subgroup_definitions.values()])


        # Add tracks to composite
        for track_file in df.itertuples():

            track_name_base = trackhub.helpers.sanitize(track_file.name)
            track_groupings = get_track_subgroups(
                track_file, subgroup_definitions)

            track = trackhub.Track(
                name=f"{track_groupings}_{track_type}",
                shortLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
                longLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
                source=track_file.path,
                autoScale="on",
                tracktype=track_type,
                windowingFunction="mean",
                subgroups={
                    subgroup: getattr(track_file, subgroup).lower()
                    for subgroup in subgroup_definitions
                },
                color=",".join(
                    [str(int(x * 255))
                     for x in color_mapping[track_file.samplename]]
                ),
            )

            # Add group to track if custom genome
            if custom_genome:
                track.add_params(group=hub.hub)

            # Append track to composite
            composite.add_subtrack(track)

        # Add to trackdb
        container.add_tracks(composite)


def add_tracks(
    hub: trackhub.Hub,
    parent: trackhub.BaseTrack,
    tracks: pd.DataFrame,
    color_mapping: Dict[str, Tuple[float, float, float]],
    custom_genome: bool = False
):

    for track_file in tracks.itertuples():

        track = trackhub.Track(
            name=track_file.samplename,
            source=track_file.path,
            tracktype=track_file.ext.strip("."),
            autoScale="on",
            color=",".join(
                [str(int(x * 255))
                 for x in color_mapping[track_file.samplename]]
            )

        )

        if custom_genome:
            track.add_params(group=hub.hub)

        parent.add_tracks(track)


def stage_hub(
    hub: trackhub.Hub,
    genome: trackhub.Genome,
    outdir: str,
    description_url_path: str = None,
    symlink: bool = False,
):

    tmpdir = "hub_staging"
    trackhub.upload.stage_hub(hub, staging=tmpdir)

    if description_url_path:
        description_basename = os.path.basename(description_url_path)
        with open(os.path.join(tmpdir, f"{hub.hub}.hub.txt"), "a") as hubtxt:
            hubtxt.write("\n")
            hubtxt.write(
                f"descriptionUrl {genome.genome}/{description_basename}\n")

        shutil.copy(
            description_url_path,
            os.path.join(tmpdir, genome.genome),
        )

    # Copy to the new location
    shutil.copytree(
        tmpdir,
        outdir,
        dirs_exist_ok=True,
        symlinks=False,
    )

    # shutil.rmtree(tempdir)


def make_hub(files: Tuple, output: str, details: Union[str, pd.DataFrame], group_by: str = None, generic_tracks: Tuple[str] = None, **kwargs):

    # Get file attributes
    df_file_attributes = get_file_attributes(files)

    # Design matrix in the format: filename samplename ATTRIBUTE_1 ATTRIBUTE_2 ...
    if isinstance(details, str):
        df_details = pd.read_csv(
            details, sep=r"\s+|\t|,", engine="python", index_col="filename")
    elif isinstance(details, pd.DataFrame):
        df_details = details
    else:
        raise RuntimeError("File detail not provided")

    df_file_attributes = get_groups_from_design_matrix(
        df_file_attributes=df_file_attributes, df_design=df_details
    )

    # Create hub
    hub = trackhub.Hub(
        hub=kwargs["hub_name"],
        short_label=kwargs.get("hub_short_label", kwargs["hub_name"]),
        long_label=kwargs.get("hub_long_label", kwargs["hub_name"]),
        email=kwargs["hub_email"],
    )

    # Genome
    custom_genome = kwargs.get("custom_genome", False)
    genome = get_genome_file(
        kwargs["genome_name"], custom_genome=custom_genome)

    # Create genomes file
    genomes_file = trackhub.GenomesFile()

    # Create trackdb
    trackdb = trackhub.TrackDb()

    # Add these to the hub
    hub.add_genomes_file(genomes_file)
    genome.add_trackdb(trackdb)
    genomes_file.add_genome(genome)

    # Create composite track definitiions
    subgroup_definitions = get_subgroup_definitions(
        df_file_attributes=df_file_attributes, grouping_column=group_by
    )

    # Get colours
    colors_mapping = get_colors(
        df_file_attributes=df_file_attributes, palette=kwargs.get(
            "palette", "hls")
    )

    # Add tracks to trackdb
    if group_by:
        for group_name, df in df_file_attributes.groupby(group_by):
            supertrack = trackhub.SuperTrack(name=group_name)
            add_composite_tracks_for_group(
                group_name=group_name,
                hub=hub,
                container=supertrack,
                track_details=df,
                subgroup_definitions=subgroup_definitions,
                color_mapping=colors_mapping,
                custom_genome=custom_genome,
            )

            if custom_genome:
                supertrack.add_params(group=hub.hub)

            trackdb.add_tracks(supertrack)

    else:
        add_composite_track(
            hub=hub,
            container=trackdb,
            track_details=df_file_attributes,
            subgroup_definitions=subgroup_definitions,
            color_mapping=colors_mapping,
            custom_genome=custom_genome,
        )

    if generic_tracks:
        add_tracks(
            hub=hub,
            parent=trackdb,
            tracks=get_file_attributes(generic_tracks),
            custom_genome=custom_genome,
        )

    # Copy hub to the correct directory
    stage_hub(
        hub=hub,
        genome=genome,
        outdir=output,
        description_url_path=kwargs.get("description_html"),
        symlink=kwargs.get("symlink"),
    )
