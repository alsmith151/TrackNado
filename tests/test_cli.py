from pathlib import Path

from typer.testing import CliRunner

import pandas as pd

import tracknado as tn
from tracknado.cli import app


def test_configure_builder_from_inputs_matches_cli_defaults(seqnado_structure, tmp_dir):
    metadata = tmp_dir / "tracks.csv"
    metadata.write_text(
        "file_path,cell_type\n"
        f"{seqnado_structure},Tcell\n"
    )

    builder = tn.configure_builder_from_inputs(
        metadata=metadata,
        seqnado=True,
        convert=True,
        chrom_sizes=tmp_dir / "hg38.chrom.sizes",
        custom_genome=True,
        twobit=tmp_dir / "genome.2bit",
        organism="Human",
        default_pos="chr1:10000-20000",
        subgroup_by=["cell_type"],
    )

    assert builder.convert_files is True
    assert builder.chrom_sizes == tmp_dir / "hg38.chrom.sizes"
    assert builder.custom_genome_config["genome_default_position"] == "chr1:10000-20000"
    assert builder.group_by_cols == ["cell_type"]

    design = builder._prepare_design_df()
    assert design.iloc[0]["norm"] == "CPM"
    assert design.iloc[0]["method"] == "ATAC_Tn5"


def test_cli_create_delegates_to_shared_builder_helper(monkeypatch, tmp_dir):
    input_file = tmp_dir / "sample.bigWig"
    input_file.touch()
    output_dir = tmp_dir / "hub_out"

    captured = {}

    class DummyHub:
        def stage_hub(self, remove_existing=False):
            captured["stage_hub"] = remove_existing

    class DummyBuilder:
        def build(self, **kwargs):
            captured["build"] = kwargs
            return DummyHub()

    def fake_configure_builder_from_inputs(**kwargs):
        captured["configure"] = kwargs
        return DummyBuilder()

    monkeypatch.setattr(
        "tracknado.cli.tn.configure_builder_from_inputs",
        fake_configure_builder_from_inputs,
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "create",
            "-i",
            str(input_file),
            "-o",
            str(output_dir),
            "--genome-name",
            "hg38",
            "--hub-name",
            "TEST_HUB",
            "--hub-email",
            "test@example.com",
            "--convert",
            "--chrom-sizes",
            str(tmp_dir / "hg38.chrom.sizes"),
            "--default-pos",
            "chr1:10000-20000",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["configure"]["input_files"] == [Path(input_file)]
    assert captured["configure"]["convert"] is True
    assert captured["configure"]["chrom_sizes"] == Path(tmp_dir / "hg38.chrom.sizes")
    assert captured["build"]["name"] == "TEST_HUB"
    assert captured["build"]["genome"] == "hg38"
    assert captured["build"]["outdir"] == output_dir
    assert captured["build"]["hub_email"] == "test@example.com"
    assert captured["build"]["description_html"] is None
    assert captured["stage_hub"] is False


def test_cli_design_generates_editable_metadata_table(tmp_dir):
    track_a = tmp_dir / "k562_ctcf.bw"
    track_b = tmp_dir / "peaks.bb"
    track_a.touch()
    track_b.touch()
    output = tmp_dir / "tracks.csv"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "design",
            "-i",
            str(track_a),
            "-i",
            str(track_b),
            "-o",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    df = pd.read_csv(output)
    assert list(df["file_path"]) == [str(track_a), str(track_b)]
    assert list(df["name"]) == ["k562_ctcf", "peaks"]
    assert list(df["ext"]) == ["bigWig", "bigBed"]
    for col in ["color", "supertrack", "composite", "overlay"]:
        assert col in df.columns
    assert "path" not in df.columns
