__all__ = ("importlib_metadata", "Protocol", "Literal")

import sys

if sys.version_info >= (3, 10):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata

if sys.version_info >= (3, 8):
    from typing import Literal, Protocol
else:
    from typing_extensions import Literal, Protocol
