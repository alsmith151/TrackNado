import pytest
import pathlib
import tempfile
import shutil
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD_LIB = PROJECT_ROOT / "build" / "lib"

if str(BUILD_LIB) in sys.path:
    sys.path.remove(str(BUILD_LIB))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
