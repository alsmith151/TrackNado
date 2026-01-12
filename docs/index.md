# TrackNado 🌪️

**TrackNado** is a high-level library and CLI tool designed to quickly generate UCSC Genome Browser track hubs from sequencing data.

## Features

-   **Fluent API**: Declarative hub construction.
-   **Auto-Conversion**: Implicitly handle BED, GTF, and GFF files.
-   **Smart Merging**: Combine multiple projects with one command.
-   **Validation**: Built-in support for `hubCheck`.

## 🚀 Quick Start

### Installation

```bash
pip install tracknado
```

### Basic Usage

```python
import tracknado as tn

hub = (
    tn.HubBuilder()
    .add_tracks(['sample1.bw', 'sample2.bw'])
    .group_by('method')
    .build(name='my_hub', genome='hg38', outdir='out/')
)
hub.stage_hub()
```

## 📖 Documentation Sections

Use the navigation bar at the top or the links below to explore:

-   **[User Guide](guide.md)**: Detailed instructions on metadata, groupings, and conversion.
-   **[Examples](examples.md)**: Real-world scripts for CapCruncher and Snakemake.
-   **[API Reference](api.md)**: Full library documentation.
