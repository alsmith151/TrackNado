import pathlib
from re import sub
from typing import Dict, Tuple
import trackhub
import seaborn as sns
import shutil
import pandas as pd
import os
import numpy as np
import tempfile


def get_file_attributes(files: Tuple):

    df = pd.Series(files).to_frame("fn")
    paths = [pathlib.Path(fn) for fn in df["fn"].values]
    df["path"] = [str(p.resolve()) for p in paths]
    df["basename"] = [p.name for p in paths]
    df["name"] = [p.stem for p in paths]
    df["ext"] = [p.suffix.lower().strip(".") for p in paths]
    return df


def get_groups_from_regex(df_file_attributes: pd.DataFrame, pattern: str):

    groups = df_file_attributes["basename"].str.extract(pattern).reset_index()
    return pd.concat([df_file_attributes, groups], axis=1)


def get_groups_from_design_matrix(
    df_file_attributes: pd.DataFrame, df_design: pd.DataFrame
):
    return (
        df_file_attributes.set_index("basename")
        .join(df_design.set_index("basename"))
        .reset_index()
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
    group_members = (
        df_file_attributes.drop(columns=["fn", "path", "basename", "ext"])
        .loc[:, lambda df: [col for col in df.columns if not grouping_column == col]]
        .apply(lambda ser: ser.unique())
        .to_dict()
    )

    return {
        grouping: trackhub.SubGroupDefinition(
            name=grouping,
            label=grouping.capitalize(),
            mapping=[g.lower() for g in group],
        )
        for grouping, group in group_members.items()
    }


def get_colors(df_file_attributes: pd.DataFrame, palette: str):
    unique_samples = df_file_attributes["samplename"].unique()
    colors = sns.color_palette(palette=palette, n_colors=len(unique_samples))
    color_mapping = dict(zip(unique_samples, colors))
    return color_mapping


def add_composite_tracks_to_hub(
    hub: trackhub.Hub,
    trackdb: trackhub.TrackDb,
    bigwigs: pd.DataFrame,
    subgroup_definitions: Dict[str, trackhub.SubGroupDefinition],
    color_mapping: Dict[str, Tuple[float, float, float]],
    grouping_column: str = None,
    custom_genome: bool = False,
):

    dimensions = dict(
        zip([f"dim{d}" for d in ["X", "Y", "A", "B", "C", "D"]], subgroup_definitions)
    )

    for group_name, df in bigwigs.groupby(grouping_column):

        # Make composite for grouping
        composite = trackhub.CompositeTrack(
            name=group_name,
            short_label=group_name,
            dimensions=" ".join([f"{k}={v}" for k, v in dimensions.items()]),
            sortOrder=" ".join([f"{k}=+" for k in subgroup_definitions]),
            tracktype="bigWig",
            visibility="hide",
            dragAndDrop="subTracks",
            allButtonPair="off",
        )

        # Need to add group if custom genome
        if custom_genome:
            composite.add_params(group=hub.hub)

        # Add the subgroup definitions
        composite.add_subgroups([*subgroup_definitions.values()])

        # Create bigwig tracks
        for bw in df.itertuples():
            track = trackhub.Track(
                name=bw.samplename,
                source=bw.fn,
                autoScale="on",
                tracktype="bigWig",
                windowingFunction="mean",
                subgroups={
                    getattr(bw, subgroup).lower() for subgroup in subgroup_definitions
                },
                color=",".join(
                    [str(int(x * 255)) for x in color_mapping[bw.samplename]]
                ),
            )

            # Add group to track if custom genome
            if custom_genome:
                track.add_params(group=hub.hub)

            # Append track to composite
            composite.add_subtrack(track)

        # Add to trackdb
        trackdb.add_tracks(composite)


def add_tracks_to_hub(
    hub: trackhub.Hub,
    trackdb: trackhub.TrackDb,
    tracks: pd.DataFrame,
    custom_genome: bool = False,
):

    for track_file in tracks.itertuples():

        track = trackhub.Track(
            name=track_file.samplename,
            source=track_file.fn,
            tracktype=track_file.ext.strip("."),
        )

        if custom_genome:
            track.add_params(group=hub.hub)

        trackdb.add_tracks(track)


def stage_hub(
    hub: trackhub.Hub,
    genome: trackhub.Genome,
    outdir: str,
    description_url_path: str = None,
    symlink: bool = False,
):

    with tempfile.TemporaryDirectory() as tmpdir:
        trackhub.upload.stage_hub(hub, staging=outdir)

        if description_url_path:
            description_basename = os.path.basename(description_url_path)
            with open(os.path.join(tmpdir, f"{hub.hub}.hub.txt"), "a") as hubtxt:
                hubtxt.write("\n")
                hubtxt.write(f"descriptionUrl {genome.genome}/{description_basename}\n")

            shutil.copy(
                description_url_path,
                os.path.join(tmpdir, genome.genome, description_basename),
            )

        # Copy to the new location
        shutil.copytree(
            tmpdir,
            outdir,
            dirs_exist_ok=True,
            symlinks=symlink,
        )


def make_hub(files: Tuple, output: str, design: str, groups: str = None, **kwargs):

    # Get file attributes
    df_file_attributes = get_file_attributes(files)

    # Design matrix in the format: filename samplename ATTRIBUTE_1 ATTRIBUTE_2 ...
    df_design = pd.read_csv(design, sep=r"\s+|\t|,", engine="python", index_col=0)
    df_file_attributes = get_groups_from_design_matrix(
        df_file_attributes=df_file_attributes, df_design=df_design
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
    genome = get_genome_file(kwargs["genome_name"], custom_genome=custom_genome)

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
        df_file_attributes=df_file_attributes, grouping_column=groups
    )

    # Get colours
    colors_mapping = get_colors(
        df_file_attributes=df_file_attributes, palette=kwargs.get("palette", "hls")
    )

    # Add tracks to hub
    df_bigwigs = df_file_attributes.loc[
        lambda df: df["ext"].str.lower().isin([".bigwig", "bigwig"])
    ]

    add_composite_tracks_to_hub(
        hub,
        trackdb,
        bigwigs=df_bigwigs,
        subgroup_definitions=subgroup_definitions,
        color_mapping=colors_mapping,
        grouping_column=groups,
        custom_genome=custom_genome,
    )

    # Add all other files to the hub
    df_other_tracks = df_file_attributes.loc[
        lambda df: ~(df["ext"].str.lower().isin(["bigwig", ".bigwig"]))
    ]

    add_tracks_to_hub(hub, trackdb, tracks=df_other_tracks, custom_genome=custom_genome)

    stage_hub(hub, genome, outdir=output, description_url_path=kwargs["description_url_path"], symlink=kwargs.get("symlink", False))
