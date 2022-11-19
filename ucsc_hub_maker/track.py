import pandas as pd
import pathlib
from typing import Tuple
import seaborn as sns
import trackhub
from typing import Dict


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
        df_file_attributes.set_index("fn")
        .join(df_design)
        .reset_index()
        .rename(columns={"index": "fn"})
    )

def get_track_subgroups(
    track_details: tuple,
    subgroup_definitions: Dict[str, trackhub.SubGroupDefinition],
):
    return "_".join(
        [getattr(track_details, subgroup).lower() for subgroup in subgroup_definitions]
    )