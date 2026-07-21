# Fluent Python API

Use `HubBuilder` when hub creation is one step in a Python workflow. The builder mirrors the command-line build options and keeps the data paths, metadata rules, and layout settings together.

```python
import pandas as pd
import tracknado as tn

tracks = pd.read_csv("tracks.csv")

builder = (
    tn.HubBuilder()
    .add_tracks_from_df(tracks)
    .group_by("data_type", as_supertrack=True)
    .group_by("cell_type", "assay")
    .color_by("cell_type")
)

hub = builder.build(
    name="project_tracks",
    genome="hg38",
    outdir="my_hub",
    hub_email="you@example.org",
)
hub.stage_hub()
```

`build()` writes `tracknado_config.json` to the output directory. `stage_hub()` writes the UCSC hub files and copies the tracks into that directory. Run `tracknado validate my_hub` after the script completes.

To convert BED or annotation files as part of the build, add:

```python
builder.with_convert_files().with_chrom_sizes("hg38.chrom.sizes")
```

For a configuration-focused example, see [refactored_make_hub.py](https://github.com/alsmith151/TrackNado/blob/main/examples/refactored_make_hub.py). Its final build calls are commented out, so copy the `build(...).stage_hub()` pattern above when adapting it.
