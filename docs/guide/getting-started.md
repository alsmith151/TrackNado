# Getting Started

TrackNado is designed to be easy to use whether you prefer the command line or a Python API.

## Installation

```bash
pip install tracknado
```

## Quick Start (CLI)

The easiest way to get started is by using the `create` command.

```bash
# Generate a metadata template
tracknado create --template tracks.csv

# After filling out tracks.csv with your file paths and metadata
tracknado create --metadata tracks.csv --output my_hub --genome-name hg38
```

## Quick Start (Python API)

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
