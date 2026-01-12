import pytest
from pathlib import Path
from tracknado.validation import HubValidator

def test_hub_validator_missing_files(tmp_dir):
    validator = HubValidator(tmp_dir)
    assert validator.validate_all() is False
    assert any("hub.txt" in e for e in validator.errors)

def test_hub_validator_structure(tmp_dir):
    (tmp_dir / "myhub.hub.txt").touch()
    (tmp_dir / "hg38").mkdir()
    (tmp_dir / "hg38" / "genomes.txt").touch()
    (tmp_dir / "hg38" / "trackDb.txt").touch()
    
    validator = HubValidator(tmp_dir)
    # It might still fail track_files_exist but should pass structure
    validator.validate_structure()
    assert len(validator.errors) == 0

def test_hub_validator_track_files(tmp_dir):
    hg38_dir = tmp_dir / "hg38"
    hg38_dir.mkdir()
    trackdb = hg38_dir / "trackDb.txt"
    with open(trackdb, "w") as f:
        f.write("track test\nbigDataUrl missing.bw\n")
    
    validator = HubValidator(tmp_dir)
    validator.validate_track_files_exist()
    assert any("missing.bw" in w for w in validator.warnings)
