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

### Print the URL with a hosting profile (optional)

If your group has a web-published storage area, you can set up a hosting profile
once. TrackNado then prints the correct hub URL whenever you build into that
area. The profile is personal: it is not shared with TrackNado users on other
HPCs or web servers.

#### Create your profile file

On the command line, run:

```bash
mkdir -p ~/.config/tracknado
nano ~/.config/tracknado/hosting.toml
```

The second command opens a new text file. Paste the following example, replacing
the values only if your local HPC and public web locations differ:

```toml
[hosting.example_web]
local_root = "/shared/track-hubs"
public_root = "https://tracks.example.org/public"
```

In `nano`, save with **Ctrl+O**, press **Enter** to accept the filename, then
exit with **Ctrl+X**. Do not put a trailing `/` at the end of either value.

#### Choose the two roots

`local_root` is the shared beginning of the HPC paths where you publish hubs.
`public_root` is the matching beginning of their public URLs. Choose them so the
remaining part of a path is identical in both places.

For example, an output directory and its public directory are:

```text
HPC output:   /shared/track-hubs/researcher/chipseq/experiment-2025-09-29
Public path:  https://tracks.example.org/public/researcher/chipseq/experiment-2025-09-29
```

The part that changes is the root:

```text
/shared/track-hubs
https://tracks.example.org/public
```

Everything after those roots (`researcher/chipseq/experiment-2025-09-29`) stays
the same. If you do not know the public URL corresponding to a directory, ask
your HPC or web-service administrator before creating the profile.

#### Use the profile

Build your hub as usual, adding `--hosting example_web`:

```bash
tracknado create \
  --metadata tracks.csv \
  --output /shared/track-hubs/researcher/chipseq/experiment-2025-09-29 \
  --hub-name example_hub \
  --genome-name hg38 \
  --hosting example_web
```

TrackNado prints:

```text
https://tracks.example.org/public/researcher/chipseq/experiment-2025-09-29/example_hub.hub.txt
```

To save that URL to a text file for a workflow or to share it later, add
`--hub-url-file`:

```bash
tracknado create \
  --metadata tracks.csv \
  --output /shared/track-hubs/researcher/chipseq/experiment-2025-09-29 \
  --hub-name example_hub \
  --genome-name hg38 \
  --hosting example_web \
  --hub-url-file hub_url.txt
```

This creates `hub_url.txt` in the current directory containing only the public
hub URL. The directory containing the file must already exist.

You can define more than one profile in the same file by adding another
`[hosting.name]` section, then select it with `--hosting name`. Use
`--hosting-config path/to/hosting.toml` if the profile file needs to live in a
project or shared location. Without `--hosting`, TrackNado stages the hub
normally and does not attempt to guess its public URL.

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
