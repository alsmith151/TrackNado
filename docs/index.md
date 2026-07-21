# TrackNado

TrackNado creates UCSC Genome Browser track hubs from local genomic data files. It stages the hub configuration and track files in a directory you can publish on a web server.

The most reliable workflow is simple:

1. Start with files that UCSC can display, such as bigWig and bigBed.
2. Put one file per row in a metadata table.
3. Choose the metadata columns that should organise the browser view.
4. Build, validate, and publish the resulting directory.

## Start here

The [Getting started guide](guide/getting-started.md) walks through a complete hub with the command line. It is the recommended first read, even if you eventually build hubs from Python.

## What TrackNado does

- stages a standard UCSC hub directory from your tracks;
- reads track labels and grouping information from CSV or TSV metadata;
- can derive metadata from file paths or a regular expression;
- creates supertracks, composite tracks, and overlays from metadata columns;
- converts BED and GTF/GFF inputs when UCSC conversion tools and chromosome sizes are available;
- validates a staged hub before you publish it.

TrackNado does not upload the hub or host it for you. After staging, place the output directory somewhere reachable over HTTP(S), and use the URL ending in `.hub.txt` in the UCSC Genome Browser.

## Guides

- [Getting started](guide/getting-started.md) — build and validate your first hub.
- [Metadata](guide/metadata.md) — design the table that drives labels, colours, and groups.
- [Organising tracks](guide/organization.md) — choose between folders, matrices, and overlays.
- [File conversion](guide/conversion.md) — use BED and annotation files safely.
- [Advanced use](guide/advanced.md) — custom assemblies, merging, and repeatable builds.
