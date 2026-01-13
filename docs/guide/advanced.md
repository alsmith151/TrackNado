# Advanced Features

## Custom Genomes (Assembly Hubs)

If you are working with a non-standard genome or a private assembly, TrackNado can generate an **Assembly Hub**.

```bash
tracknado create \
  -i tracks/*.bw \
  -o custom_hub \
  --custom-genome \
  --genome-name MySeq \
  --twobit reference.2bit \
  --organism "Mouse"
```

## Merging Hubs

You can merge multiple TrackNado configurations into a single "Master" hub. This is useful when different teams are working on different parts of a project.

```bash
# Merge two existing project configurations
tracknado merge project_a/tracknado_config.json project_b/tracknado_config.json -o merged_hub
```

## Validation

Always validate your hub before hosting it. TrackNado includes a built-in structural validator and support for the official UCSC `hubCheck`.

```bash
tracknado validate ./my_hub/hub.txt
```
