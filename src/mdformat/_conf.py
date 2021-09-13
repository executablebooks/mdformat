from __future__ import annotations

import functools
from pathlib import Path
from typing import Mapping

import tomli

DEFAULT_OPTS = {
    "wrap": "keep",
    "number": False,
    "end_of_line": "lf",
}


class InvalidConfError(Exception):
    """Error raised given invalid TOML or a key that is not valid for
    mdformat."""


@functools.lru_cache()
def read_toml_opts(conf_dir: Path) -> Mapping:
    conf_path = conf_dir / ".mdformat.toml"
    if not conf_path.is_file():
        parent_dir = conf_dir.parent
        if conf_dir == parent_dir:
            return {}
        return read_toml_opts(parent_dir)

    with open(conf_path, "rb") as f:
        try:
            toml_opts = tomli.load(f)
        except tomli.TOMLDecodeError as e:
            raise InvalidConfError(f"Invalid TOML syntax: {e}")

    for key in toml_opts:
        if key not in DEFAULT_OPTS:
            raise InvalidConfError(f"Invalid key {key!r} in {conf_path}")

    return toml_opts
