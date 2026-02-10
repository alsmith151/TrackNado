from __future__ import annotations
import re
from pathlib import Path
from typing import Callable

MetadataExtractor = Callable[[Path], dict[str, str]]

def determine_seqnado_assay(parts: list[str]) -> str:
    parts_lower = [p.lower() for p in parts]
    for i, part in enumerate(parts_lower):
        if part == "seqnado_output" and i + 1 < len(parts):
            return parts[i + 1]

    if len(parts) >= 4:
        return parts[-4]
    
    raise ValueError("Could not determine assay from path")


def from_seqnado_path(path: Path) -> dict[str, str]:
    """Extract metadata from seqnado file paths.
    
    Pattern: .../seqnado_output/{assay}/[bigwigs/peaks]/{method}/{norm}/{sample}_{strand|viewpoint}.[bigWig|bed]
    Example: .../seqnado_output/atac/bigwigs/atac_tn5/cpm/sample1.bigWig
    """
    metadata = {}
    parts = list(path.parts)

    metadata["assay"] = determine_seqnado_assay(parts)
    metadata["norm"] = parts[-2]
    metadata["method"] = parts[-3]
    metadata['file_type'] = parts[-4]   # bigwigs or peaks for now
    
    # samplename is usually the stem, but seqnado sometimes has extensions like .plus/.minus
    # We'll take the first part before any dots or underscores commonly used
    stem = path.stem
    metadata["samplename"] = re.split(r"[._]", stem)[0]

    # If the assay is "MCC" we need to extract the viewpoint from the filename
    # Pattern looks like: /bigwigs/mcc/replicates/{sample}_{viewpoint_group}.bigWig
    if metadata["assay"] == "MCC":
        metadata["viewpoint"] = re.split(r"[._]", stem)[-1].split(".")[0]
    
    # For RNA we need to extract the strandedness from the filename
    # Pattern looks like: /bigwigs/{method}/{norm}/{sample}_{strand}.bigWig
    elif metadata["assay"] == "RNA":
        metadata["strand"] = re.split(r"[._]", stem)[-1].split(".")[0]

    return metadata

def from_filename_pattern(pattern: str) -> MetadataExtractor:
    """Create extractor from regex pattern with named groups."""
    regex = re.compile(pattern)
    
    def extractor(path: Path) -> dict[str, str]:
        match = regex.search(path.name)
        if match:
            return match.groupdict()
        return {}
        
    return extractor

def from_parent_dirs(depth: int = 1, names: list[str] = None) -> MetadataExtractor:
    """Extract metadata from parent directory names.
    
    Args:
        depth: How many levels up to go
        names: Optional list of keys for the directory levels (last to first)
    """
    def extractor(path: Path) -> dict[str, str]:
        metadata = {}
        current = path.parent
        for i in range(depth):
            if current == current.parent: # Reached root
                break
            key = names[i] if names and i < len(names) else f"dir_{i+1}"
            metadata[key] = current.name
            current = current.parent
        return metadata
        
    return extractor


def compose_extractors(
    *extractors: MetadataExtractor, overwrite: bool = True
) -> MetadataExtractor:
    """Compose multiple extractors into one extractor function."""
    def extractor(path: Path) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for fn in extractors:
            extracted = fn(path)
            if overwrite:
                metadata.update(extracted)
            else:
                for key, value in extracted.items():
                    metadata.setdefault(key, value)
        return metadata

    return extractor


def with_static_metadata(**values: str) -> MetadataExtractor:
    """Create a simple metadata stub extractor with static key/value pairs."""
    metadata = {k: str(v) for k, v in values.items()}

    def extractor(path: Path) -> dict[str, str]:
        return metadata.copy()

    return extractor
