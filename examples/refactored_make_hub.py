import tracknado as tn
from pathlib import Path

# This example demonstrates how to use the new refactored TrackNado API
# to create a UCSC Genome Browser hub from a list of files.

# 1. Provide your input files
files = [
    Path("ATAC/ATAC_Tn5/CPM/sample1_plus.bigWig"),
    Path("ATAC/ATAC_Tn5/CPM/sample1_minus.bigWig"),
    Path("ATAC/ATAC_Tn5/CPM/sample2_plus.bigWig"),
    Path("ChIP/ChIP_IP/TPM/sample3.bigWig"),
]

# 2. Use the fluent HubBuilder API
hub = (
    tn.HubBuilder()
    .add_tracks(files)
    # Use built-in seqnado extractor
    .with_metadata_extractor(tn.from_seqnado_path)
    # Configure groupings
    .group_by("method", as_supertrack=True)
    .group_by("samplename")
    # Configure aesthetics
    .color_by("samplename")
    .overlay_by("samplename")
)

print("Hub design prepared successfully!")
print(f"Total tracks: {len(hub.tracks)}")

# 3. Build and stage the hub
# This will automatically save 'output/hub/tracknado_config.json'
# hub.build(
#     name="my_refactored_hub",
#     genome="hg38",
#     outdir="output/hub",
#     hub_email="user@example.com"
# ).stage_hub()

# 4. Improved Merging Workflow
# You can load previously staged hubs via their sidecar JSON config
# h1 = tn.HubBuilder.from_json("output/hub1/tracknado_config.json")
# h2 = tn.HubBuilder.from_json("output/hub2/tracknado_config.json")

# and merge them easily:
# mega_hub = h1.merge(h2).build(name="MergedHub", ...)

# 5. Local validation
# valid, message = tn.validate_hub(Path("output/hub/my_refactored_hub.hub.txt"))
# print(f"Validation: {valid}, {message}")
