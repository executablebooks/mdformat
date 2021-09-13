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


class InvalidConfKeyError(Exception):
    def __init__(self, key: str, conf_path: Path) -> None:
        self.key = key
        self.conf_path = conf_path


@functools.lru_cache()
def read_toml_opts(file_path: Path | None) -> Mapping:
    toml_opts = {}
    if not file_path:
        file_path = Path.cwd() / "foo.md"
    for parent_dir in file_path.parents:
        conf_path = parent_dir / ".mdformat.toml"
        if conf_path.is_file():
            with open(conf_path, "rb") as f:
                toml_opts = tomli.load(f)
            break

    for key in toml_opts:
        if key not in DEFAULT_OPTS:
            raise InvalidConfKeyError(key, conf_path)
    return toml_opts
