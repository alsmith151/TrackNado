# Snakemake workflow step

This example is a Python script intended to run inside a Snakemake rule. It reads paths and hub settings from `snakemake.input`, `snakemake.output`, and `snakemake.params`, then stages the hub into the parent directory of the requested output.

It uses `from_seqnado_path` to derive metadata from a seqnado-style directory layout. The fields named in `supergroup_by`, `subgroup_by`, `overlay_by`, and `color_by` must therefore be present in that extracted metadata.

When adapting it, define the output hub path, input track files, contact email, genome, and grouping parameters explicitly in the Snakemake rule. Run the script once on a small set of tracks and validate the staged directory before incorporating it into a larger workflow.

[View the source](https://github.com/alsmith151/TrackNado/blob/main/examples/seqnado_make_hub.py)
