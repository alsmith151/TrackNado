import os
import pathlib
import shutil
import re
from typing import Dict, Tuple, Union, List

import tempfile
import numpy as np
import pandas as pd
import seaborn as sns
import trackhub
import subprocess

from .track import get_file_attributes, get_groups_from_design_matrix
from .hub_setup import get_genome_file, make_track_palette
from .grouping import (
    get_subgroup_definitions,
    add_composite_tracks_to_container,
    add_overlay_track_to_container,
    add_hub_group,
)


def stage_hub(
    hub: trackhub.Hub,
    genome: trackhub.Genome,
    outdir: str,
    description_url_path: str = None,
):

    with tempfile.TemporaryDirectory() as tmpdir:
        trackhub.upload.stage_hub(hub, staging=tmpdir)

        if description_url_path:
            description_basename = os.path.basename(description_url_path)
            with open(os.path.join(tmpdir, f"{hub.hub}.hub.txt"), "a") as hubtxt:
                hubtxt.write("\n")
                hubtxt.write(f"descriptionUrl {genome.genome}/{description_basename}\n")

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

        subprocess.run(["chmod", "-R", "2755", outdir])
    

def get_grouping_columns(cols):
    try:
        if len(cols) > 1:
            return cols
        else:
            return cols[0]
    except IndexError:
        return None


def make_hub(
    files: Tuple,
    output: str,
    details: Union[str, pd.DataFrame] = None,
    group_composite: Tuple[str] = None,
    group_overlay: Tuple[str] = None,
    **kwargs,
):

    # Set-up varibles
    group_composite = get_grouping_columns(group_composite)
    group_overlay = get_grouping_columns(group_overlay)

    # Get file attributes
    df_file_attributes = get_file_attributes(
        files,
        convert=kwargs.get("convert", False),
        chrom_sizes=kwargs.get("chrom_sizes", None),
    )

    # Design matrix in the format: filename samplename ATTRIBUTE_1 ATTRIBUTE_2 ...
    if isinstance(details, str):
        df_details = pd.read_csv(
            details, sep=r"\s+|\t|,", engine="python", index_col="filename"
        )
    elif isinstance(details, pd.DataFrame):
        df_details = details
    else:
        df_details = pd.DataFrame()
        # raise RuntimeError("File detail not provided")

    if not df_details.empty:
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
    genome = get_genome_file(**kwargs)

    # Create genomes file
    genomes_file = trackhub.GenomesFile()

    # Create trackdb
    trackdb = trackhub.TrackDb()

    # Add these to the hub
    hub.add_genomes_file(genomes_file)
    genome.add_trackdb(trackdb)
    genomes_file.add_genome(genome)

    # # Create composite track definitions
    subgroup_definitions = get_subgroup_definitions(
        df_file_attributes=df_file_attributes, grouping_columns=group_composite
    )

    color_tracks_by = list(kwargs.get("color_by", ("name",)))

    color_mapping = make_track_palette(
        df_file_attributes=df_file_attributes,
        palette=kwargs.get("palette", "hls"),
        color_by=color_tracks_by,
    )

    # Make supertracks to hold any groupings
    supertracks = dict()

    # Composite tracks
    if group_composite:
        for group_name, df in df_file_attributes.groupby(group_composite):
            supertracks[group_name] = trackhub.SuperTrack(name=group_name)

            add_composite_tracks_to_container(
                container=supertracks[group_name],
                track_details=df,
                subgroup_definitions=subgroup_definitions,
                color_by=color_tracks_by,
                color_mapping=color_mapping,
                track_suffix=group_name,
                custom_genome=custom_genome,
                hub=hub,
                genome_twobit=kwargs["genome_twobit"],
            )
            add_hub_group(
                container=supertracks[group_name], hub=hub, custom_genome=custom_genome
            )
    else:
        add_composite_tracks_to_container(
            container=trackdb,
            track_details=df_file_attributes,
            subgroup_definitions=subgroup_definitions,
            color_by=color_tracks_by,
            color_mapping=color_mapping,
            custom_genome=custom_genome,
            hub=hub,
            genome_twobit=kwargs["genome_twobit"],
        )

    if group_overlay:
        for group_name, df in df_file_attributes.groupby(group_overlay):

            supertrack_exists = False
            if not group_name in supertracks:
                supertrack_exists = True
                supertracks[group_name] = trackhub.SuperTrack(name=group_name)

            add_overlay_track_to_container(
                track_name=group_name,
                container=supertracks[group_name],
                track_details=df,
                color_by=color_tracks_by,
                color_mapping=color_mapping,
                custom_genome=custom_genome,
                hub=hub,
            )

            if not supertrack_exists:
                add_hub_group(
                    container=supertracks[group_name],
                    hub=hub,
                    custom_genome=custom_genome,
                )

    trackdb.add_tracks(supertracks.values())

    ## Add generic tracks
    for track in kwargs["generic_tracks"]:
        track_name = trackhub.helpers.sanitize(os.path.basename(t))
        track_path = os.path.abspath(track)
        t = trackhub.Track(
            name=track_name,
            source=track_path,
            tracktype=os.path.basename(track_name).split(".")[1],
        )

        trackdb.add_tracks(track)

    # Copy hub to the correct directory
    stage_hub(
        hub=hub,
        genome=genome,
        outdir=output,
        description_url_path=kwargs.get("description_html"),
    )
