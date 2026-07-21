# TrackNado 🌪️

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://alsmith151.github.io/TrackNado/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

**TrackNado** is a powerful Python library and CLI tool designed to rapidly generate complex UCSC Genome Browser track hubs. It handles the "heavy lifting" of metadata extraction, multi-dimensional groupings, and automated file conversion, letting you focus on the science.

---

## 🚀 Key Features

-   **Fluent Python API**: A declarative `HubBuilder` for intuitive and reproducible hub construction.
-   **Shared Build Path**: The CLI and Python API use the same builder setup helper, so flags and method calls stay in sync.
-   **Automated Conversion**: Built-in, container-backed conversion for **BED → bigBed** and **GTF/GFF → bigGenePred** (with codon display).
-   **Custom Genomes (Assembly Hubs)**: Deep support for private assemblies with `.2bit` integration.
-   **Multi-Dimensional Grouping**: Seamlessly create SuperTracks, CompositeTracks (matrix display), and OverlayTracks.
-   **Universal Metadata**: Extract metadata from filenames, parent directories, or external CSV/TSV tables.
-   **Smart Merging**: Combine multiple projects into a single unified hub via sidecar JSON configurations.
-   **Type Safety**: Fully validated by Pydantic and Pandera.

---

## 📦 Installation

```bash
pip install tracknado
```

TrackNado will automatically attempt to use UCSC tools from your `$PATH`. If not found, it can automatically pull and run them via **Docker** or **Apptainer**.

---

## 🛠️ Quick Start (CLI)

The CLI is powered by Typer and uses the same builder pipeline as the Python API, so the options map directly to the fluent methods.

Use `--grouping-regex` when your grouping columns are encoded in the file name rather than a metadata table.

### 1. Generate a Metadata Table

Point `design` at your track files to auto-generate an editable metadata CSV, pre-filled with `fn`/`name`/`ext` (and anything `--seqnado`/`--grouping-regex` can extract) so you're not starting from scratch:

```bash
tracknado design -i data/*.bw -i data/*.bb -o tracks.csv
```

```csv
fn,name,ext,color,supertrack,composite,overlay
data/k562_ctcf.bw,k562_ctcf,bigWig,,,,
data/gm12878_ctcf.bw,gm12878_ctcf,bigWig,,,,
data/peaks.bb,peaks,bigBed,,,,
```

Fill in the blank columns by hand — e.g. `color` (`R,G,B`), `supertrack`/`composite`/`overlay` (for grouping) — and add any extra metadata columns you want:

```csv
fn,name,ext,color,supertrack,composite,overlay
data/k562_ctcf.bw,K562 CTCF,bigWig,"255,0,0",ChIP-seq,K562,CTCF
data/gm12878_ctcf.bw,GM12878 CTCF,bigWig,"0,0,255",ChIP-seq,GM12878,CTCF
data/peaks.bb,Called Peaks,bigBed,,Annotation,,
```

(Prefer a blank starting point instead? `tracknado create --template tracks.csv` writes just the header row.)

### 2. Create a Hub
```bash
tracknado create \
  --metadata tracks.csv \
  --output ./my_hub \
  --genome-name hg38 \
  --subgroup-by cell_type \
  --subgroup-by assay \
  --convert \
  --chrom-sizes hg38.chrom.sizes
```

### 3. Create a Custom Assembly Hub
```bash
tracknado create \
  -i tracks/*.bw \
  --output ./custom_hub \
  --custom-genome \
  --twobit reference.2bit \
  --organism "MySpecies"
```

---

## 🐍 Quick Start (Python API)

TrackNado’s fluent API makes complex hubs readable and maintainable.

```python
import tracknado as tn

# Build a multi-dimensional hub with one statement
builder = (
    tn.HubBuilder()
    .add_tracks(['data/peaks.bed', 'data/signal.bw'])
    .with_metadata_extractor(tn.from_seqnado_path)
    .group_by('assay', as_supertrack=True)  # Signal vs Peaks folders
    .group_by('cell_type', 'condition')     # Matrix display
    .color_by('condition', palette='hls')
    .with_convert_files()
    .with_chrom_sizes("hg38.chrom.sizes")
)

# Build and Stage
hub = builder.build(
    name="Scientific_Project",
    genome="hg38",
    outdir="hub_out/",
    hub_email="scientist@lab.edu",
    description_html="docs/project_summary.html"
)

hub.stage_hub()
```

---

## 🔍 Validation

Never host a broken hub again. TrackNado includes a built-in structural validator and support for the official UCSC `hubCheck`.

```bash
tracknado validate my_hub/
```

---

## 📖 Learn More

For full documentation, example metadata tables, and API references, visit:
👉 **[Documentation Portal](https://alsmith151.github.io/TrackNado/)**

## 📄 License

TrackNado is released under the [GNU General Public License v3](LICENSE).
