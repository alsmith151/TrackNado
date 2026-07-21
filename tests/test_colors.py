import pandas as pd
import pytest

from tracknado.api import TrackDesign
from tracknado.colors import parse_color


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("steelblue", (70, 130, 180)),
        ("#4682B4", (70, 130, 180)),
        ("#48B", (68, 136, 187)),
        ("rgb(70, 130, 180)", (70, 130, 180)),
        ("70, 130, 180", (70, 130, 180)),
        ((70, 130, 180), (70, 130, 180)),
    ],
)
def test_parse_color_accepts_common_formats(value, expected):
    assert parse_color(value) == expected


def test_parse_color_allows_empty_values():
    assert parse_color("") is None
    assert parse_color(None) is None
    assert parse_color(float("nan")) is None


def test_parse_color_rejects_invalid_values():
    with pytest.raises(ValueError, match="Invalid colour"):
        parse_color("not-a-colour")


def test_track_design_normalizes_metadata_colours():
    details = pd.DataFrame(
        [
            {
                "file_path": "one.bw",
                "path": "/tmp/one.bw",
                "name": "one",
                "ext": "bigWig",
                "color": "steelblue",
            },
            {
                "file_path": "two.bw",
                "path": "/tmp/two.bw",
                "name": "two",
                "ext": "bigWig",
                "color": "#ff8c00",
            },
            {
                "file_path": "three.bw",
                "path": "/tmp/three.bw",
                "name": "three",
                "ext": "bigWig",
                "color": None,
            },
        ]
    )

    design = TrackDesign.from_design(details)

    assert list(design.details["color"]) == [
        (70, 130, 180),
        (255, 140, 0),
        None,
    ]
