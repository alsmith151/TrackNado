"""Helpers for converting user-facing colour values to UCSC RGB tuples."""

from __future__ import annotations

from collections.abc import Sequence
from math import isnan
from typing import Any

from PIL import ImageColor


def parse_color(value: Any) -> tuple[int, int, int] | None:
    """Convert a colour value to an ``(R, G, B)`` tuple.

    Accepted values include named colours (``"steelblue"``), hexadecimal values
    (``"#4682B4"`` or ``"#48B"``), CSS ``rgb(...)`` strings, comma-separated
    RGB values, and three-item numeric sequences. Empty values return ``None``.
    """
    if value is None:
        return None
    if isinstance(value, float) and isnan(value):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        channels = [channel.strip() for channel in value.split(",")]
        if len(channels) == 3:
            try:
                return _validate_channels(tuple(int(channel) for channel in channels))
            except ValueError:
                # Let Pillow provide support for formats such as rgb(1, 2, 3).
                pass

        try:
            return _validate_channels(ImageColor.getrgb(value))
        except ValueError as exc:
            raise ValueError(
                f"Invalid colour {value!r}. Use a named colour, a hex value such "
                "as '#4682B4', or an RGB value such as '70,130,180'."
            ) from exc

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        try:
            return _validate_channels(tuple(int(channel) for channel in value))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid colour {value!r}. RGB colours must contain three integers "
                "between 0 and 255."
            ) from exc

    raise ValueError(
        f"Invalid colour {value!r}. Use a named colour, a hex value, or an RGB value."
    )


def _validate_channels(channels: tuple[int, ...]) -> tuple[int, int, int]:
    if len(channels) != 3 or any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError("RGB colours must contain three integers between 0 and 255.")
    return channels  # type: ignore[return-value]
