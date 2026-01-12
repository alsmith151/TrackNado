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

## 📖 Useful Links

-   [User Guide](guide.md): Learn about grouping, coloring, and custom genomes.
-   [Examples](examples.md): See real-world usage scenarios.
-   [API Reference](api.md): Detailed documentation of all classes and functions.
