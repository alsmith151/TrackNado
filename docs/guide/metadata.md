# Track Metadata

TrackNado centers around a **Track Design**—a table where each row is a track and columns represent metadata (sample name, assay, coloring, etc.).

## Positional Metadata

You can provide metadata via a CSV/TSV file using the `--metadata` flag. This file **must** include a `fn` column containing the paths to your track files.

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
