from __future__ import annotations
import os
import pathlib
from typing import List, Optional
from loguru import logger
import pandas as pd
import typer
from rich.console import Console
from rich.logging import RichHandler

import tracknado as tn

app = typer.Typer(help="TrackNado: Generate UCSC track hubs with ease. TrackNado go BRRRR!")
console = Console()

@app.command()
def create(
    input_files: Optional[List[pathlib.Path]] = typer.Option(
        None, "--input-files", "-i", help="A list of local track files (bigWig, bigBed, BAM, etc.) to include in the hub."
    ),
    output: Optional[pathlib.Path] = typer.Option(
        None, "--output", "-o", help="The directory where the staged hub and tracknado_config.json will be created."
    ),
    metadata: Optional[pathlib.Path] = typer.Option(
        None, "--metadata", "-m", help="Path to a CSV/TSV containing track metadata. Must include a 'fn' column with file paths."
    ),
    seqnado: bool = typer.Option(
        False, "--seqnado", help="Automatically extract sample metadata using the seqnado directory structure convention."
    ),
    hub_name: str = typer.Option(
        "HUB", "--hub-name", help="The short identifier for the hub (used in UCSC URL)."
    ),
    hub_email: str = typer.Option(
        "alastair.smith@ndcls.ox.ac.uk", "--hub-email", help="Contact email displayed on the hub's description page."
    ),
    genome_name: str = typer.Option(
        "hg38", "--genome-name", help="The genome assembly ID (e.g., hg38, mm10). For custom genomes, use this as the assembly name."
    ),
    color_by: Optional[str] = typer.Option(
        None, "--color-by", help="The metadata column name to use for determining track colors."
    ),
    supergroup_by: Optional[List[str]] = typer.Option(
        None, "--supergroup-by", help="One or more metadata columns to use for top-level track grouping (SuperTracks)."
    ),
    subgroup_by: Optional[List[str]] = typer.Option(
        None, "--subgroup-by", help="Metadata columns to define multi-dimensional CompositeTracks (matrix display)."
    ),
    overlay_by: Optional[List[str]] = typer.Option(
        None, "--overlay-by", help="Metadata columns to define OverlayTracks (e.g., multi-signal plots)."
    ),
    url_prefix: str = typer.Option(
        "https://userweb.molbiol.ox.ac.uk", "--url-prefix", help="Base URL where the hub will be hosted (used for final URL reporting)."
    ),
    convert: bool = typer.Option(
        False, "--convert", help="Enable automatic conversion of formats like BED -> bigBed or GTF -> bigGenePred."
    ),
    chrom_sizes: Optional[pathlib.Path] = typer.Option(
        None, "--chrom-sizes", help="Required for --convert. Path to a chrom.sizes file for the target genome."
    ),
    custom_genome: bool = typer.Option(
        False, "--custom-genome", help="Flag to indicate an Assembly Hub (custom genome) rather than a built-in UCSC genome."
    ),
    twobit: Optional[pathlib.Path] = typer.Option(
        None, "--twobit", help="Required for custom genomes. Path to the .2bit file containing the genome sequence."
    ),
    organism: Optional[str] = typer.Option(
        None, "--organism", help="Required for custom genomes. Common name of the organism (e.g., 'Human', 'Mouse')."
    ),
    default_pos: str = typer.Option(
        "chr1:10000-20000", "--default-pos", help="Set the initial viewing coordinates for the hub."
    ),
    description: Optional[pathlib.Path] = typer.Option(
        None, "--description", help="Path to an HTML file to display as the hub's landing page/documentation."
    ),
    template: Optional[pathlib.Path] = typer.Option(
        None, "--template", "-t", help="Create a template metadata file at the specified path and exit."
    ),
):
    """Create a UCSC track hub from a set of files."""
    if template:
        df = pd.DataFrame(columns=["fn", "name", "track_type", "color", "supertrack", "composite", "overlay"])
        df.to_csv(template, index=False)
        logger.info(f"Created template metadata file at {template}")
        raise typer.Exit()

    if not output:
        console.print("[red]Error: Missing option '--output' / '-o'.[/red]")
        raise typer.Exit(code=1)

    logger.info("Initializing TrackNado")
    
    builder = tn.HubBuilder()
    builder.convert_files = convert
    builder.chrom_sizes = chrom_sizes
    
    # 1. Add tracks
    if metadata:
        logger.info(f"Loading metadata from {metadata}")
        df = pd.read_csv(metadata, sep=None, engine="python")
        builder.add_tracks_from_df(df)
    elif input_files:
        logger.info(f"Adding {len(input_files)} input files")
        builder.add_tracks(input_files)
    else:
        console.print("[red]Error: Must provide --input-files or --metadata[/red]")
        raise typer.Exit(code=1)
        
    # 2. Add extractors
    if seqnado:
        builder.with_metadata_extractor(tn.from_seqnado_path)
        
    # 3. Configure groupings
    if supergroup_by:
        builder.group_by(*supergroup_by, as_supertrack=True)
    if subgroup_by:
        builder.group_by(*subgroup_by)
    if overlay_by:
        builder.overlay_by(*overlay_by)
    if color_by:
        builder.color_by(color_by)
        
    # 4. Custom Genome
    if custom_genome or twobit:
        if not twobit or not organism:
             console.print("[red]Error: --twobit and --organism are required for custom genomes[/red]")
             raise typer.Exit(code=1)
        builder.with_custom_genome(
            name=genome_name,
            twobit_file=twobit,
            organism=organism,
            default_position=default_pos
        )
        
    # 5. Build
    logger.info(f"Building hub '{hub_name}' for {genome_name}")
    hub = builder.build(
        name=hub_name,
        genome=genome_name,
        outdir=output,
        hub_email=hub_email,
        description_html=description
    )
    
    logger.info("Staging hub files")
    hub.stage_hub()
    
    logger.info(f"Hub created successfully at {output}")
    hub_url = f"{url_prefix.strip('/')}/{str(output).strip('/')}/{hub_name}.hub.txt"
    logger.info(f"Hub URL: {hub_url}")

@app.command()
def merge(
    input_configs: List[pathlib.Path] = typer.Argument(
        ..., help="A list of 'tracknado_config.json' files from previously generated hubs."
    ),
    output: pathlib.Path = typer.Option(
        ..., "--output", "-o", help="The directory where the new merged hub will be staged."
    ),
    hub_name: str = typer.Option(
        "MERGED_HUB", "--hub-name", help="The name for the combined hub."
    ),
    genome_name: str = typer.Option(
        "hg38", "--genome-name", help="The genome assembly for the combined hub."
    ),
    hub_email: str = typer.Option(
        "alastair.smith@ndcls.ox.ac.uk", "--hub-email", help="Contact email for the merged hub."
    ),
):
    """
    Merge multiple TrackNado hubs into one. 
    
    This command combines the track definitions from several sidecar configuration 
    files into a single unified UCSC Track Hub.
    """
    logger.info(f"Merging {len(input_configs)} hub configurations")
    
    builders = [tn.HubBuilder.from_json(cfg) for cfg in input_configs]
    
    main_builder = builders[0]
    if len(builders) > 1:
        main_builder.merge(*builders[1:])
        
    hub = main_builder.build(
        name=hub_name,
        genome=genome_name,
        outdir=output,
        hub_email=hub_email
    )
    
    logger.info("Staging merged hub")
    hub.stage_hub()
    logger.info(f"Merged hub created at {output}")

@app.command()
def validate(
    hub_path: pathlib.Path = typer.Argument(
        ..., help="Path to a hub directory or a 'hub.txt' file to check for errors."
    ),
    strict: bool = typer.Option(
        False, "--strict", help="If set, treats all warnings as errors during validation."
    ),
):
    """
    Validate a local hub directory or hub.txt file.
    
    Performs structural checks and uses the UCSC 'hubCheck' tool if available 
    to ensure the hub is correctly formatted and accessible.
    """
    logger.info(f"Validating hub at {hub_path}")
    
    path = hub_path
    if path.is_dir():
        # Try to find a hub.txt
        hub_files = list(path.glob("*.hub.txt"))
        if not hub_files:
            logger.error(f"No .hub.txt file found in {hub_path}")
            # Fallback to internal structure check
            validator = tn.HubValidator(path)
            valid = validator.validate_all()
            for err in validator.errors: logger.error(err)
            for warn in validator.warnings: logger.warning(warn)
            if not valid: raise typer.Exit(code=1)
            logger.info("Hub structure is valid (standard structure)")
            return
        path = hub_files[0]

    valid, message = tn.validate_hub(path, strict=strict)
    if valid:
        logger.info(f"Success: {message}")
    else:
        logger.error(f"Validation failed: {message}")
        raise typer.Exit(code=1)

def cli():
    app()

if __name__ == "__main__":
    app()








