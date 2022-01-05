import click
from .make_hub import get_file_attributes, make_hub
import pandas as pd


def categorise_capcruncher_tracks(df_file_attributes: pd.DataFrame):
    mapping = {
        "raw": "Replicates",
        "normalised": "ReplicatesScaled",
        "summary": "SamplesSummarised",
        "subtraction": "SamplesCompared",
        pd.NA: "Viewpoints",
    }

    return [
        mapping[k]
        for k in mapping
        for index, method in df_file_attributes["method"].iteritems()
        if k in method
    ]


def get_ngs_pipeline_attributes(df_file_attributes: pd.DataFrame):

    chipseq_pattern = r"(?P<samplename>.*?)_(?P<antibody>.*)_(?:.*).(bigWig|bed|bigBed)"
    generic_pattern = r"(?P<samplename>.*?).(bigWig|bed|bigBed)"
    attributes = df_file_attributes["basename"].str.extract(chipseq_pattern)

    if attributes["samplename"].dropna().shape[0]:
        attributes = df_file_attributes["basename"].str.extract(generic_pattern)

    return attributes


@click.command()
@click.argument("files")
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
    type=click.Choice(["capcruncher", "ngs-pipeline"]),
)
def create_hub(*args, **kwargs):

    if kwargs["mode"] == "capcruncher":
        df = get_file_attributes(args)
        attributes = df["basename"].str.extract(
            r"(?P<samplename>.*?)\.(?P<method>.*?)\.(?P<viewpoint>.*?)\.(?P<file_type>.*)"
        )
        df_details = pd.concat(
            [df.rename(columns={"basename": "filename"})["filename"], attributes],
            axis=1,
        ).set_index("filename")

        df_details["track_category"] = categorise_capcruncher_tracks(df_details)

        make_hub(
            files=args,
            output=kwargs["output"],
            details=df_details,
            group_by="track_category",
        )

    elif kwargs["mode"] == "ngs-pipeline":
        df = get_file_attributes(args)
        attributes = get_ngs_pipeline_attributes(df)
        df_details = pd.concat(
            [df.rename(columns={"basename": "filename"})["filename"], attributes],
            axis=1,
        ).set_index("filename")

        make_hub(
            files=args,
            output=kwargs["output"],
            details=df_details,
            group_by="antibody" if "antibody" in df_details.columns else "samplename",
        )

    else:
        make_hub(*args, **kwargs)
