# Complex Edge Cases

Demonstrates merging multiple hubs, handling mixed file types, and reconciling different grouping strategies.

Key features:

- Merging disparate track designs.
- Handling overlapping chromosome names.
- Mixed data types (BAM + BigWig + BigBed). Note: each `.bam` needs a same-named `.bai` index next to it (`sample.bam` -> `sample.bam.bai`, e.g. via `samtools index`) — TrackNado errors clearly at build time if it's missing.

[View full source code on GitHub](https://github.com/alsmith151/TrackNado/blob/main/examples/complex_edge_cases.py)
