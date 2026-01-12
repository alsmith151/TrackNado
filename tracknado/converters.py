from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger

class ToolFinder:
    """Helper to find UCSC tools in various environments."""
    
    @staticmethod
    def find_local(tool: str) -> str | None:
        """Find tool in PATH or ~/bin."""
        path = shutil.which(tool)
        if path:
            return path
        
        home_bin = Path.home() / "bin" / tool
        if home_bin.exists() and os.access(home_bin, os.X_OK):
            return str(home_bin)
        
        return None

    @staticmethod
    def get_container_cmd(tool: str) -> list[str] | None:
        """Determine if we can use Apptainer or Docker."""
        container_images = {
            "bedToBigBed": "quay.io/biocontainers/ucsc-bedtobigbed:447--h29774a3_3",
            "gtfToGenePred": "quay.io/biocontainers/ucsc-gtftogenepred:447--h29774a3_3",
            "gff3ToGenePred": "quay.io/biocontainers/ucsc-gff3togenepred:447--h29774a3_2",
            "genePredToBigGenePred": "quay.io/biocontainers/ucsc-genepredtobiggenepred:447--h29774a3_3"
        }
        image = container_images.get(tool)
        if not image:
            return None

        # Try Apptainer
        if shutil.which("apptainer"):
            return ["apptainer", "exec", f"docker://{image}", tool]
        elif shutil.which("singularity"):
            return ["singularity", "exec", f"docker://{image}", tool]
        
        # Try Docker
        if shutil.which("docker"):
            # Note: Docker requires mounting volumes, which we'll handle in the execution step
            return ["docker", "run", "--rm", "-v", "{cwd}:{cwd}", "-w", "{cwd}", image, tool]
            
        return None

def convert_bed_to_bigbed(
    input_bed: Path, 
    chrom_sizes: Path, 
    output_bb: Path | None = None,
    force_container: bool = False
) -> Path:
    """Convert a BED file to BigBed format."""
    if output_bb is None:
        output_bb = input_bed.with_suffix(".bb")

    # 1. Find tool
    cmd_prefix = []
    if not force_container:
        local_tool = ToolFinder.find_local("bedToBigBed")
        if local_tool:
            cmd_prefix = [local_tool]
    
    if not cmd_prefix:
        container_cmd = ToolFinder.get_container_cmd("bedToBigBed")
        if container_cmd:
            cmd_prefix = container_cmd
        else:
            raise RuntimeError(
                "bedToBigBed not found locally and no container engine (Apptainer/Docker) detected. "
                "Please install bedToBigBed or a container engine."
            )

    # 2. Sort BED file (required for bedToBigBed)
    logger.info(f"Sorting {input_bed.name}...")
    sorted_bed = tempfile.NamedTemporaryFile(suffix=".sorted.bed", delete=False).name
    try:
        # We use LC_ALL=C for consistent sorting
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        subprocess.run(
            ["sort", "-k1,1", "-k2,2n", str(input_bed)],
            stdout=open(sorted_bed, "w"),
            check=True,
            env=env
        )

        # 3. Run bedToBigBed
        logger.info(f"Converting {input_bed.name} to BigBed...")
        
        # Prepare actual command (handling Docker mount replacement if needed)
        cwd = os.getcwd()
        final_cmd = []
        for part in cmd_prefix:
            if isinstance(part, str):
                final_cmd.append(part.replace("{cwd}", cwd))
        
        final_cmd.extend([sorted_bed, str(chrom_sizes), str(output_bb)])
        
        subprocess.run(final_cmd, check=True)
        logger.info(f"Successfully created {output_bb}")
        
    finally:
        if os.path.exists(sorted_bed):
            os.remove(sorted_bed)

    return output_bb

def convert_gtf_to_biggenepred(
    input_file: Path,
    chrom_sizes: Path,
    output_bb: Path | None = None,
    force_container: bool = False
) -> Path:
    """Convert a GTF or GFF file to BigGenePred format."""
    if output_bb is None:
        output_bb = input_file.with_suffix(".bb")

    ext = input_file.suffix.lower()
    conv_tool = "gtfToGenePred" if ext == ".gtf" else "gff3ToGenePred"
    
    # Check for tools
    tools = [conv_tool, "genePredToBigGenePred", "bedToBigBed"]
    cmd_prefixes = {}
    
    for tool in tools:
        cmd_prefix = []
        if not force_container:
            local_tool = ToolFinder.find_local(tool)
            if local_tool:
                cmd_prefix = [local_tool]
        
        if not cmd_prefix:
            container_cmd = ToolFinder.get_container_cmd(tool)
            if container_cmd:
                cmd_prefix = container_cmd
            else:
                 raise RuntimeError(
                    f"{tool} not found locally and no container engine detected."
                )
        cmd_prefixes[tool] = cmd_prefix

    as_file = Path(__file__).parent / "as_files" / "bigGenePred.as"
    if not as_file.exists():
        raise FileNotFoundError(f"Required autoSql file not found: {as_file}")

    intermediate_genepred = tempfile.NamedTemporaryFile(suffix=".genePred", delete=False).name
    intermediate_txt = tempfile.NamedTemporaryFile(suffix=".txt", delete=False).name
    
    try:
        cwd = os.getcwd()
        
        # 1. Convert to genePred
        logger.info(f"Converting {input_file.name} to genePred...")
        cmd1 = []
        for part in cmd_prefixes[conv_tool]:
            cmd1.append(part.replace("{cwd}", cwd))
        if conv_tool == "gtfToGenePred":
            cmd1.extend(["-genePredExt", str(input_file), intermediate_genepred])
        else: # gff3ToGenePred
            cmd1.extend([str(input_file), intermediate_genepred])
        subprocess.run(cmd1, check=True)

        # 2. Convert to bigGenePred text
        logger.info("Converting genePred to bigGenePred text...")
        cmd2 = []
        for part in cmd_prefixes["genePredToBigGenePred"]:
            cmd2.append(part.replace("{cwd}", cwd))
        cmd2.extend([intermediate_genepred, intermediate_txt])
        subprocess.run(cmd2, check=True)

        # 3. Sort bigGenePred text (required for bedToBigBed)
        logger.info("Sorting bigGenePred text...")
        sorted_txt = tempfile.NamedTemporaryFile(suffix=".sorted.txt", delete=False).name
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        subprocess.run(
            ["sort", "-k1,1", "-k2,2n", intermediate_txt],
            stdout=open(sorted_txt, "w"),
            check=True,
            env=env
        )

        # 4. Convert to BigBed with .as
        logger.info(f"Converting to BigGenePred: {output_bb.name}...")
        cmd4 = []
        for part in cmd_prefixes["bedToBigBed"]:
            cmd4.append(part.replace("{cwd}", cwd))
        cmd4.extend([
            "-type=bed12+8", 
            "-tab", 
            f"-as={as_file}", 
            sorted_txt, 
            str(chrom_sizes), 
            str(output_bb)
        ])
        subprocess.run(cmd4, check=True)
        
        if os.path.exists(sorted_txt):
            os.remove(sorted_txt)
            
        logger.info(f"Successfully created {output_bb}")

    finally:
        for f in [intermediate_genepred, intermediate_txt]:
            if os.path.exists(f):
                os.remove(f)

    return output_bb
