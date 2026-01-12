# User Guide

This guide explains how to use TrackNado's advanced features.

## Metadata Extraction

TrackNado can automatically extract metadata from your file paths.

```python
from tracknado import HubBuilder, from_seqnado_path

hub = HubBuilder().add_tracks(files).with_metadata_extractor(from_seqnado_path)
```

## Grouping and Coloring

You can group your tracks into supertracks, composites, or overlays.

```python
hub.group_by("assay", as_supertrack=True)
hub.group_by("method")
hub.color_by("samplename")
hub.overlay_by("samplename")
```

## Validation

You can validate your hub locally before uploading it.

```python
from tracknado import validate_hub
is_valid, message = validate_hub("my_hub/hub.txt")
```
