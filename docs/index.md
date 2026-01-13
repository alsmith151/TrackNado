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

Explore the documentation to get started:

-   **[Getting Started](guide/getting-started.md)**: Installation and quick start guides for CLI and API.
-   **[Metadata Management](guide/metadata.md)**: Learn how to handle track metadata effectively.
-   **[Organizing Tracks](guide/organization.md)**: Deep dive into SuperTracks, CompositeTracks, and overlays.
-   **[API Reference](reference/api.md)**: Full library documentation.
-   **[Examples](examples/overview.md)**: Real-world scripts for common workflows.
