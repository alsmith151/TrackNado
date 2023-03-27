# UCSC Hub Maker

Simple command line tool to quickly generate a UCSC hub from a set of files.

## Installation
```bash
git clone https://github.com/alsmith151/ucsc_hub_maker.git
cd ucsc_hub_maker
pip install .
```

## Usage

See the help for more details on the options that can be provided.

```bash
make-ucsc-hub --help
```

## Example

### Minimal example

```bash
make-ucsc-hub \
--hub-name 270123_PM_MA4_BP \
--hub-email alastair.smith@ndcls.ox.ac.uk \
--genome-name hg38 \
-o /datashare/asmith/chipseq/270123_PM_MA4_BP \
bigwigs/deeptools/*.bigWig \ # Files to be added to the hub
peaks/lanceotron/*.bigBed # More files to be added to the hub
```

### Example when providing details for tracks

File details can be provided in a tab-separated file. The first line should be a header with the following columns: filename (full path to file) samplename (name for file; user defined).

Any other columns can be added and these can be used for more elaborate grouping or coloring of tracks.

```bash
make-ucsc-hub \
--hub-name 270123_PM_MA4_BP \
--hub-email
--genome-name hg38 \
-o /datashare/asmith/chipseq/270123_PM_MA4_BP \
--track-details track_details.txt \
--color-by antibody \
bigwigs/deeptools/*.bigWig \ # Files to be added to the hub
peaks/lanceotron/*.bigBed # More files to be added to the hub
```


