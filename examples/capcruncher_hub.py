from __future__ import annotations
import os
import re
import pathlib
import pandas as pd
from tracknado import HubBuilder

def extract_capcruncher_metadata(path: pathlib.Path):
    r"""
    Replicates the legacy regex extraction:
    (?P<samplename>.*?)\.(?P<method>.*?)\.(?P<viewpoint>.*?)\.(?P<file_type>.*)
    """
    pattern = r"(?P<samplename>.*?)\.(?P<method>.*?)\.(?P<viewpoint>.*?)\.(?P<file_type>.*)"
    match = re.search(pattern, path.name)
    if match:
        meta = match.groupdict()
        # Replicate summary_method logic: bw.method.split("-")[0]
        meta["summary_method"] = meta["method"].split("-")[0]
        
        # Replicate categorisation logic (mock implementation of categorise_tracks)
        # In the original code, this was used to create separate composite tracks
        if "summary" in meta["method"]:
            meta["track_category"] = "summaries"
        else:
            meta["track_category"] = "raw_values"
            
        return meta
    return {}

def run_capcruncher_example():
    # 1. Setup mock environment
    project_dir = pathlib.Path("capcruncher_example")
    project_dir.mkdir(exist_ok=True)
    
    # Create some dummy bigWig files
    samples = ["sample1", "sample2"]
    methods = ["norm-summary", "raw"]
    viewpoints = ["VP1", "VP2"]
    
    bigwigs = []
    for s in samples:
        for m in methods:
            for v in viewpoints:
                fname = f"{s}.{m}.{v}.bigWig"
                path = project_dir / fname
                path.touch()
                bigwigs.append(path)
                
    # Create some dummy bigBed files
    bigbeds = []
    for v in viewpoints:
        path = project_dir / f"{v}.viewpoints.bigBed"
        path.touch()
        bigbeds.append(path)
        
    # Dummy stats report
    stats_report = project_dir / "pipeline_report.html"
    stats_report.touch()

    # 2. Build the hub using TrackNado
    # This replaces the ~150 lines of trackhub logic in the user's request
    builder = (
        HubBuilder()
        .add_tracks(bigwigs + bigbeds)
        .with_metadata_extractor(extract_capcruncher_metadata)
        
        # dimensions="dimX=samplename dimY=viewpoint dimA=summary_method"
        # TrackNado handles dimension creation from these columns automatically
        .group_by("viewpoint", "samplename", "summary_method")
        
        # If you want different categories to be separate SuperTracks (or containers)
        .group_by("track_category", as_supertrack=True)
        
        # Generate color mapping based on sample names using "hls" palette
        .color_by("samplename", palette="hls")
    )
    
    output_dir = project_dir / "hub_output"
    
    # 3. Final Build
    # This handles staging, custom genome setup, and descriptionUrl
    builder.build(
        name="CapCruncherHub",
        genome="hg38",
        outdir=output_dir,
        hub_email="user@example.edu",
        description_html=stats_report
    )
    
    print(f"Hub built successfully at {output_dir}")
    print(f"Config saved to {output_dir}/tracknado_config.json")

if __name__ == "__main__":
    run_capcruncher_example()
