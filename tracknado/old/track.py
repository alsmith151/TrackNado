import pandas as pd
import pathlib
from typing import Tuple
import seaborn as sns
import trackhub
from typing import Dict
import subprocess
import numpy as np
from collections import defaultdict


def convert_to_bigbed(bed: str, chrom_sizes: str, out: str):

    cmd = f"""
            export LC_ALL=C &&
            sort -k1,1 -k2,2n {bed} | cut -f 1-3 | grep -P 'chr(\d+|X|Y)' > {bed}.tmp && 
            bedToBigBed {bed}.tmp {chrom_sizes} {out}
            rm {bed}.tmp
           """
    subprocess.run(cmd, shell=True)
    return out



def get_file_attributes(files: Tuple, convert: bool = False, chrom_sizes: str = ""):

    if convert:
        files_new = []
        for fn in files:
            if fn.endswith(".bed"):
                files_new.append(convert_to_bigbed(fn, chrom_sizes, fn.replace(".bed", ".bigBed")))
            else:
                files_new.append(fn)
        files = tuple(files_new)
    
    df = pd.Series(files).to_frame("fn")
    paths = [pathlib.Path(fn) for fn in df["fn"].values]
    df["path"] = [str(p.absolute().resolve()) for p in paths]
    df["basename"] = [p.name for p in paths]
    df["name"] = [p.stem for p in paths]
    df["ext"] = [p.suffix.strip(".") for p in paths]

    # Deal with duplicate names
    basenames = defaultdict(int)
    for row in df.itertuples():
        basenames[row.basename] += 1
        if basenames[row.basename] > 1:

            name = f"{row.name}_{basenames[row.basename]}"
            basename = f"{row.basename}_{basenames[row.basename]}.{row.ext}"
            df.loc[row.Index, "name"] = name
            df.loc[row.Index, "basename"] = basename


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
        [str(getattr(track_details, subgroup)).lower() for subgroup in subgroup_definitions]
    )