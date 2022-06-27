import click
from .make_hub import get_file_attributes, make_hub
import pandas as pd


def categorise_capcruncher_tracks(df_file_attributes: pd.DataFrame):
    mapping = {
        "raw": "Replicates",
        "normalised": "ReplicatesScaled",
        "summary": "SamplesSummarised",
        "subtraction": "SamplesCompared",
    }

    return [
        mapping[k]
        for _, method in df_file_attributes["method"].iteritems()
        for k in mapping
        if k in method
    ]


def get_ngs_pipeline_attributes(df_file_attributes: pd.DataFrame):

    chipseq_pattern = r"(?P<samplename>.*?)_(?P<antibody>.*)_(?:.*).(bigWig|bed|bigBed)"
    generic_pattern = r"(?P<samplename>.*?).(bigWig|bed|bigBed)"
    attributes = df_file_attributes["basename"].str.extract(chipseq_pattern)

    if attributes["samplename"].dropna().shape[0]:
        attributes = df_file_attributes["basename"].str.extract(
            generic_pattern)

    return attributes


@click.command()
@click.argument("files", nargs=-1)
@click.option("-o", "--output", help="Output hub directory name", default="HUB/")
@click.option(
    "-d",
    "--details",
    help="Extra details for each file. MUST contain: filename and samplename columns",
)
@click.option("-g", "--group-by", help="Column in the provided details to group tracks")
@click.option("--description-html", help="Path to HTML file with hub description")
@click.option(
    "-m",
    "--mode",
    help="Presets for CapCruncher and NGS-Pipeline files",
    type=click.Choice(["capcruncher", "ngs-pipeline", "custom"]),
    default="custom",
)
@click.option(
    "-t",
    "--generic-tracks",
    help="Ungrouped tracks to add to the hub",
    multiple=True,
)
@click.option(
    "--hub-name",
    help="Name of hub to generate",
    default="HUB",
)
@click.option(
    "--hub-email",
    help="Email address for hub",
    default="alastair.smith@ndcls.ox.ac.uk",
)
@click.option(
    "--genome-name",
    help="Name of genome",
    default="hg19",
)
def create_hub(files, **kwargs):

    if kwargs["mode"] == "capcruncher":
        df = get_file_attributes(files)
        attributes = df["basename"].str.extract(
            r"(?P<samplename>.*?)\.(?P<method>.*?)\.(?P<viewpoint>.*?)\.(?P<file_type>.*)"
        )

        df_details = pd.concat(
            [df.rename(columns={"basename": "filename"})
             ["filename"], attributes],
            axis=1,
        ).set_index("filename")


        df_details["track_category"] = categorise_capcruncher_tracks(df_details)
        df_details = df_details.drop(columns=["file_type", "method"])

        make_hub(
            files=files,
            details=df_details,
            group_by="track_category",
            **{k:v for k,v in kwargs.items() if not k in ["files", "details", "group_by"]}
        )

    elif kwargs["mode"] == "ngs-pipeline":
        df = get_file_attributes(files)
        attributes = get_ngs_pipeline_attributes(df)
        df_details = pd.concat(
            [df.rename(columns={"basename": "filename"})
             ["filename"], attributes],
            axis=1,
        ).set_index("filename")

        make_hub(
            files=files,
            output=kwargs["output"],
            details=df_details,
            group_by="antibody" if "antibody" in df_details.columns else "samplename",
            **kwargs
        )

    else:
        make_hub(files, **kwargs)
