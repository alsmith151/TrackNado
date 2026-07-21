from __future__ import annotations
import pathlib
from typing import List, Optional
from loguru import logger
import pandas as pd
import typer
from rich.console import Console

import tracknado as tn
from .hosting import hub_url_from_profile

app = typer.Typer(help="Build and validate UCSC Genome Browser track hubs.")
console = Console()

@app.command()
def create(
    input_files: Optional[List[pathlib.Path]] = typer.Option(
        None, "--input-files", "-i", help="Local track files or glob patterns (for example, 'tracks/*.bigWig') to include in the hub."
    ),
    output: Optional[pathlib.Path] = typer.Option(
        None, "--output", "-o", help="The directory where the staged hub and tracknado_config.json will be created."
    ),
    metadata: Optional[pathlib.Path] = typer.Option(
        None, "--metadata", "-m", help="Path to a CSV/TSV containing track metadata. Must include a 'file_path' column."
    ),
    seqnado: bool = typer.Option(
        False, "--seqnado", help="Automatically extract sample metadata using the seqnado directory structure convention."
    ),
    grouping_regex: Optional[str] = typer.Option(
        None, "--grouping-regex", help="Regex with named groups for extracting grouping metadata from file names."
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
    hosting: Optional[str] = typer.Option(
        None, "--hosting", help="Name of a user-defined hosting profile used to report the hub URL."
    ),
    hosting_config: Optional[pathlib.Path] = typer.Option(
        None, "--hosting-config", help="Path to a TOML hosting-profile configuration file."
    ),
    hub_url_file: Optional[pathlib.Path] = typer.Option(
        None, "--hub-url-file", help="Write the resolved public hub URL to this file (requires --hosting)."
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
    sort_metadata: bool = typer.Option(
        False, "--sort-metadata", help="Sort metadata columns alphabetically (keeping standard columns first)."
    ),
    remove_existing: bool = typer.Option(
        False, "--remove-existing", help="Remove existing hub at output location before staging."
    ),
):
    """Create a UCSC track hub from a set of files."""
    if template:
        df = pd.DataFrame(columns=["file_path", "name", "track_type", "color", "supertrack", "composite", "overlay"])
        df.to_csv(template, index=False)
        logger.info(f"Created template metadata file at {template}")
        raise typer.Exit()

    if not output:
        console.print("[red]Error: Missing option '--output' / '-o'.[/red]")
        raise typer.Exit(code=1)
    if hub_url_file and not hosting:
        console.print("[red]Error: '--hub-url-file' requires '--hosting'.[/red]")
        raise typer.Exit(code=1)

    logger.info("Initializing TrackNado")
    
    try:
        builder = tn.configure_builder_from_inputs(
            input_files=input_files,
            metadata=metadata,
            seqnado=seqnado,
            grouping_regex=grouping_regex,
            convert=convert,
            chrom_sizes=chrom_sizes,
            supergroup_by=supergroup_by,
            subgroup_by=subgroup_by,
            overlay_by=overlay_by,
            color_by=color_by,
            sort_metadata=sort_metadata,
            custom_genome=custom_genome,
            twobit=twobit,
            organism=organism,
            default_pos=default_pos,
        )
    except ValueError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1)

    logger.info(f"Building hub '{hub_name}' for {genome_name}")
    try:
        hub = builder.build(
            name=hub_name,
            genome=genome_name,
            outdir=output,
            hub_email=hub_email,
            description_html=description
        )
    except ValueError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1)
    
    logger.info("Staging hub files")
    hub.stage_hub(remove_existing=remove_existing)
    
    logger.info(f"Hub created successfully at {output}")
    if hosting:
        try:
            hub_url = hub_url_from_profile(output, hub_name, hosting, hosting_config)
        except ValueError as exc:
            console.print(f"[yellow]Hub created, but no URL was reported: {exc}[/yellow]")
        else:
            logger.info(f"Hub URL: {hub_url}")
            if hub_url_file:
                try:
                    hub_url_file.expanduser().write_text(f"{hub_url}\n")
                except OSError as exc:
                    console.print(
                        f"[yellow]Hub created, but the URL could not be written to "
                        f"{hub_url_file}: {exc}[/yellow]"
                    )
                else:
                    logger.info(f"Hub URL written to {hub_url_file}")

@app.command()
def design(
    input_files: List[pathlib.Path] = typer.Option(
        ..., "--input-files", "-i", help="Track files or glob patterns (for example, 'tracks/*.bigWig') for the metadata table."
    ),
    output: pathlib.Path = typer.Option(
        ..., "--output", "-o", help="Path to write the editable metadata CSV/TSV to."
    ),
    seqnado: bool = typer.Option(
        False, "--seqnado", help="Pre-fill metadata using the seqnado directory structure convention."
    ),
    grouping_regex: Optional[str] = typer.Option(
        None, "--grouping-regex", help="Regex with named groups to pre-fill metadata from file names."
    ),
):
    """
    Generate an editable metadata table from a set of track files.

    Writes one row per file (file_path, name, ext, plus anything extracted via
    --seqnado/--grouping-regex) with empty color/supertrack/composite/overlay
    columns ready to fill in and pass to 'tracknado create --metadata'.
    """
    builder = tn.HubBuilder().add_tracks(input_files)

    if seqnado:
        from .extractors import from_seqnado_path
        builder.with_metadata_extractor(from_seqnado_path)

    if grouping_regex:
        builder.with_grouping_regex(grouping_regex)

    df = builder.to_dataframe()
    df = df.drop(columns=["path"], errors="ignore")

    for col in ["color", "supertrack", "composite", "overlay"]:
        if col not in df.columns:
            df[col] = ""

    df.to_csv(output, index=False)
    logger.info(f"Wrote editable metadata table ({len(df)} tracks) to {output}")

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
    sort_metadata: bool = typer.Option(
        False, "--sort-metadata", help="Sort metadata columns alphabetically (keeping standard columns first)."
    ),
    remove_existing: bool = typer.Option(
        False, "--remove-existing", help="Remove existing hub at output location before staging."
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
    
    if sort_metadata:
        main_builder.with_sort_metadata()
        
    hub = main_builder.build(
        name=hub_name,
        genome=genome_name,
        outdir=output,
        hub_email=hub_email
    )
    
    logger.info("Staging merged hub")
    hub.stage_hub(remove_existing=remove_existing)
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
            for err in validator.errors:
                logger.error(err)
            for warn in validator.warnings:
                logger.warning(warn)
            if not valid:
                raise typer.Exit(code=1)
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




