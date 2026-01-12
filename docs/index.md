# TrackNado

Simple command line tool and Python library to quickly generate UCSC track hubs from sequencing data.

## Installation

```bash
pip install tracknado
```

## Quick Start

TrackNado can be used from the command line or from Python.

### CLI

```bash
tracknado create -i data/*.bigWig -o my_hub --hub-name "My Hub" --genome-name hg38
```

### Python API

```python
import tracknado as tn

hub = (
    tn.HubBuilder()
    .add_tracks(['sample1.bw', 'sample2.bw'])
    .group_by('method')
    .build(name='my_hub', genome='hg38', outdir='out/')
)
```
