# TrackNado

TrackNado builds [UCSC Genome Browser track hubs](https://genome.ucsc.edu/goldenPath/help/hgTrackHubHelp.html) from local track files and a small table of metadata. Use it when you want a repeatable way to stage bigWig, bigBed, BAM, and annotation tracks for a UCSC hub.

The command-line interface is the simplest way to start. The Python API exposes the same build steps for pipelines and scripts.

## Install

```bash
pip install tracknado
```

## Build a hub

This example creates a hub for four tracks on `hg38`.

1. Make an editable metadata table from the files:

   ```bash
   tracknado design \
     -i tracks/*.bw \
     -i tracks/*.bb \
     -o tracks.csv
   ```

2. Edit `tracks.csv`. Every row is one track. `file_path` is required; the other columns describe how the track should appear in the browser.

   ```csv
   file_path,name,ext,assay,cell_type,color
   tracks/k562_ctcf.bw,K562 CTCF,bigWig,ChIP-seq,K562,crimson
   tracks/gm12878_ctcf.bw,GM12878 CTCF,bigWig,ChIP-seq,GM12878,#4169E1
   tracks/k562_atac.bw,K562 ATAC,bigWig,ATAC-seq,K562,darkorange
   tracks/peaks.bb,Called peaks,bigBed,Peaks,All,#464646
   ```

3. Build and stage the hub:

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

4. Check the staged hub:

   ```bash
   tracknado validate my_hub
   ```

`my_hub` now contains `project_tracks.hub.txt`, the genome and trackDb files, copied track files, and `tracknado_config.json`. Publish that directory through a web server, then give UCSC the URL to the `.hub.txt` file.

## Common changes

- Add a top-level folder-like grouping: `--supergroup-by assay`.
- Give tracks colours from a categorical metadata field: `--color-by cell_type`.
- Combine related signal tracks in one display: `--overlay-by condition`.
- Convert BED, GTF, or GFF inputs while building: add `--convert --chrom-sizes hg38.chrom.sizes`.
- Build an assembly hub for a private genome: add `--custom-genome --twobit reference.2bit --organism "Species name"`.

See the [documentation](https://alsmith151.github.io/TrackNado/) for the complete walkthrough, metadata rules, track layouts, and Python examples.

## Python API

```python
import pandas as pd
import tracknado as tn

tracks = pd.read_csv("tracks.csv")
hub = (
    tn.HubBuilder()
    .add_tracks_from_df(tracks)
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

## License

TrackNado is distributed under the [GNU General Public License v3](LICENSE).
