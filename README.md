# TrackNado

Simple command line tool to quickly generate a UCSC hub from a set of files.

## Installation
```bash
pip install tracknado
```

## Usage

See the help for more details on the options that can be provided.

```bash
tracknado --help
```

## Example

### Minimal example with no track details

```bash
tracknado \
create \ 
--hub-name HUB_NAME_HERE \
--hub-email EMAIL_ADDRESS \
--genome-name hg38 \
-o /datashare/asmith/ \
-i bigwigs/deeptools/*.bigWig peaks/lanceotron/*.bigBed
```

### Example with track details

```bash
tracknado \
create \
--hub-name HUB_NAME_HERE \
--hub-email EMAIL_ADDRESS \
--genome-name hg38 \
-o /datashare/asmith/ \
-d PATH_TO_TRACK_DETAILS_FILE \
```

### Example with a custom genome

```bash
tracknado \
create \
--hub-name HUB_NAME_HERE \
--hub-email EMAIL_ADDRESS \
--genome-name CUSTOM_GENOME_NAME \
--genome-organism CUSTOM_GENOME_ORGANISM \
--genome-two-bit-path PATH_TO_TWO_BIT_FILE \
-i bigwigs/deeptools/*.bigWig peaks/lanceotron/*.bigBed
-o /datashare/asmith/ \
```

## Merging hubs

It is possible to merge the outputs from tracknado create into a single hub by using the merge command. This requires that
hubs have been created with the --save-hub-design flag. This will create a file called hub_design.pkl in the output
directory. This file contains all the information required to recreate the hub. This does require that the hubs are for the same
genome.

First create a couple of example hubs as above:

```bash
tracknado \
create \
--hub-name HUB_NAME_HERE \
--hub-email EMAIL_ADDRESS \
--genome-name hg38 \
-o /datashare/asmith/path1 \
-i bigwigs/deeptools/*.bigWig peaks/lanceotron/*.bigBed \
--save-hub-design
```

```bash
tracknado \
create \
--hub-name HUB_NAME_HERE \
--hub-email EMAIL_ADDRESS \
--genome-name hg38 \
-o /datashare/asmith/path2 \
-i bigwigs/deeptools/*.bigWig peaks/lanceotron/*.bigBed \
--save-hub-design
```


Then merge them:

```bash
tracknado \
merge \
--hub-name HUB_NAME_HERE \
--hub-email EMAIL_ADDRESS \
--genome-name hg38 \
-o /datashare/asmith/merged \
-i /datashare/asmith/path1/hub_design.pkl /datashare/asmith/path2/hub_design.pkl
```

This will create a new hub in /datashare/asmith/merged that contains all the tracks from the two input hubs. 
You can also supply all of the standard arguments to the merge command to change the hub name, email, genome etc.







