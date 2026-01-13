# Organizing Your Hub

TrackNado supports three main types of track organization, mapping directly to UCSC Genome Browser concepts.

## 1. SuperTracks (Folders)

Top-level containers that group tracks together. These appear as folders in the track selection area.

*   **CLI**: `--supergroup-by column_name`
*   **API**: `.group_by("column_name", as_supertrack=True)`

## 2. Composite Tracks (Matrices)

A multi-dimensional display matrix (matrix of checkboxes). This is the most powerful way to organize large numbers of tracks.

*   **CLI**: `--subgroup-by col1 --subgroup-by col2`
*   **API**: `.group_by("col1", "col2")`

## 3. Overlay Tracks (Signals)

Combines multiple signals into a single plot (e.g., multi-wiggle).

*   **CLI**: `--overlay-by column_name`
*   **API**: `.overlay_by("column_name")`

---

## Example Metadata Table Structures

Below are examples of how to structure your metadata file (e.g., `tracks.csv`) for different hub layouts.

### Basic Composite Track (Matrix Display)

To create a matrix of checkboxes where columns are **Cell Type** and rows are **Assay**:

| fn | cell_type | assay | name |
| :--- | :--- | :--- | :--- |
| tracks/k562_ctcf.bw | K562 | CTCF | K562 CTCF Signal |
| tracks/gm12878_ctcf.bw | GM12878 | CTCF | GM12878 CTCF Signal |
| tracks/k562_h3k27ac.bw | K562 | H3K27ac | K562 H3K27ac Signal |

### Grouping with SuperTracks (Folders)

To group different types of data (Signals vs. Regions) into high-level containers:

| fn | category | name |
| :--- | :--- | :--- |
| tracks/chip_signal.bw | Signal | ChIP-seq Signal |
| tracks/peaks.bb | Regions | Called Peaks |
| tracks/genes.gtf | Regions | Gene Annotations |

### Combined Layout (Folders + Matrix)

You can combine these strategies for complex hubs. This will create folders for each **Assay**, and within those, a matrix for **Sample** and **Condition**.

| fn | assay | sample | condition | name |
| :--- | :--- | :--- | :--- | :--- |
| data/s1_wt.bw | RNA-seq | S1 | WT | RNA S1 WT |
| data/s1_ko.bw | RNA-seq | S1 | KO | RNA S1 KO |
| data/atp_s1.bw | ATAC-seq | S1 | WT | ATAC S1 WT |
