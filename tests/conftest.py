import pytest
import pathlib
import tempfile
import shutil

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield pathlib.Path(tmp)

@pytest.fixture
def sample_bigwig(tmp_dir):
    path = tmp_dir / "sample.bigWig"
    path.touch()
    return path

@pytest.fixture
def sample_bigbed(tmp_dir):
    path = tmp_dir / "sample.bigBed"
    path.touch()
    return path

@pytest.fixture
def seqnado_structure(tmp_dir):
    """Create a mock seqnado directory structure."""
    path = tmp_dir / "ATAC" / "ATAC_Tn5" / "CPM" / "sample1.bigWig"
    path.parent.mkdir(parents=True)
    path.touch()
    return path
