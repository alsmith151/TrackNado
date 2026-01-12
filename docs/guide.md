# TrackNado User Guide

TrackNado is a high-level library and CLI for generating UCSC Track Hubs from sequencing data. It simplifies the complex process of metadata management, track grouping, and file conversion.

## Quick Start (CLI)

The easiest way to get started is by using the `create` command.

```bash
# Generate a metadata template
tracknado create --template tracks.csv

# After filling out tracks.csv with your file paths and metadata
tracknado create --metadata tracks.csv --output my_hub --genome-name hg38
```

## Track Metadata

TrackNado centers around a **Track Design**—a table where each row is a track and columns represent metadata (sample name, assay, coloring, etc.).

### Positional Metadata
You can provide metadata via a CSV/TSV file using the `--metadata` flag. This file **must** include a `fn` column containing the paths to your track files.

### Automated Extraction
You can also extract metadata from file paths using functions:

```python
from tracknado import HubBuilder, from_seqnado_path

builder = (
    HubBuilder()
    .add_tracks(["data/sample1.bigWig"])
    .with_metadata_extractor(from_seqnado_path) # Extracts from 'sample1'
)
```

## Organizing Your Hub

TrackNado supports three main types of track organization:

1.  **SuperTracks**: Top-level containers that group tracks together.
    *   CLI: `--supergroup-by column_name`
    *   API: `.group_by("column_name", as_supertrack=True)`
2.  **Composite Tracks**: Multi-dimensional display matrix (matrix of checkboxes).
    *   CLI: `--subgroup-by col1 --subgroup-by col2`
    *   API: `.group_by("col1", "col2")`
3.  **Overlay Tracks**: Combines multiple signals into a single plot (e.g., multi-wiggle).
    *   CLI: `--overlay-by column_name`
    *   API: `.overlay_by("column_name")`

### Example Metadata Tables

Below are examples of how to structure your metadata file (e.g., `tracks.csv`) for different hub layouts.

#### 1. A Basic Composite Track (Matrix Display)
To create a matrix of checkboxes where columns are **Cell Type** and rows are **Assay**:
*   **Command**: `tracknado create --metadata tracks.csv --subgroup-by cell_type --subgroup-by assay`

| fn | cell_type | assay | name |
| :--- | :--- | :--- | :--- |
| tracks/k562_ctcf.bw | K562 | CTCF | K562 CTCF Signal |
| tracks/gm12878_ctcf.bw | GM12878 | CTCF | GM12878 CTCF Signal |
| tracks/k562_h3k27ac.bw | K562 | H3K27ac | K562 H3K27ac Signal |

#### 2. Grouping with SuperTracks (Folders)
To group different types of data (Signals vs. Regions) into high-level containers:
*   **Command**: `tracknado create --metadata tracks.csv --supergroup-by category`

| fn | category | name |
| :--- | :--- | :--- |
| tracks/chip_signal.bw | Signal | ChIP-seq Signal |
| tracks/peaks.bb | Regions | Called Peaks |
| tracks/genes.gtf | Regions | Gene Annotations |

#### 3. Combined Layout (Folders + Matrix)
You can combine these strategies for complex hubs. This will create folders for each **Assay**, and within those, a matrix for **Sample** and **Condition**.
*   **Command**: `tracknado create --metadata tracks.csv --supergroup-by assay --subgroup-by sample --subgroup-by condition`

| fn | assay | sample | condition | name |
| :--- | :--- | :--- | :--- | :--- |
| data/s1_wt.bw | RNA-seq | S1 | WT | RNA S1 WT |
| data/s1_ko.bw | RNA-seq | S1 | KO | RNA S1 KO |
| data/atp_s1.bw | ATAC-seq | S1 | WT | ATAC S1 WT |

## Track Conversion

TrackNado automatically converts common formats to UCSC-compatible indexed files if the `--convert` flag is set.

*   **BED to BigBed**: Automatically sorts and converts BED files.
*   **GTF/GFF to BigGenePred**: Converts gene annotations to the `bigGenePred` format, allowing for codon and amino acid display when zoomed in.

### Configuration
Conversion requires a `chrom.sizes` file:

```bash
tracknado create -i data/*.gtf -o gene_hub --convert --chrom-sizes hg38.chrom.sizes
```

TrackNado attempts to find UCSC tools (`bedToBigBed`, `gtfToGenePred`, etc.) in your `$PATH`. If not found, it will automatically pull and run them via **Docker** or **Apptainer**.

## Custom Genomes (Assembly Hubs)

If you are working with a non-standard genome or a private assembly, TrackNado can generate an **Assembly Hub**.

```bash
tracknado create \
  -i tracks/*.bw \
  -o custom_hub \
  --custom-genome \
  --genome-name MySeq \
  --twobit reference.2bit \
  --organism "Mouse"
```

## Merging Hubs

You can merge multiple TrackNado configurations into a single "Master" hub.

```bash
# Merge two existing project configurations
tracknado merge project_a/tracknado_config.json project_b/tracknado_config.json -o master_hub
```

## Validation

Always validate your hub before hosting it:

```bash
tracknado validate ./my_hub/hub.txt
```

This uses the UCSC `hubCheck` tool if available, or falls back to a structural validator.
