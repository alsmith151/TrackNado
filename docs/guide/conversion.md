# Track Conversion

TrackNado automatically converts common formats to UCSC-compatible indexed files if the conversion flag is set.

## Supported Formats

*   **BED to BigBed**: Automatically sorts and converts BED files.
*   **GTF/GFF to BigGenePred**: Converts gene annotations to the `bigGenePred` format, allowing for codon and amino acid display when zoomed in.

## Usage

### CLI
```bash
tracknado create -i data/*.gtf -o gene_hub --convert --chrom-sizes hg38.chrom.sizes
```

### API
```python
builder.with_convert_files().with_chrom_sizes("hg38.chrom.sizes")
```

## Backend Requirements

TrackNado attempts to find UCSC tools (`bedToBigBed`, `gtfToGenePred`, etc.) in your `$PATH`. If not found, it will automatically pull and run them via **Docker** or **Apptainer**.
