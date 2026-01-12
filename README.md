# TrackNado 🌪️

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://alsmith151.github.io/TrackNado/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

TrackNado is a powerful Python library and CLI tool designed to quickly generate UCSC Genome Browser track hubs from sequencing data. It features a fluent API, robust metadata extraction, and smart hub merging.

## Key Features

- **Fluent API**: Builder pattern for intuitive hub construction.
- **Type Safety**: Powered by Pydantic and Pandera for robust validation.
- **Smart Merging**: Merge hubs with automatic reconciliation of groupings and colors.
- **Auto-Extraction**: Built-in extractors for complex directory structures (e.g., seqnado).
- **Local Validation**: Built-in support for UCSC `hubCheck`.
- **Modern Docs**: Comprehensive documentation built with MkDocs.

## Installation

```bash
pip install tracknado
```

To include documentation building dependencies:
```bash
pip install "tracknado[docs]"
```

## Quick Start (Python API)

```python
import tracknado as tn

# Build a hub with a few lines of code
hub = (
    tn.HubBuilder()
    .add_tracks(['data/sample1.bw', 'data/sample2.bw'])
    .with_metadata_extractor(tn.from_seqnado_path)
    .group_by('method', as_supertrack=True)
    .color_by('samplename')
    .build(
        name='MyHub',
        genome='hg38',
        outdir='hubs/my_hub/',
        hub_email='your@email.com'
    )
)

# Stage the hub files
hub.stage_hub()
```

## Quick Start (CLI)

### Create a Hub
```bash
tracknado create -i data/*.bw -o my_hub --hub-name "My Hub" --genome-name hg38 --seqnado
```

### Merge Hubs
TrackNado automatically saves a `tracknado_config.json` sidecar. Use it to merge hubs:
```bash
tracknado merge -i hub1/tracknado_config.json hub2/tracknado_config.json -o merged_hub
```

### Validate a Hub
```bash
tracknado validate my_hub/
```

## Documentation

For detailed usage guides and API reference, visit our documentation:
[https://alsmith151.github.io/TrackNado/](https://alsmith151.github.io/TrackNado/)

## License

TrackNado is released under the [GNU General Public License v3](LICENSE).
