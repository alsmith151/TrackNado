# Organising tracks

Choose a layout based on how someone will browse the data. TrackNado maps metadata columns to three UCSC structures: supertracks, composite tracks, and overlays. You can use more than one, but start with the smallest structure that makes the hub easy to scan.

## Supertracks: broad sections

A supertrack creates a top-level section in the track controls. Use it for genuinely different families of data, such as signal, peaks, and annotation.

```bash
tracknado create --metadata tracks.csv --output my_hub \
  --genome-name hg38 --supergroup-by data_type
```

| file_path | name | data_type |
| --- | --- | --- |
| `tracks/ctcf.bw` | CTCF signal | Signal |
| `tracks/peaks.bb` | CTCF peaks | Peaks |
| `tracks/genes.bb` | Genes | Annotation |

In Python, use `.group_by("data_type", as_supertrack=True)`.

## Composite tracks: compare combinations

A composite track provides selectors for combinations of metadata fields. It is useful for a regular experimental design, for example multiple assays across cell types and conditions.

```bash
tracknado create --metadata tracks.csv --output my_hub \
  --genome-name hg38 \
  --subgroup-by cell_type \
  --subgroup-by assay
```

| file_path | cell_type | assay |
| --- | --- | --- |
| `tracks/k562_ctcf.bw` | K562 | CTCF |
| `tracks/gm12878_ctcf.bw` | GM12878 | CTCF |
| `tracks/k562_h3k27ac.bw` | K562 | H3K27ac |

Use columns whose values are short, stable, and meaningful to a reader. A column with a unique value for every file is rarely a helpful composite dimension.

In Python, use `.group_by("cell_type", "assay")`.

## Overlays: display related signals together

An overlay combines related tracks in a multi-signal display. Use it for tracks users will usually compare at the same genomic location, such as conditions for a sample.

```bash
tracknado create --metadata tracks.csv --output my_hub \
  --genome-name hg38 --overlay-by condition
```

| file_path | sample | condition |
| --- | --- | --- |
| `tracks/s1_control.bw` | S1 | Control |
| `tracks/s1_treated.bw` | S1 | Treated |

In Python, use `.overlay_by("condition")`.

## A practical pattern

For a larger project, use a supertrack for the broad data family, a composite track for the experimental design, and an overlay only where viewing signals together is useful:

```bash
tracknado create --metadata tracks.csv --output my_hub \
  --genome-name hg38 \
  --supergroup-by data_type \
  --subgroup-by cell_type \
  --subgroup-by assay \
  --overlay-by condition
```

Build a small subset first and inspect it in UCSC. A flat hub is often the clearest answer for only a few tracks.
