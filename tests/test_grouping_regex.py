from tracknado.builder import HubBuilder


def test_grouping_regex_extracts_metadata_and_supports_grouping(tmp_dir):
    track = tmp_dir / "treated_CTCF.bigWig"
    track.touch()

    builder = (
        HubBuilder()
        .add_tracks([track])
        .with_grouping_regex(r"(?P<condition>[^_]+)_(?P<mark>[^.]+)\.bigWig")
        .group_by("condition")
        .group_by("mark", as_supertrack=True)
    )

    design = builder._prepare_design_df()

    assert design.iloc[0]["condition"] == "treated"
    assert design.iloc[0]["mark"] == "CTCF"
    assert builder.group_by_cols == ["condition"]
    assert builder.supergroup_by_cols == ["mark"]


def test_configure_builder_warns_when_no_grouping_source(monkeypatch, tmp_dir):
    track = tmp_dir / "sample.bigWig"
    track.touch()

    warnings: list[str] = []

    def capture_warning(message):
        warnings.append(message)

    monkeypatch.setattr("tracknado.builder.logger.warning", capture_warning)

    builder = HubBuilder()
    configured = builder
    configured = configured.add_tracks([track])

    # Use the shared helper path so the warning behavior matches CLI/API usage.
    from tracknado.builder import configure_builder_from_inputs

    configured = configure_builder_from_inputs(input_files=[track])

    assert configured.tracks[0].path == track
    assert warnings == ["No metadata source was provided, so no grouping can be performed."]