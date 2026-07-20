# CLI Reference

TrackNado provides a powerful command-line interface for common tasks.

## `tracknado create`

The main command for generating hubs.

### Arguments

- `-i, --input-files <PATHS>`: Paths to track files (BigWig, BAM, BED, GTF, etc.). Repeat the option for multiple inputs.
- `-m, --metadata <CSV/TSV>`: Path to metadata table.
- `-o, --output <DIR>`: Output directory for the hub.

### Flags

- `--template`: Generate a metadata template based on input files.
- `--seqnado`: Extract metadata from a seqnado-style directory layout.
- `--grouping-regex`: Extract grouping metadata from file names using named regex groups.
- `--hub-name`: Set the hub short label.
- `--hub-email`: Set the contact email written into the hub.
- `--genome-name`: Set the genome assembly name.
- `--supergroup-by`: Group tracks into top-level SuperTracks.
- `--subgroup-by`: Group tracks into CompositeTrack dimensions.
- `--overlay-by`: Group tracks into OverlayTracks.
- `--color-by`: Choose a metadata column for color assignment.
- `--convert`: Automatically convert files to UCSC formats.
- `--chrom-sizes`: Required when using `--convert`.
- `--custom-genome`: Generate an assembly hub.
- `--twobit`: Required for custom genomes.
- `--organism`: Required for custom genomes.
- `--default-pos`: Set the default viewing position for custom genomes.
- `--description`: Path to an HTML landing page for the hub.
- `--sort-metadata`: Sort metadata columns alphabetically.
- `--remove-existing`: Remove any existing hub directory before staging.
- `--url-prefix`: Base URL used when reporting the final hub URL.

## `tracknado merge`

Combines multiple `tracknado_config.json` files into a single hub.

- `--hub-name`, `--genome-name`, and `--hub-email` control the merged hub metadata.
- `--sort-metadata` and `--remove-existing` mirror the create command behavior.

## `tracknado validate`

Validates a hub directory or `hub.txt` file.

- `--strict`: Treat warnings as errors.
