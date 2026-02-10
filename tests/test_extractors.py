import pytest
from pathlib import Path
from tracknado.extractors import (
    from_seqnado_path,
    from_filename_pattern,
    from_parent_dirs,
    compose_extractors,
    with_static_metadata,
)

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


def test_from_filename_pattern_no_match():
    path = Path("SAMPLE_CTCF_R1.bigWig")
    extractor = from_filename_pattern(r"(?P<sample>.+?)_(?P<mark>.+?)\.bam")
    metadata = extractor(path)
    assert metadata == {}

def test_from_parent_dirs(seqnado_structure):
    extractor = from_parent_dirs(depth=2, names=["norm", "method"])
    metadata = extractor(seqnado_structure)
    assert metadata["norm"] == "CPM"
    assert metadata["method"] == "ATAC_Tn5"


def test_from_seqnado_path_mcc(tmp_dir):
    path = tmp_dir / "seqnado_output" / "MCC" / "bigwigs" / "mcc" / "replicates" / "sample1_view1.bigWig"
    path.parent.mkdir(parents=True)
    path.touch()

    metadata = from_seqnado_path(path)
    assert metadata["assay"] == "MCC"
    assert metadata["viewpoint"] == "view1"


def test_from_seqnado_path_rna(tmp_dir):
    path = tmp_dir / "seqnado_output" / "RNA" / "bigwigs" / "STAR" / "CPM" / "sample1_plus.bigWig"
    path.parent.mkdir(parents=True)
    path.touch()

    metadata = from_seqnado_path(path)
    assert metadata["assay"] == "RNA"
    assert metadata["strand"] == "plus"


def test_compose_extractors_no_overwrite():
    path = Path("K562_CTCF.bigWig")
    e1 = with_static_metadata(sample="DEFAULT", assay="ATAC")
    e2 = from_filename_pattern(r"(?P<sample>.+?)_(?P<mark>.+?)\.")

    extractor = compose_extractors(e1, e2, overwrite=False)
    metadata = extractor(path)

    assert metadata["sample"] == "DEFAULT"
    assert metadata["assay"] == "ATAC"
    assert metadata["mark"] == "CTCF"


def test_compose_extractors_with_overwrite():
    path = Path("K562_CTCF.bigWig")
    e1 = with_static_metadata(sample="DEFAULT")
    e2 = from_filename_pattern(r"(?P<sample>.+?)_(?P<mark>.+?)\.")

    extractor = compose_extractors(e1, e2, overwrite=True)
    metadata = extractor(path)

    assert metadata["sample"] == "K562"
    assert metadata["mark"] == "CTCF"
