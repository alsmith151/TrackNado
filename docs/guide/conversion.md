# File conversion

UCSC track hubs work best with indexed formats such as bigWig and bigBed. TrackNado can convert BED files to bigBed and GTF/GFF files to bigGenePred while it builds the hub.

## Convert during a build

Provide `--convert` and a chromosome-sizes file for the target assembly:

```bash
tracknado create \
  -i annotations/genes.gtf \
  -i peaks/regions.bed \
  --output my_hub \
  --genome-name hg38 \
  --convert \
  --chrom-sizes hg38.chrom.sizes
```

The chromosome sizes must match the genome assembly and the chromosome names in your input. A mismatch is a common cause of conversion or display failures.

Converted files are written under `my_hub/converted` before staging. The original source files are not changed.

The same configuration in Python is:

```python
builder.with_convert_files().with_chrom_sizes("hg38.chrom.sizes")
```

## Tool requirements

TrackNado looks for the UCSC conversion programs, including `bedToBigBed` and `gtfToGenePred`, on `PATH`. If they are unavailable, it can run them through Docker or Apptainer. Make sure one of these routes is available before running a large conversion job.

## Formats that need preparation

- **bigWig and bigBed** can be included directly.
- **BED** is converted to bigBed with `--convert`.
- **GTF/GFF** is converted to bigGenePred with `--convert`.
- **BAM** needs a same-named `.bai` index next to it, for example `sample.bam.bai`. TrackNado stops early with a clear error if it cannot find the index.

For repeatable production hubs, consider converting and validating data in your analysis workflow, then give TrackNado the finished UCSC-ready files.
