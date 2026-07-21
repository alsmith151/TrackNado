# Getting started

This guide builds a small `hg38` hub from existing bigWig and bigBed files. It uses the command line because it makes the files and decisions visible; the same metadata table also works with the Python API.

## Before you begin

Install TrackNado and make sure the input files are readable from the directory where you run the command.

```bash
pip install tracknado
```

For this first hub, use UCSC-ready files (`.bw`/`.bigWig` and `.bb`/`.bigBed`). See [File conversion](conversion.md) if you have BED, GTF, or GFF files instead.

## 1. Create a track table

Ask TrackNado to inspect the files and make a starting CSV:

```bash
tracknado design \
  -i tracks/*.bw \
  -i tracks/*.bb \
  -o tracks.csv
```

The generated table includes the file path (`file_path`), a default label (`name`), and detected type (`ext`). Edit it to add useful labels and grouping fields:

```csv
file_path,name,ext,assay,cell_type,color
tracks/k562_ctcf.bw,K562 CTCF,bigWig,ChIP-seq,K562,crimson
tracks/gm12878_ctcf.bw,GM12878 CTCF,bigWig,ChIP-seq,GM12878,#4169E1
tracks/k562_atac.bw,K562 ATAC,bigWig,ATAC-seq,K562,darkorange
tracks/peaks.bb,Called peaks,bigBed,Peaks,All,#464646
```

Only `file_path` is mandatory. `name` becomes the visible label. The `assay` and `cell_type` columns in this example will become a browser matrix.

## 2. Build the hub

```bash
tracknado create \
  --metadata tracks.csv \
  --output my_hub \
  --hub-name project_tracks \
  --hub-email you@example.org \
  --genome-name hg38 \
  --subgroup-by assay \
  --subgroup-by cell_type
```

`--output` is the directory TrackNado stages. `--hub-name` determines the hub file name: this command produces `my_hub/project_tracks.hub.txt`.

`--subgroup-by` can be repeated. With two fields, UCSC presents the tracks as a composite-track matrix. If a matrix would not help your users, leave those options out; the hub still builds.

## 3. Validate the result

```bash
tracknado validate my_hub
```

Run this before publishing. It checks the staged structure and uses UCSC's `hubCheck` when that executable is available.

## 4. Publish and load it

Copy the entire `my_hub` directory to a location served over HTTP(S). Do not move only the `.hub.txt` file: its relative links point to the accompanying genome, trackDb, and data files.

In the UCSC Genome Browser, open **My Data → Track Hubs**, then enter the public URL to:

```text
https://example.org/path/to/my_hub/project_tracks.hub.txt
```

## Build the same hub from Python

```python
import pandas as pd
import tracknado as tn

df = pd.read_csv("tracks.csv")
hub = (
    tn.HubBuilder()
    .add_tracks_from_df(df)
    .group_by("assay", "cell_type")
    .build(
        name="project_tracks",
        genome="hg38",
        outdir="my_hub",
        hub_email="you@example.org",
    )
)
hub.stage_hub()
```

Use the [metadata guide](metadata.md) to refine the table, then [organise tracks](organization.md) to choose a suitable browser layout.
