__all__ = ("importlib_metadata", "tomllib")

import sys

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    import tomllib
else:  # pragma: <3.11 cover
    import tomli as tomllib

if sys.version_info >= (3, 10):  # pragma: >=3.10 cover
    from importlib import metadata as importlib_metadata
else:  # pragma: <3.10 cover
    import importlib_metadata
