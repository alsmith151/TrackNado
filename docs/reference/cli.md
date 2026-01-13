# CLI Reference

TrackNado provides a powerful command-line interface for common tasks.

## `tracknado create`

The main command for generating hubs.

### Arguments

- `-i, --input <PATHS>`: Paths to track files (BigWig, BAM, BED, GTF, etc.).
- `-m, --metadata <CSV/TSV>`: Path to metadata table.
- `-o, --output <DIR>`: Output directory for the hub.

### Flags

- `--template`: Generate a metadata template based on input files.
- `--convert`: Automatically convert files to UCSC formats.
- `--custom-genome`: Generate an assembly hub.

## `tracknado merge`

Combines multiple `tracknado_config.json` files into a single hub.

## `tracknado validate`

Validates a hub directory or `hub.txt` file.
