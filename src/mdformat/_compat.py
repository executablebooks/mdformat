__all__ = ("importlib_metadata", "Protocol", "Literal", "tomllib")

import sys

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

if sys.version_info >= (3, 10):  # pragma: no cover
    from importlib import metadata as importlib_metadata
else:  # pragma: no cover
    import importlib_metadata

if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import Literal, Protocol
else:  # pragma: no cover
    from typing_extensions import Literal, Protocol
