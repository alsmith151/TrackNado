# Advanced use

## Custom assemblies

Use an assembly hub when the genome is not one of UCSC's built-in assemblies. You need a `.2bit` sequence file, an organism name, and a sensible default browser position.

```bash
tracknado create \
  -i tracks/*.bw \
  --output custom_hub \
  --hub-name project_assembly \
  --genome-name project_v1 \
  --hub-email you@example.org \
  --custom-genome \
  --twobit reference/project_v1.2bit \
  --organism "Example species" \
  --default-pos chr1:10000-20000
```

The genome names in your track files must match the sequence names in the `.2bit` file. Test an assembly hub with a small set of tracks before staging the complete project.

The equivalent Python configuration is:

```python
builder.with_custom_genome(
    name="project_assembly",
    twobit_file="reference/project_v1.2bit",
    organism="Example species",
    default_position="chr1:10000-20000",
)
```

## Merge prepared builds

Every build writes `tracknado_config.json` alongside the staged hub. Merge those configuration files when several teams or workflow steps produce parts of the same hub:

```bash
tracknado merge \
  project_a/tracknado_config.json \
  project_b/tracknado_config.json \
  --output combined_hub \
  --hub-name combined_project \
  --genome-name hg38 \
  --hub-email you@example.org
```

The merged input should describe compatible tracks for the same assembly. Validate the resulting `combined_hub` before publishing it.

## Make builds repeatable

Keep the following under version control where practical:

- the metadata CSV/TSV;
- the command or workflow rule that runs TrackNado;
- any chromosome-sizes and custom-assembly inputs; and
- a small HTML description file, if you pass one with `--description`.

Use `--remove-existing` only when the output directory is dedicated to that build. It removes the existing output directory before staging the replacement hub.

## Validate locally, then publish

```bash
tracknado validate combined_hub --strict
```

`--strict` treats warnings as errors. Validation cannot prove that an arbitrary web server will expose every file correctly, so after publishing, load the public `.hub.txt` URL in UCSC as a final check.
