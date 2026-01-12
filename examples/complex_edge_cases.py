import os
import pathlib
import pandas as pd
import tracknado as tn
from loguru import logger

# 1. Setup dummy data for a complex scenario
# We want:
# - Mixed BED and BigWig files
# - Files in different directory depths
# - Mixed metadata (some from paths, some from DataFrame)
# - Duplicate names that need fixing
# - Deeply nested groupings

def create_complex_dummy_data(base_dir: pathlib.Path):
    """Creates a complex directory structure for testing."""
    tracks = [
        # Normal BigWigs
        "project/assay1/method1/raw/sample1.bigWig",
        "project/assay1/method1/raw/sample2.bigWig",
        # BED files that need conversion
        "project/assay1/method2/sorted/peaks1.bed",
        "project/assay2/method1/normalized/sample3.bw",
        # Duplicate sample name in different assay
        "project/assay2/method2/raw/sample1.bigWig", 
    ]
    
    for t in tracks:
        p = base_dir / t
        p.parent.mkdir(parents=True, exist_ok=True)
        # Create dummy content
        if p.suffix == ".bed":
            p.write_text("chr1\t100\t200\tpeak1\nchr1\t300\t400\tpeak2\n")
        else:
            p.write_text("dummy bigWig content")
            
    # Mock chrom.sizes
    (base_dir / "hg38.chrom.sizes").write_text("chr1\t248956422\n")
    return [base_dir / t for t in tracks]

def run_complex_scenario():
    base_dir = pathlib.Path("test_complex_hub")
    if base_dir.exists():
        import shutil
        shutil.rmtree(base_dir)
    base_dir.mkdir()
    
    files = create_complex_dummy_data(base_dir)
    logger.info(f"Created {len(files)} dummy files")
    
    # Setup Builder A: Using seqnado-style path extraction
    builder_a = (
        tn.HubBuilder()
        .add_tracks(files[:3])
        .with_metadata_extractor(tn.from_seqnado_path)
        .with_convert_files()
        .with_chrom_sizes(base_dir / "hg38.chrom.sizes")
        .group_by("assay", as_supertrack=True)
        .group_by("method")
        .color_by("samplename")
    )
    
    # Mock conversion to avoid Docker dependencies in this demo
    def mock_convert(input_bed, chrom_sizes, output_bb):
        logger.info(f"MOCK CONVERT: {input_bed} -> {output_bb}")
        output_bb.parent.mkdir(parents=True, exist_ok=True)
        output_bb.write_text("dummy bigBed content")
        return output_bb
        
    import tracknado.builder
    import tracknado.converters
    tracknado.builder.convert_bed_to_bigbed = mock_convert
    tracknado.converters.convert_bed_to_bigbed = mock_convert
    
    # Setup Builder B: Using manual DataFrame metadata
    df_data = {
        "fn": [str(files[3]), str(files[4])],
        "assay": ["manual_assay", "manual_assay"],
        "method": ["manual_method", "manual_method"],
        "custom_label": ["label1", "label2"]
    }
    df = pd.DataFrame(df_data)
    builder_b = (
        tn.HubBuilder()
        .add_tracks_from_df(df)
        .group_by("assay", as_supertrack=True)
        .group_by("method")
        .overlay_by("custom_label")
    )
    
    # MERGE Builders (Testing reconciliation of groupings)
    logger.info("Merging builders...")
    combined_builder = builder_a.merge(builder_b)
    
    # BUILD
    logger.info("Building merged hub...")
    hub = combined_builder.build(
        name="ComplexTestHub",
        genome="hg38",
        outdir=base_dir / "hub_output",
        hub_email="test@ox.ac.uk"
    )
    
    # STAGE
    logger.info("Staging hub...")
    hub.stage_hub()
    
    # VALIDATE
    logger.info("Validating hub structure...")
    validator = tn.HubValidator(base_dir / "hub_output")
    if validator.validate_all():
        logger.info("✅ HUB STRUCTURE VALID")
    else:
        logger.error("❌ HUB STRUCTURE INVALID")
        for err in validator.errors: logger.error(f"Error: {err}")
        
    logger.info(f"Complex example finished. Hub at {base_dir / 'hub_output'}")

if __name__ == "__main__":
    run_complex_scenario()
