from pathlib import Path

import pytest

from tracknado.hosting import hub_url_from_profile


def test_hub_url_from_profile_maps_output_relative_to_local_root(tmp_dir):
    local_root = tmp_dir / "published-hubs"
    output = local_root / "researcher" / "chipseq" / "hub directory"
    output.mkdir(parents=True)
    config = tmp_dir / "hosting.toml"
    config.write_text(
        "[hosting.site]\n"
        f'local_root = "{local_root}"\n'
        'public_root = "https://example.org/public"\n'
    )

    assert hub_url_from_profile(output, "PRJNA 317349", "site", config) == (
        "https://example.org/public/researcher/chipseq/hub%20directory/"
        "PRJNA%20317349.hub.txt"
    )


def test_hub_url_from_profile_rejects_output_outside_local_root(tmp_dir):
    local_root = tmp_dir / "published-hubs"
    local_root.mkdir()
    config = tmp_dir / "hosting.toml"
    config.write_text(
        "[hosting.site]\n"
        f'local_root = "{local_root}"\n'
        'public_root = "https://example.org/public/project"\n'
    )

    with pytest.raises(ValueError, match="not inside"):
        hub_url_from_profile(tmp_dir / "elsewhere", "hub", "site", config)
