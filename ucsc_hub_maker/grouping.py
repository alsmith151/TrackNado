import trackhub
import pandas as pd
from typing import Dict, Tuple
import re
import pathlib

from .track import get_track_subgroups

def get_subgroup_definitions(
    df_file_attributes: pd.DataFrame, grouping_columns: str = None
):

    columns_to_drop = ["fn", "path", "basename", "ext", "name"]

    if grouping_columns:
        columns_to_drop.append(grouping_columns)

    group_members = {
        col: df_file_attributes[col].unique()
        for col in df_file_attributes.drop(columns=columns_to_drop, errors="ignore")
    }

    subgroups = {
        grouping: trackhub.SubGroupDefinition(
            name=grouping,
            label=grouping.capitalize(),
            mapping={str(g).lower(): g for g in group},
        )
        for grouping, group in group_members.items()
    }

    return subgroups


def add_hub_group(container: trackhub.Track, hub: trackhub.Hub = None, custom_genome: bool = False):
    if custom_genome:
        if hub:
            container.add_params(group=hub.hub)
        else:
            raise ValueError("Custom genome specified but no hub provided")


def add_composite_tracks_to_container(
    container: trackhub.TrackDb,
    track_details: pd.DataFrame,
    subgroup_definitions: Dict[str, trackhub.SubGroupDefinition],
    color_by: list,
    color_mapping: Dict[str, Tuple[float, float, float]],
    track_suffix: str = "",
    custom_genome: bool = False,
    genome_twobit: str = "",  
    hub: trackhub.Hub = None,
):

    dimensions = dict(
        zip([f"dim{d}" for d in ["X", "Y", "A", "B", "C", "D"]], subgroup_definitions)
    )

    for track_type, df in track_details.groupby("ext"):

        track_types = {
            "bigwig": "Signal_Pileup",
            "bigbed": "Peaks_or_Regions_of_Interest",
        }


        # Make composite for each file type
        composite = trackhub.CompositeTrack(
            name=f"{track_types.get(str(track_type.lower()), 'Tracks')}",
            short_label=f"{track_type}",
            dimensions=" ".join([f"{k}={v}" for k, v in dimensions.items()]) if dimensions else None,
            sortOrder=" ".join([f"{k}=+" for k in subgroup_definitions]) if subgroup_definitions else None,
            tracktype=track_type,
            visibility="hide",
            dragAndDrop="subTracks",
            allButtonPair="off",
        )
        
        # Add group if custom genome
        add_hub_group(container=composite, hub=hub, custom_genome=custom_genome)
            

        # Add the subgroup definitions
        composite.add_subgroups(
            [definition for definition in subgroup_definitions.values()]
        )

        # Add tracks to composite
        for track_file in df.itertuples():
            

            path = pathlib.Path(track_file.path)
            track_name_base = trackhub.helpers.sanitize(track_file.name)
            track_groupings = get_track_subgroups(track_file, subgroup_definitions)

            track = trackhub.Track(
                name=f"{track_name_base}_{track_type}{'_' + track_suffix if track_suffix else ''}",
                shortLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
                longLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
                source=track_file.path,
                autoScale="on",
                tracktype=track_type,
                windowingFunction="mean",
                subgroups={
                    subgroup: str(getattr(track_file, subgroup)).lower()
                    for subgroup in subgroup_definitions
                },
                color=",".join(
                    [
                        str(int(x * 255))
                        for x in color_mapping[
                            "".join(getattr(track_file, cb) for cb in color_by)
                        ]
                    ]
                ),
            )

            # Add group to track if custom genome
            add_hub_group(container=track, hub=hub, custom_genome=custom_genome)

            # Append track to composite
            composite.add_subtrack(track)

        # Add to trackdb
        container.add_tracks(composite)


def add_overlay_track_to_container(
    track_name: str,
    container: trackhub.TrackDb,
    track_details: pd.DataFrame,
    color_by: list,
    color_mapping: Dict[str, Tuple[float, float, float]],
    custom_genome: bool = False,
    hub: trackhub.Hub = None,
):

    overlay = trackhub.AggregateTrack(
        aggregate="transparentOverlay",
        visibility="full",
        tracktype="bigWig",
        maxHeightPixels="8:80:50",
        showSubtrackColorOnUi="on",
        name=track_name,
    )

    # Need to add group if custom genome
    add_hub_group(container=overlay, hub=hub, custom_genome=custom_genome)

    for track_file in track_details.itertuples():

        track_name_base = trackhub.helpers.sanitize(track_file.name)

        track = trackhub.Track(
            name=f"{track_name_base}_{track_name}_overlay",
            shortLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
            longLabel=" ".join(re.split(r"[.|_|\s+|-]", track_file.name)),
            source=track_file.path,
            autoScale="on",
            tracktype="bigWig",
            windowingFunction="mean",
            color=",".join(
                [
                    str(int(x * 255))
                    for x in color_mapping[
                        "".join(getattr(track_file, cb) for cb in color_by)
                    ]
                ]
            ),
        )

        # Add group to track if custom genome
        add_hub_group(container=track, hub=hub, custom_genome=custom_genome)

        # Append track to composite
        overlay.add_subtrack(track)

        # Add to trackdb
        container.add_tracks(overlay)




def add_generic_tracks(
    parent: trackhub.BaseTrack,
    track_details: pd.DataFrame,
    color_by: list,
    color_mapping: Dict[str, Tuple[float, float, float]],
    custom_genome: bool = False,
    hub: trackhub.Hub = None,
):

    for track_file in track_details.itertuples():

        track = trackhub.Track(
            name=track_file.samplename,
            source=track_file.path,
            tracktype=track_file.ext.strip("."),
            autoScale="on",
            color=",".join(
                [
                    str(int(x * 255))
                    for x in color_mapping[
                        "".join(getattr(track_file, cb) for cb in color_by)
                    ]
                ]
            ),
        )

        add_hub_group(container=track, hub=hub, custom_genome=custom_genome)
        parent.add_tracks(track)

