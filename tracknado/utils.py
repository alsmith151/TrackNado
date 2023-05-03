import pathlib
from typing import Union
import click
import pandas as pd


def has_valid_chromsizes(chrom_sizes: Union[str, pathlib.Path]) -> bool:
    """Check if the chromosome sizes file is valid"""

    if not chrom_sizes:
        return False

    if not pathlib.Path(chrom_sizes).is_file():
        return False

    return True


def has_tracks_to_convert(df: pd.DataFrame) -> bool:
    """Check if the design has tracks that need to be converted"""

    bed_files = df[df["ext"] == "bed"]
    if bed_files.empty:
        return False

    return True
