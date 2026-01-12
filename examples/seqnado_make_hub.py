import sys
from pathlib import Path
import tracknado as tn
from loguru import logger

# Configure logger to write to snakemake log file if available
if "snakemake" in globals():
    logger.remove()
    logger.add(
        snakemake.log[0],
        format="{time} {level} {message}",
        level="INFO",
    )
    logger.add(sys.stderr, format="{time} {level} {message}", level="ERROR")

try:
    logger.info("🌪️  TrackNado: Generating UCSC Genome Browser hub...")
    logger.info(f"Assay: {snakemake.params.assay}, Files: {len(snakemake.input.data)}")

    # 1. Initialize the HubBuilder with the input files
    # We use the fluent API to configure everything in a single chain
    builder = (
        tn.HubBuilder()
        .add_tracks(snakemake.input.data)
        
        # 2. Use the built-in seqnado path extractor
        # This automatically handles directory structures like assay/method/norm/sample.bw
        .with_metadata_extractor(tn.from_seqnado_path)
        
        # 3. Configure groupings based on metadata columns
        # We use the parameters provided via Snakemake
        .group_by(*snakemake.params.supergroup_by, as_supertrack=True)
        .group_by(*snakemake.params.subgroup_by)
        .overlay_by(*snakemake.params.overlay_by)
        .color_by(snakemake.params.color_by)
    )

    # 4. Build and stage the hub
    # This automatically generates hub.txt, genomes.txt, trackDb.txt
    # and saves a 'tracknado_config.json' sidecar for easy merging later.
    outdir = Path(str(snakemake.output.hub)).parent
    hub = builder.build(
        name=snakemake.params.hub_name,
        genome=snakemake.params.genome,
        outdir=outdir,
        hub_email=snakemake.params.hub_email,
        description_html=Path(snakemake.input.report) if hasattr(snakemake.input, "report") else None,
        custom_genome=snakemake.params.custom_genome,
        genome_twobit=snakemake.params.genome_twobit,
        genome_organism=snakemake.params.genome_organism,
        genome_default_position=snakemake.params.genome_default_position,
    )

    hub.stage_hub()

    logger.info(f"✓ Hub successfully generated in {outdir}")
    logger.info("💡 Pro-tip: You can merge multiple hubs later using 'tracknado merge'")

except Exception as e:
    logger.error("=" * 80)
    logger.error(f"❌ ERROR: Failed to generate UCSC hub: {e}")
    import traceback
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    logger.error("=" * 80)
    raise
