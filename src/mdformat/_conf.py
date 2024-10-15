from __future__ import annotations

import functools
from pathlib import Path
from typing import Mapping

from mdformat._compat import tomllib

DEFAULT_OPTS = {
    "wrap": "keep",
    "number": False,
    "end_of_line": "lf",
    "exclude": [],
}


class InvalidConfError(Exception):
    """Error raised on invalid TOML configuration.

    Will be raised on:
    - invalid TOML
    - invalid conf key
    - invalid conf value
    """


@functools.lru_cache()
def read_toml_opts(conf_dir: Path) -> tuple[Mapping, Path | None]:
    conf_path = conf_dir / ".mdformat.toml"
    if not conf_path.is_file():
        parent_dir = conf_dir.parent
        if conf_dir == parent_dir:
            return {}, None
        return read_toml_opts(parent_dir)

    with open(conf_path, "rb") as f:
        try:
            toml_opts = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise InvalidConfError(f"Invalid TOML syntax: {e}")

    _validate_keys(toml_opts, conf_path)
    _validate_values(toml_opts, conf_path)

    return toml_opts, conf_path


def _validate_values(opts: Mapping, conf_path: Path) -> None:  # noqa: C901
    if "wrap" in opts:
        wrap_value = opts["wrap"]
        if not (
            (isinstance(wrap_value, int) and wrap_value > 1)
            or wrap_value in {"keep", "no"}
        ):
            raise InvalidConfError(f"Invalid 'wrap' value in {conf_path}")
    if "end_of_line" in opts:
        if opts["end_of_line"] not in {"crlf", "lf", "keep"}:
            raise InvalidConfError(f"Invalid 'end_of_line' value in {conf_path}")
    if "number" in opts:
        if not isinstance(opts["number"], bool):
            raise InvalidConfError(f"Invalid 'number' value in {conf_path}")
    if "exclude" in opts:  # pragma: >=3.13 cover
        if not isinstance(opts["exclude"], list):
            raise InvalidConfError(f"Invalid 'exclude' value in {conf_path}")
        for pattern in opts["exclude"]:
            if not isinstance(pattern, str):
                raise InvalidConfError(f"Invalid 'exclude' value in {conf_path}")


def _validate_keys(opts: Mapping, conf_path: Path) -> None:
    for key in opts:
        if key not in DEFAULT_OPTS:
            raise InvalidConfError(
                f"Invalid key {key!r} in {conf_path}."
                f" Keys must be one of {set(DEFAULT_OPTS)}."
            )
