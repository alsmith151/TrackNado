# Metadata

TrackNado uses a table to turn files into well-labelled browser tracks. Each row describes one file. Columns are ordinary metadata fields that you can reuse for labels, colours, and layout.

## Required and useful columns

`file_path` is the only required column. It contains a path to the input file. TrackNado accepts both CSV and TSV files and detects the delimiter automatically.

| Column | Purpose |
| --- | --- |
| `file_path` | Required path to the data file. |
| `name` | Optional label shown in UCSC. Defaults to the file stem. |
| `ext` | Optional track type, such as `bigWig`, `bigBed`, or `bam`. Usually filled by `tracknado design`. |
| `color` | Optional colour. Use a name such as `steelblue`, a hex value such as `#4682B4`, or `R,G,B`. |
| other columns | Your fields, such as `assay`, `cell_type`, `condition`, and `replicate`. Use them with the grouping and colour options. |

For example:

```csv
file_path,name,ext,assay,cell_type,condition,replicate,color
tracks/k562_ctcf_r1.bw,K562 CTCF rep 1,bigWig,ChIP-seq,K562,untreated,1,crimson
tracks/k562_ctcf_r2.bw,K562 CTCF rep 2,bigWig,ChIP-seq,K562,untreated,2,crimson
tracks/gm12878_ctcf_r1.bw,GM12878 CTCF rep 1,bigWig,ChIP-seq,GM12878,untreated,1,#4169E1
tracks/peaks.bb,Called peaks,bigBed,Peaks,All,,,#464646
```

Generate a starter table instead of typing paths by hand:

```bash
tracknado design -i tracks/*.bw -i tracks/*.bb -o tracks.csv
```

`tracknado create --template tracks.csv` creates a header-only table when that is more convenient.

## Use columns when building

Pass the names of your columns—not fixed special names—to the build command:

```bash
tracknado create \
  --metadata tracks.csv \
  --output my_hub \
  --genome-name hg38 \
  --supergroup-by assay \
  --subgroup-by cell_type \
  --subgroup-by condition \
  --color-by cell_type
```

This makes one top-level group per assay and a cell-type-by-condition composite display within it. `--color-by` assigns a palette from categories. To use the explicit values in the `color` column instead, omit `--color-by`.

The `color` column accepts named colours (for example `steelblue`), six- or three-digit hex values (`#4682B4` or `#48B`), CSS `rgb(70, 130, 180)`, and the original comma-separated RGB form (`70,130,180`). TrackNado converts these to the RGB values UCSC requires.

See [Organising tracks](organization.md) for guidance on when to use each layout option.

## Derive metadata from paths

If your naming convention is consistent, TrackNado can populate fields before you edit the table. A regular expression must use named capture groups:

```bash
tracknado design \
  -i tracks/*.bw \
  -o tracks.csv \
  --grouping-regex '(?P<cell_type>[^_]+)_(?P<assay>[^_]+)'
```

The command adds `cell_type` and `assay` columns from names such as `K562_CTCF.bw`. Check the resulting rows before building: filenames are convenient input, but a metadata table is the final source of truth.

For seqnado-style directory structures, use `--seqnado` instead. The equivalent Python methods are `.with_grouping_regex(...)` and `.with_metadata_extractor(tn.from_seqnado_path)`.

## Missing group values

Blank values are acceptable if those tracks should not participate in a particular group. If every track needs a value in an active grouping field, fill the blanks in the CSV or use the Python API:

```python
builder.with_missing_groups("Other", "condition")
```

This replaces empty `condition` values with `Other` before the hub is generated.
