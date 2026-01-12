import pytest
from pathlib import Path
from tracknado.models import Track, TrackGroup

def test_track_creation(sample_bigwig):
    track = Track(path=sample_bigwig, name="Test Track", metadata={"antibody": "CTCF"})
    assert track.path == sample_bigwig
    assert track.name == "Test Track"
    assert track.metadata["antibody"] == "CTCF"

def test_track_invalid_color(sample_bigwig):
    with pytest.raises(ValueError, match="Color values must be 0-255"):
        Track(path=sample_bigwig, color=(300, 0, 0))

def test_track_group_creation(sample_bigwig):
    track = Track(path=sample_bigwig)
    group = TrackGroup(name="Group 1", tracks=[track])
    assert group.name == "Group 1"
    assert len(group.tracks) == 1
    assert group.tracks[0].path == sample_bigwig

def test_recursive_group():
    subgroup = TrackGroup(name="Sub")
    parent = TrackGroup(name="Parent", subgroups=[subgroup])
    assert parent.subgroups[0].name == "Sub"
