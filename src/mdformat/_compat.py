__all__ = ("importlib_metadata", "Protocol", "nullcontext")

import sys

if sys.version_info >= (3, 10):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

if sys.version_info >= (3, 7):
    from contextlib import nullcontext
else:
    from contextlib import suppress as nullcontext
