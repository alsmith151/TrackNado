import pytest
import pandas as pd
from pathlib import Path
from tracknado.builder import HubBuilder
from tracknado.extractors import from_seqnado_path

def test_builder_add_tracks(sample_bigwig):
    builder = HubBuilder().add_tracks([sample_bigwig], antibody="CTCF")
    assert len(builder.tracks) == 1
    assert builder.tracks[0].metadata["antibody"] == "CTCF"

def test_builder_from_df(tmp_dir):
    df = pd.DataFrame([
        {"fn": str(tmp_dir / "f1.bw"), "cell": "K562"},
        {"fn": str(tmp_dir / "f2.bw"), "cell": "GM12878"}
    ])
    # Touch files so Track validation passes (if we ever enable it)
    for f in df["fn"]: Path(f).touch()
    
    builder = HubBuilder().add_tracks_from_df(df)
    assert len(builder.tracks) == 2
    assert builder.tracks[0].metadata["cell"] == "K562"

def test_builder_chaining(sample_bigwig):
    builder = (
        HubBuilder()
        .add_tracks([sample_bigwig])
        .group_by("method", as_supertrack=True)
        .color_by("samplename")
    )
    assert "method" in builder.supergroup_by_cols
    assert builder.color_by_col == "samplename"

def test_builder_prepare_df(seqnado_structure):
    builder = (
        HubBuilder()
        .add_tracks([seqnado_structure])
        .with_metadata_extractor(from_seqnado_path)
    )
    df = builder._prepare_design_df()
    assert df.iloc[0]["norm"] == "CPM"
    assert df.iloc[0]["method"] == "ATAC_Tn5"

def test_builder_merge(sample_bigwig, sample_bigbed):
    b1 = HubBuilder().add_tracks([sample_bigwig], set="A").group_by("cell").color_by("cell")
    b2 = HubBuilder().add_tracks([sample_bigbed], set="B").group_by("mark")
    
    merged = b1.merge(b2)
    assert len(merged.tracks) == 2
    assert merged.tracks[0].metadata["set"] == "A"
    assert merged.tracks[1].metadata["set"] == "B"
    # Verify settings reconciliation
    assert "cell" in merged.group_by_cols
    assert "mark" in merged.group_by_cols
    assert merged.color_by_col == "cell"

def test_builder_serialization(sample_bigwig, tmp_dir):
    builder = (
        HubBuilder()
        .add_tracks([sample_bigwig], antibody="CTCF")
        .group_by("method", as_supertrack=True)
        .color_by("samplename")
    )
    
    # To JSON string
    json_data = builder.to_json()
    assert "CTCF" in json_data
    assert "method" in json_data
    
    # From JSON string
    new_builder = HubBuilder.from_json(json_data)
    assert len(new_builder.tracks) == 1
    assert new_builder.tracks[0].metadata["antibody"] == "CTCF"
    assert "method" in new_builder.supergroup_by_cols
    assert new_builder.color_by_col == "samplename"

    # To/From JSON file
    json_path = tmp_dir / "config.json"
    builder.to_json(json_path)
    assert json_path.exists()
    
    file_builder = HubBuilder.from_json(json_path)
    assert len(file_builder.tracks) == 1
    assert file_builder.tracks[0].path == sample_bigwig
