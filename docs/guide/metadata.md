# Track Metadata

TrackNado centers around a **Track Design**—a table where each row is a track and columns represent metadata (sample name, assay, coloring, etc.).

## Positional Metadata

You can provide metadata via a CSV/TSV file using the `--metadata` flag. This file **must** include a `fn` column containing the paths to your track files. Delimiter (comma or tab) is auto-detected, so `.csv` and `.tsv` both work.

### Worked Example

Generate a starting template from your input files, then fill it in:

```bash
tracknado create --template tracks.csv
```

This produces a header-only file with the standard columns:

```csv
fn,name,track_type,color,supertrack,composite,overlay
```

Fill in one row per track. Only `fn` is required — every other column is optional metadata you can reference later with `--color-by`, `--supergroup-by`, `--subgroup-by`, or `--overlay-by`:

| fn | name | track_type | color | supertrack | composite | overlay |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| data/k562_ctcf_rep1.bw | K562 CTCF Rep1 | bigWig | 255,0,0 | ChIP-seq | K562 | CTCF |
| data/k562_ctcf_rep2.bw | K562 CTCF Rep2 | bigWig | 255,0,0 | ChIP-seq | K562 | CTCF |
| data/gm12878_ctcf_rep1.bw | GM12878 CTCF Rep1 | bigWig | 0,0,255 | ChIP-seq | GM12878 | CTCF |
| data/peaks.bb | Called Peaks | bigBed | | Annotation | | |

Then build the hub, pointing at whichever columns should drive grouping and color:

```bash
tracknado create \
  --metadata tracks.csv \
  --output my_hub \
  --genome-name hg38 \
  --supergroup-by supertrack \
  --subgroup-by composite \
  --overlay-by overlay \
  --color-by color
```

Equivalent Python API:

```python
import pandas as pd
import tracknado as tn

df = pd.read_csv("tracks.csv")

hub = (
    tn.HubBuilder()
    .add_tracks_from_df(df)
    .group_by("supertrack", as_supertrack=True)
    .group_by("composite")
    .overlay_by("overlay")
    .color_by("color")
    .build(name="my_hub", genome="hg38", outdir="my_hub/")
)
hub.stage_hub()
```

Notes:

- `color` accepts an `R,G,B` triple (0-255 each); leave blank to auto-assign via `--color-by` on a categorical column instead (e.g. `--color-by supertrack`).
- Blank cells in grouping columns (like `composite`/`overlay` for the peaks row above) are fine — see [Handling Missing Group Values](organization.md#handling-missing-group-values) to give them a catch-all label.

## Automated Extraction

You can also extract metadata from file paths using extraction functions. This allows you to encode metadata in your directory structure.

```python
from tracknado import HubBuilder, from_seqnado_path

builder = (
    HubBuilder()
    .add_tracks(["data/sample1.bigWig"])
    .with_metadata_extractor(from_seqnado_path) # Extracts from 'sample1'
)
```

### Extraction Patterns

TrackNado supports several built-in extractors:
- `from_seqnado_path`: Expects a standard bioinformatic directory structure.
- `from_filename_pattern`: Uses regex to pull metadata from names.
- `from_parent_dirs`: Uses the names of parent directories as metadata values.
- `with_static_metadata`: Adds constant key/value metadata (useful as a stub/default layer).
- `compose_extractors`: Chains extractors in order and resolves key collisions with `overwrite=True/False`.

### Stubbing + Layering Metadata

```python
import tracknado as tn

extractor = tn.compose_extractors(
    tn.with_static_metadata(condition="NA", replicate="1"),
    tn.from_filename_pattern(r"(?P<sample>.+?)_(?P<condition>.+?)\."),
    overwrite=False,  # keep defaults when a field is missing
)
```
