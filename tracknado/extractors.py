from __future__ import annotations
import re
from pathlib import Path
from typing import Callable

def from_seqnado_path(path: Path) -> dict[str, str]:
    """Extract metadata from seqnado file paths.
    
    Pattern: .../assay/method/norm/samplename.ext
    Example: .../ATAC/ATAC_Tn5/CPM/sample1.bigWig
    """
    metadata = {}
    parts = path.parts
    if len(parts) >= 4:
        # We assume the directory structure is relatively fixed for seqnado
        metadata["norm"] = parts[-2]
        metadata["method"] = parts[-3]
        metadata["assay"] = parts[-4]
    
    # samplename is usually the stem, but seqnado sometimes has extensions like .plus/.minus
    # We'll take the first part before any dots or underscores commonly used
    stem = path.stem
    metadata["samplename"] = re.split(r"[._]", stem)[0]
    
    return metadata

def from_filename_pattern(pattern: str) -> Callable[[Path], dict[str, str]]:
    """Create extractor from regex pattern with named groups."""
    regex = re.compile(pattern)
    
    def extractor(path: Path) -> Dict[str, str]:
        match = regex.search(path.name)
        if match:
            return match.groupdict()
        return {}
        
    return extractor

def from_parent_dirs(depth: int = 1, names: list[str] = None) -> Callable[[Path], dict[str, str]]:
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
