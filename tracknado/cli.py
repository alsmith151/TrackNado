import os
import click
from typing import Literal, Union
from loguru import logger

class OptionEatAll(click.Option):

    def __init__(self, *args, **kwargs):
        self.save_other_options = kwargs.pop('save_other_options', True)
        nargs = kwargs.pop('nargs', -1)
        assert nargs == -1, 'nargs, if set, must be -1 not {}'.format(nargs)
        super(OptionEatAll, self).__init__(*args, **kwargs)
        self._previous_parser_process = None
        self._eat_all_parser = None

    def add_to_parser(self, parser, ctx):

        def parser_process(value, state):
            # method to hook to the parser.process
            done = False
            value = [value]
            if self.save_other_options:
                # grab everything up to the next option
                while state.rargs and not done:
                    for prefix in self._eat_all_parser.prefixes:
                        if state.rargs[0].startswith(prefix):
                            done = True
                    if not done:
                        value.append(state.rargs.pop(0))
            else:
                # grab everything remaining
                value += state.rargs
                state.rargs[:] = []
            value = tuple(value)

            # call the actual process
            self._previous_parser_process(value, state)

        retval = super(OptionEatAll, self).add_to_parser(parser, ctx)
        for name in self.opts:
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break
        return retval


@click.group()
def cli():
    """Tracknado: A tool for generating UCSC track hubs
    Tracknado go BRRRR!
    """

@cli.command()
@click.option("-i", "--input-files", help="Input files", cls=OptionEatAll, type=list)
@click.option("-o", "--output", help="Design name", required=True)
@click.option(
    "--preset",
    help="Adjust design for specific use cases. Choose from: seqnado",
    type=click.Choice(["seqnado"]),
    default=None,
)

def design(input_files: list, output: str, preset: Union[None, Literal["seqnado"]]):

    from tracknado.api import TrackFiles

    tf = TrackFiles(input_files, infer_subgroups=True, infer_attributes=True)

    if preset == "seqnado":
        tf.files = tf.files.assign(experiment=lambda df: df["fn"].apply(lambda x: x.parent.parent.parent.name))

    tf.files.to_csv(output)



@cli.command()
@click.option("-i", "--input-files", help="Input files", cls=OptionEatAll, type=tuple)
@click.option("-o", "--output", help="Hub output directory", required=True)
@click.option("--save-hub-design", help="Save hub design to file", type=str)
@click.option(
    "-d",
    "--details",
    help="Extra details for each file. MUST contain: 'fn' column",
)
@click.option(
    "--infer-details",
    help="Infer details from filenames. Requires SAMPLENAME_[ANTIBODY]_[REPLICATE]",
    is_flag=True,
)
@click.option(
    "--hub-name",
    help="Name of hub to generate",
    default="HUB",
    required=True,
)
@click.option(
    "--hub-email",
    help="Email address for hub",
    default="alastair.smith@ndcls.ox.ac.uk",
    required=True,
)
@click.option(
    "--genome-name",
    help="Name of genome",
    default="hg19",
    required=True,
)
@click.option(
    "--custom-genome",
    help="Determines if this is a custom genome",
    is_flag=True,
    default=False,
)
@click.option(
    "--genome-twobit",
    help="Twobit file required for custom genome",
)
@click.option(
    "--genome-organism",
    help="Organism name required for custom genome",
    default="NA",
)
@click.option(
    "--color-by",
    help="Name of column in details dataframe to use for track colors",
    multiple=True,
    default=None,
)
@click.option("--description-html", help="Path to HTML file with hub description")
@click.option(
    "--supergroup-by",
    help="Column(s) defining supertracks",
    multiple=True,
    default=None,
)
@click.option(
    "--subgroup-by",
    help="Column(s) defining subgroupings for composite tracks. If any value is provided a composite track will be generated for each filetype",
    multiple=True,
    default=None,
)
@click.option(
    "--composite-by",
    help="Column(s) defining composite tracks.",
    multiple=True,
    default=None,
)
@click.option(
    "--overlay-by",
    help="Column(s) defining overlay tracks",
    multiple=True,
    default=None,
)
@click.option(
    "--convert-files",
    help="Convert files to UCSC compatible format",
    is_flag=True,
    default=False,
)
@click.option(
    "--chrom-sizes",
    help="Path to chrom.sizes file",
    default=None,
)
@click.option("--url-prefix", help="URL prefix for the hub", default="https://userweb.molbiol.ox.ac.uk")

def create(*args, **kwargs):

    """Create a UCSC track hub from a set of files

    The options provided will determine how the files are grouped into tracks and
    supertracks. 

    There are two ways to provide the files to be included in the hub. The first is to provide
    a list of files using the --input-files option. The second is to provide a design file using
    the --details option.

    File attributes can be inferred from the filenames using the --infer-details option. This
    option requires that the filenames are in the format SAMPLENAME_[ANTIBODY]_[REPLICATE].
    The attributes will be inferred from the filename and the following columns will be added
    to the design file (if they are present): 'sample_name', 'antibody', 'replicate'.
    
    The --supergroup-by, --subgroup-by, --composite-by, and --overlay-by options can be used to specify
    columns in the design file that will be used to group the files into tracks. The columns can be
    specified multiple times to group by multiple columns. For example, if the design file contains
    columns 'sample', 'antibody', and 'replicate' then the following options will group the files
    into supertracks by sample, then subtracks by antibody, then composite tracks by replicate:

    --supergroup-by sample --subgroup-by antibody --composite-by replicate

    The --color-by option can be used to specify a column in the design file that will be used to
    assign colors to the tracks. The colors will be assigned in the order that the values appear in
    the column unless colors are specified in the design file using the 'color' column.

    The --convert-files option can be used to convert the input files to UCSC compatible format. This
    option is only available for bed files at this time. The files will be converted in the current
    working directory and the converted files will be used to generate the hub. The original files
    will be left in place.

    A custom genome can be specified using the --custom-genome option. This option requires that
    the --genome-twobit and --genome-organism options are also provided.

    The --description-html option can be used to provide a path to an HTML file that will be used
    as the hub description. The HTML file will be copied to the hub directory and the path to the
    file will be added to the hub.txt file.

    """

    # sys.tracebacklimit = 0
    logger.info("Initialising tracknado")
    import pandas as pd
    from tracknado.api import TrackDesign, HubGenerator

    # Fix cli to api differences
    kwargs["color_by"] = kwargs["color_by"][0] if kwargs["color_by"] else None


    # Get design
    logger.info("Obtaining track design")
    if not kwargs["details"]:
        assert kwargs[
            "input_files"
        ], "Input file MUST be provided if not specifying by a design file"

        kwargs.pop("details")

        design = TrackDesign.from_files(
            kwargs["input_files"],
            infer_attributes=kwargs["infer_details"],
            chromosome_sizes=kwargs["chrom_sizes"],
            **kwargs
        )

    else:
        details = pd.read_csv(kwargs["details"], sep=r"\s+|\t|,", engine="python")
        kwargs.pop("input_files")
        kwargs.pop("details")

        design = TrackDesign.from_design(
            details,
            infer_attributes=kwargs["infer_details"],
            chromosome_sizes=kwargs["chrom_sizes"],
            **kwargs
        )


    logger.info("Generating hub")
    hub = HubGenerator(
        outdir=kwargs["output"],
        track_design=design,
        genome=kwargs["genome_name"],
        hub_name=kwargs["hub_name"],
        hub_email=kwargs["hub_email"],
        custom_genome=kwargs["custom_genome"],
        genome_twobit=kwargs["genome_twobit"],
        genome_organism=kwargs["genome_organism"],
        description_html=kwargs["description_html"],
    )

    logger.info("Staging hub (copying files to output directory)")
    hub.stage_hub()

    if kwargs["save_hub_design"]:
        design.to_pickle(kwargs["save_hub_design"])

    logger.info("Hub created successfully")
    logger.info(f"Hub directory: {kwargs['output']}")
    logger.info(f"Hub URL: {kwargs['url_prefix'].strip('/')}/{kwargs['output'].strip('/')}/{kwargs['hub_name']}.hub.txt")
    
    



@cli.command()
@click.option("-i", "--input-files", help="Input files", cls=OptionEatAll, type=tuple)
@click.option("-o", "--output", help="Hub output directory", required=True)
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
@click.option(
    "--custom-genome",
    help="Determines if this is a custom genome",
    is_flag=True,
    default=False,
)
@click.option(
    "--genome-twobit",
    help="Twobit file required for custom genome",
)
@click.option(
    "--genome-organism",
    help="Organism name required for custom genome",
    default="NA",
)
@click.option(
    "--color-by",
    help="Name of column in details dataframe to use for track colors",
    multiple=True,
    default=None,
    type=list
)
@click.option("--description-html", help="Path to HTML file with hub description")
@click.option(
    "--supergroup-by",
    help="Column(s) defining supertracks",
    multiple=True,
    default=None,
)
@click.option(
    "--subgroup-by",
    help="Column(s) defining subgroupings for composite tracks. If any value is provided a composite track will be generated for each filetype",
    multiple=True,
    default=None,
)
@click.option(
    "--composite-by",
    help="Column(s) defining composite tracks.",
    multiple=True,
    default=None,
)
@click.option(
    "--overlay-by",
    help="Column(s) defining overlay tracks",
    multiple=True,
    default=None,
)
def merge(*args, **kwargs):
    """Merge multiple seqnado created hubs into a single hub.
    
    This command will merge multiple seqnado created hubs into a single hub. 
    
    This requires that the hubs were created with the tracknado create command and that the hub designs were saved using the --save-hub-design option.
    """

    assert all(os.path.exists(hub) for hub in kwargs["input_files"]), "All input files must exist"

    import pandas as pd
    from tracknado.api import TrackDesign, HubGenerator

    for ii, hub in enumerate(kwargs["input_files"]):
        if ii == 0:
            design = TrackDesign.from_pickle(hub)
        else:
            design = design + TrackDesign.from_pickle(hub) # type: ignore
        

    hub = HubGenerator(
        outdir=kwargs["output"],
        track_design=design, # type: ignore
        genome=kwargs["genome_name"],
        hub_name=kwargs["hub_name"],
        hub_email=kwargs["hub_email"],
        custom_genome=kwargs["custom_genome"],
        genome_twobit=kwargs["genome_twobit"],
        genome_organism=kwargs["genome_organism"],
        description_html=kwargs["description_html"],
    )

    hub.stage_hub()








