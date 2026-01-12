import itertools
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tracknado
from loguru import logger

# configre logger to write to snakemake log file if available
if "snakemake" in globals():
    logger.remove()
    logger.add(
        snakemake.log[0],
        format="{time} {level} {message}",
        level="INFO",
    )
    logger.add(sys.stderr, format="{time} {level} {message}", level="ERROR")


def get_rna_samplename(path: str):
    p = Path(path)
    return re.split(r"_[plus|minus]", p.name)[0]


try:
    logger.info("Generating UCSC Genome Browser hub...")
    logger.info(f"Assay: {snakemake.params.assay}, Files: {len(snakemake.input.data)}")

    # Set up details
    df = pd.DataFrame(
        snakemake.input.data,
        columns=["fn"],
    )

    # Resolve relative paths to absolute paths for consistent parsing
    df["fn"] = df["fn"].apply(lambda x: str(Path(x).resolve()))

    # extract extra cols
    def extract_metadata_from_path(path: str, key: str) -> str:
        p = Path(path)
        if key == "samplename":
            return p.stem.split(".")[0]
        elif key == "method":
            # e.g., ATAC_Tn5, ChIP_IP, RNA_plus, RNA_minus
            parts = p.stem.split("/")
            if len(parts) > 1:
                return parts[-2]
            else:
                return "unknown"
        elif key == "norm":
            # e.g., CPM, RPKM, TPM
            parts = p.stem.split("/")
            if len(parts) > 1:
                return parts[-1]
            else:
                return "unknown"
        else:
            return "unknown"
        


    color_by = snakemake.params.color_by
    subgroup_by = snakemake.params.subgroup_by if any(snakemake.params.subgroup_by) else None
    supergroup_by = snakemake.params.supergroup_by
    overlay_by = snakemake.params.overlay_by

    # Flatten all groupings to a list of strings
    grouping_cols = []
    if color_by:
        if isinstance(color_by, (list, tuple)):
            grouping_cols.extend(color_by)
        else:
            grouping_cols.append(color_by)
    for group in [subgroup_by, supergroup_by, overlay_by]:
        if group:
            grouping_cols.extend(group)

    for col in grouping_cols:
        df[col] = df["fn"].apply(lambda x: extract_metadata_from_path(x, col))

    # Create hub design
    design = tracknado.TrackDesign.from_design(
        df,
        color_by=snakemake.params.color_by,
        subgroup_by=snakemake.params.subgroup_by
        if any(snakemake.params.subgroup_by)
        else None,
        supergroup_by=snakemake.params.supergroup_by,
        overlay_by=snakemake.params.overlay_by,
    )

    
    

    # Generate hub files
    outdir = Path(str(snakemake.output.hub)).parent
    hub = tracknado.HubGenerator(
        track_design=design,
        genome=snakemake.params.genome,
        hub_name=snakemake.params.hub_name,
        description_html=Path(snakemake.input.report),
        hub_email=snakemake.params.hub_email,
        custom_genome=snakemake.params.custom_genome,
        genome_twobit=snakemake.params.genome_twobit,
        genome_organism=snakemake.params.genome_organism,
        genome_default_position=snakemake.params.genome_default_position,
        outdir=outdir,
    )

    hub.stage_hub()
    design.to_pickle(outdir / ".track_design.pkl")

    logger.info(f"✓ Hub files generated successfully in {outdir}")
    logger.info("=" * 80)

except Exception as e:
    logger.error("=" * 80)
    logger.error(f"ERROR: Failed to generate UCSC hub: {e}")
    logger.error(f"Exception type: {type(e).__name__}")
    import traceback

    logger.error(f"Traceback:\n{traceback.format_exc()}")
    logger.error("=" * 80)
    raise
