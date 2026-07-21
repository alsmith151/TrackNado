# Mixed inputs and merged builders

This script is an implementation-oriented test case rather than a template for production data. It demonstrates two ways of adding metadata—extracting it from paths and supplying a pandas DataFrame—then merges the resulting builders.

It also includes a BED-to-bigBed conversion path, but replaces the actual converter with a mock so the demonstration can run without UCSC tools. Do not use the generated dummy files as a browser-ready hub.

For a real build, use valid bigWig/bigBed data or enable normal conversion with a matching chromosome-sizes file. BAM files must have a same-named `.bai` index beside them.

[View the source](https://github.com/alsmith151/TrackNado/blob/main/examples/complex_edge_cases.py)
