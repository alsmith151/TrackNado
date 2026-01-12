from __future__ import annotations
import pytest
import pathlib
from tracknado import HubBuilder
from unittest.mock import patch

def test_gtf_conversion_flow(tmp_path):
    # 1. Create a dummy GTF file
    gtf_file = tmp_path / "test.gtf"
    gtf_file.write_text("chr1\torigin\texon\t100\t200\t.\t+\t.\tgene_id \"G1\"; transcript_id \"T1\";")
    
    chrom_sizes = tmp_path / "hg38.chrom.sizes"
    chrom_sizes.write_text("chr1\t1000000\n")
    
    # 2. Mock the converter function
    with patch("tracknado.converters.convert_gtf_to_biggenepred") as mock_conv:
        mock_conv.return_type = tmp_path / "test.bb"
        mock_conv.side_effect = lambda input_file, chrom_sizes, output_bb, **kwargs: output_bb
        
        builder = (
            HubBuilder()
            .add_tracks([gtf_file])
            .with_convert_files()
            .with_chrom_sizes(chrom_sizes)
        )
        
        builder.build(
            name="GTFHub",
            genome="hg38",
            outdir=tmp_path / "hub_out"
        )
        
        assert mock_conv.called

def test_gtf_mapping():
    builder = HubBuilder().add_tracks(["genes.gtf"])
    df = builder._prepare_design_df()
    assert df.iloc[0]["ext"] == "bigGenePred"
