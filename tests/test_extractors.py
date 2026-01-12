import pytest
from pathlib import Path
from tracknado.extractors import from_seqnado_path, from_filename_pattern, from_parent_dirs

def test_from_seqnado_path(seqnado_structure):
    metadata = from_seqnado_path(seqnado_structure)
    assert metadata["assay"] == "ATAC"
    assert metadata["method"] == "ATAC_Tn5"
    assert metadata["norm"] == "CPM"
    assert metadata["samplename"] == "sample1"

def test_from_filename_pattern():
    path = Path("SAMPLE_CTCF_R1.bigWig")
    extractor = from_filename_pattern(r"(?P<sample>.+?)_(?P<mark>.+?)_(?P<rep>.+)\.")
    metadata = extractor(path)
    assert metadata["sample"] == "SAMPLE"
    assert metadata["mark"] == "CTCF"
    assert metadata["rep"] == "R1"

def test_from_parent_dirs(seqnado_structure):
    extractor = from_parent_dirs(depth=2, names=["norm", "method"])
    metadata = extractor(seqnado_structure)
    assert metadata["norm"] == "CPM"
    assert metadata["method"] == "ATAC_Tn5"
