import sys
from typing import Callable, Dict, Mapping

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def _load_codeformatters() -> Dict[str, Callable[[str], str]]:
    codeformatter_entrypoints = importlib_metadata.entry_points().get(
        "mdformat.codeformatter", ()
    )
    return {ep.name: ep.load() for ep in codeformatter_entrypoints}


CODEFORMATTERS: Mapping[str, Callable[[str], str]] = _load_codeformatters()
