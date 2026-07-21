"""Resolve published track-hub URLs from user-defined hosting profiles."""

from __future__ import annotations

import os
import pathlib
from urllib.parse import quote

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


def default_hosting_config_path() -> pathlib.Path:
    """Return the per-user configuration location without requiring it to exist."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return pathlib.Path(config_home) / "tracknado" / "hosting.toml"
    return pathlib.Path.home() / ".config" / "tracknado" / "hosting.toml"


def hub_url_from_profile(
    output: pathlib.Path,
    hub_name: str,
    profile_name: str,
    config_path: pathlib.Path | None = None,
) -> str:
    """Build a hub URL using a ``[hosting.<name>]`` TOML profile.

    A profile maps a local directory tree to its externally visible URL tree.
    ``output`` must be inside the configured ``local_root``.
    """
    config_path = (config_path or default_hosting_config_path()).expanduser()
    if not config_path.is_file():
        raise ValueError(f"Hosting configuration not found: {config_path}")

    try:
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in hosting configuration {config_path}: {exc}") from exc

    profile = config.get("hosting", {}).get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"No hosting profile named {profile_name!r} in {config_path}")

    local_root = profile.get("local_root")
    public_root = profile.get("public_root")
    if not isinstance(local_root, str) or not isinstance(public_root, str):
        raise ValueError(
            f"Hosting profile {profile_name!r} must define string local_root and public_root values"
        )

    output_path = output.expanduser().resolve()
    root_path = pathlib.Path(local_root).expanduser().resolve()
    try:
        relative_path = output_path.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(
            f"Output directory {output_path} is not inside profile {profile_name!r}'s "
            f"local_root ({root_path})"
        ) from exc

    public_path = "/".join(quote(part, safe="") for part in relative_path.parts)
    hub_file = quote(f"{hub_name}.hub.txt", safe="")
    return f"{public_root.rstrip('/')}/{public_path}/{hub_file}"
