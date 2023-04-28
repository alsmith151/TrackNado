import trackhub
import pandas as pd
from typing import Dict, Tuple
import seaborn as sns


def get_genome_file(genome_name: str, custom_genome: bool = False, **kwargs):

    if not custom_genome:
        genome = trackhub.Genome(genome_name)
        groups_file = None
    else:
        genome = trackhub.Assembly(
            genome=genome_name,
            twobit_file=kwargs["genome_twobit"],
            organism=kwargs["genome_organism"],
            defaultPos=kwargs.get("hub_default_position", "chr1:10000-20000"),
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


def make_track_palette(
    df_file_attributes: pd.DataFrame,
    palette: str,
    color_by: Tuple = None,
):

    if len(color_by) == 1:
        unique_samples = df_file_attributes[color_by[0]].unique()
    else:
        unique_samples = (
            df_file_attributes[color_by]
            .drop_duplicates()
            .astype(str)
            .apply("".join, axis=1)
        )
    colors = sns.color_palette(palette=palette, n_colors=len(unique_samples))
    color_mapping = dict(zip(unique_samples, colors))
    return color_mapping