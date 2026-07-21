# Command-line reference

Run `tracknado --help` or `tracknado <command> --help` to see the options installed with your version.

## `tracknado design`

Create an editable CSV from track files. It writes one row per input with `file_path`, `name`, and `ext`, plus empty `color`, `supertrack`, `composite`, and `overlay` columns.

```bash
tracknado design -i tracks/*.bw -o tracks.csv
```

| Option | Meaning |
| --- | --- |
| `-i`, `--input-files` | One or more track files. Repeat the option to add another set. |
| `-o`, `--output` | CSV or TSV path to write. |
| `--seqnado` | Extract fields from a seqnado-style directory layout. |
| `--grouping-regex` | Extract named groups from file names. |

## `tracknado create`

Build and stage a hub from either a metadata table or input files.

```bash
tracknado create --metadata tracks.csv --output my_hub --genome-name hg38
```

| Option | Meaning |
| --- | --- |
| `-i`, `--input-files` | Track files to include. Use this instead of `--metadata` when no table is needed. |
| `-m`, `--metadata` | CSV or TSV with a `file_path` column. |
| `-o`, `--output` | Staged hub directory. Required unless creating a template. |
| `-t`, `--template` | Write a header-only metadata template and exit. |
| `--hub-name` | Short hub identifier; used in the `.hub.txt` filename. |
| `--hub-email` | Contact email stored in the hub. |
| `--genome-name` | Genome assembly identifier, such as `hg38` or `mm10`. |
| `--supergroup-by` | Metadata field(s) for top-level supertracks. |
| `--subgroup-by` | Metadata field(s) for composite-track dimensions. |
| `--overlay-by` | Metadata field(s) for overlay tracks. |
| `--color-by` | Metadata field used to assign colours. |
| `--seqnado` | Extract metadata from a seqnado-style path. |
| `--grouping-regex` | Extract named metadata fields from file names. |
| `--convert` | Convert BED and GTF/GFF inputs to UCSC formats. |
| `--chrom-sizes` | Required alongside `--convert`; sizes for the target assembly. |
| `--custom-genome` | Build an assembly hub. Requires `--twobit` and `--organism`. |
| `--twobit` | Sequence file for a custom assembly. |
| `--organism` | Common organism name for a custom assembly. |
| `--default-pos` | Initial custom-assembly browser position. |
| `--description` | HTML file to include as the hub landing page. |
| `--sort-metadata` | Sort non-standard metadata columns in the saved configuration. |
| `--remove-existing` | Remove the existing output directory before staging. |
| `--hosting` | Name of a user-defined TOML hosting profile used to report the public hub URL. |
| `--hosting-config` | Optional path to the TOML hosting-profile file. Defaults to `~/.config/tracknado/hosting.toml` (or `$XDG_CONFIG_HOME/tracknado/hosting.toml`). |

## `tracknado merge`

Create one hub from the `tracknado_config.json` files produced by earlier builds:

```bash
tracknado merge a/tracknado_config.json b/tracknado_config.json --output merged_hub
```

Use `--hub-name`, `--genome-name`, and `--hub-email` to set the merged hub metadata. `--sort-metadata` and `--remove-existing` have the same meaning as for `create`.

## `tracknado validate`

Check a staged hub directory or a `.hub.txt` file:

```bash
tracknado validate my_hub --strict
```

`--strict` treats warnings as errors.
