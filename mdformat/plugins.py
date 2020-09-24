import sys
from typing import Callable, Dict, List, Mapping, Optional

from markdown_it import MarkdownIt
from markdown_it.token import Token

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def _load_codeformatters() -> Dict[str, Callable[[str, str], str]]:
    codeformatter_entrypoints = importlib_metadata.entry_points().get(
        "mdformat.codeformatter", ()
    )
    return {ep.name: ep.load() for ep in codeformatter_entrypoints}


CODEFORMATTERS: Mapping[str, Callable[[str, str], str]] = _load_codeformatters()


class ParsePluginAbstract:
    """A class for extending the base parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> MarkdownIt:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        return mdit

    @staticmethod
    def render_token(
        tokens: List[Token], index: int, options: dict, env: dict
    ) -> Optional[str]:
        """Convert a token to a string, or return None if no render method
        available."""
        return None


def _load_parseplugins() -> Mapping[str, ParsePluginAbstract]:
    parseplugins_entrypoints = importlib_metadata.entry_points().get(
        "mdformat.parseplugins", ()
    )
    return {ep.name: ep.load() for ep in parseplugins_entrypoints}


PARSEPLUGINS: Mapping[str, ParsePluginAbstract] = _load_parseplugins()
