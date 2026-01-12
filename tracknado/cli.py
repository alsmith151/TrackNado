from __future__ import annotations
import os
import pathlib
import click
import pandas as pd
from typing import Literal, Optional
from loguru import logger

import tracknado as tn

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
            done = False
            value = [value]
            if self.save_other_options:
                while state.rargs and not done:
                    for prefix in self._eat_all_parser.prefixes:
                        if state.rargs[0].startswith(prefix):
                            done = True
                    if not done:
                        value.append(state.rargs.pop(0))
            else:
                value += state.rargs
                state.rargs[:] = []
            value = tuple(value)
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
    """TrackNado: Generate UCSC track hubs with ease.
    TrackNado go BRRRR!
    """

@cli.command()
@click.option("-i", "--input-files", help="Input files", cls=OptionEatAll, type=tuple)
@click.option("-o", "--output", help="Hub output directory", required=True)
@click.option(
    "-d",
    "--details",
    help="Extra details (CSV/TSV) for each file. MUST contain: 'fn' column",
)
@click.option(
    "--seqnado",
    help="Use seqnado directory structure for metadata extraction",
    is_flag=True,
    default=False,
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
    default="hg38",
)
@click.option(
    "--color-by",
    help="Column name to use for track colors",
    default=None,
)
@click.option(
    "--supergroup-by",
    help="Column(s) defining supertracks",
    multiple=True,
    default=None,
)
@click.option(
    "--subgroup-by",
    help="Column(s) defining subgroupings (composite tracks)",
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
    "--url-prefix", 
    help="URL prefix for the hub", 
    default="https://userweb.molbiol.ox.ac.uk"
)
@click.option(
    "--convert",
    help="Convert tracks to UCSC formats (e.g. BED -> BigBed)",
    is_flag=True,
    default=False,
)
@click.option(
    "--chrom-sizes",
    help="Path to chrom.sizes file (required for conversion)",
    type=click.Path(exists=True, path_type=pathlib.Path),
)
def create(**kwargs):
    """Create a UCSC track hub from a set of files."""
    logger.info("Initializing TrackNado")
    
    builder = tn.HubBuilder()
    builder.convert_files = kwargs["convert"]
    builder.chrom_sizes = kwargs["chrom_sizes"]
    
    # 1. Add tracks
    if kwargs["details"]:
        logger.info(f"Loading details from {kwargs['details']}")
        df = pd.read_csv(kwargs["details"], sep=None, engine="python")
        builder.add_tracks_from_df(df)
    elif kwargs["input_files"]:
        logger.info(f"Adding {len(kwargs['input_files'])} input files")
        builder.add_tracks(list(kwargs["input_files"]))
    else:
        raise click.UsageError("Must provide --input-files or --details")
        
    # 2. Add extractors
    if kwargs["seqnado"]:
        builder.with_metadata_extractor(tn.from_seqnado_path)
        
    # 3. Configure groupings
    if kwargs["supergroup_by"]:
        builder.group_by(*kwargs["supergroup_by"], as_supertrack=True)
    if kwargs["subgroup_by"]:
        builder.group_by(*kwargs["subgroup_by"])
    if kwargs["overlay_by"]:
        builder.overlay_by(*kwargs["overlay_by"])
    if kwargs["color_by"]:
        builder.color_by(kwargs["color_by"])
        
    # 4. Build
    logger.info(f"Building hub '{kwargs['hub_name']}' for {kwargs['genome_name']}")
    hub = builder.build(
        name=kwargs["hub_name"],
        genome=kwargs["genome_name"],
        outdir=kwargs["output"],
        hub_email=kwargs["hub_email"]
    )
    
    logger.info("Staging hub files")
    hub.stage_hub()
    
    logger.info(f"Hub created successfully at {kwargs['output']}")
    logger.info(f"Hub URL: {kwargs['url_prefix'].strip('/')}/{kwargs['output'].strip('/')}/{kwargs['hub_name']}.hub.txt")

@cli.command()
@click.option("-i", "--input-configs", help="Paths to tracknado_config.json files", cls=OptionEatAll, type=tuple, required=True)
@click.option("-o", "--output", help="Hub output directory", required=True)
@click.option("--hub-name", help="Name of merged hub", default="MERGED_HUB")
@click.option("--genome-name", help="Name of genome", default="hg38")
@click.option("--hub-email", help="Email for hub", default="alastair.smith@ndcls.ox.ac.uk")
def merge(**kwargs):
    """Merge multiple TrackNado hubs into one using their sidecar configs."""
    logger.info(f"Merging {len(kwargs['input_configs'])} hub configurations")
    
    builders = [tn.HubBuilder.from_json(cfg) for cfg in kwargs["input_configs"]]
    
    main_builder = builders[0]
    if len(builders) > 1:
        main_builder.merge(*builders[1:])
        
    hub = main_builder.build(
        name=kwargs["hub_name"],
        genome=kwargs["genome_name"],
        outdir=kwargs["output"],
        hub_email=kwargs["hub_email"]
    )
    
    logger.info("Staging merged hub")
    hub.stage_hub()
    logger.info(f"Merged hub created at {kwargs['output']}")

@cli.command()
@click.argument("hub_path", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Fail on any warning")
def validate(hub_path, strict):
    """Validate a local hub directory or hub.txt file."""
    logger.info(f"Validating hub at {hub_path}")
    
    path = pathlib.Path(hub_path)
    if path.is_dir():
        # Try to find a hub.txt
        hub_files = list(path.glob("*.hub.txt"))
        if not hub_files:
            logger.error(f"No .hub.txt file found in {hub_path}")
            # Fallback to internal structure check
            validator = tn.HubValidator(path)
            valid = validator.validate_all()
            for err in validator.errors: logger.error(err)
            for warn in validator.warnings: logger.warning(warn)
            if not valid: raise click.ClickException("Hub structure is invalid")
            logger.info("Hub structure is valid (standard structure)")
            return
        path = hub_files[0]

    valid, message = tn.validate_hub(path, strict=strict)
    if valid:
        logger.info(f"Success: {message}")
    else:
        logger.error(f"Validation failed: {message}")
        raise click.ClickException("Hub validation failed")

if __name__ == "__main__":
    cli()








