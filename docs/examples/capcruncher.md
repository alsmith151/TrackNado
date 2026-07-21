# CapCruncher-style metadata

This example shows a custom metadata extractor for filenames shaped like:

```text
sample.method.viewpoint.bigWig
```

The extractor returns fields such as `samplename`, `method`, and `viewpoint`. The builder then uses those fields as composite-track dimensions and puts derived track categories into supertracks.

This is useful when a project has a stable naming convention that the built-in extractors do not cover. Treat the regular expression as part of the project configuration: test it against a few representative paths before processing a whole result directory.

The example creates placeholder files to demonstrate the metadata logic. It prepares a `HubBuilder` and calls `build()` but does not call `stage_hub()`, so add that call when adapting the pattern to real data.

[View the source](https://github.com/alsmith151/TrackNado/blob/main/examples/capcruncher_hub.py)
