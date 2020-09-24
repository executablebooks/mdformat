from textwrap import dedent
from typing import List, Optional

from markdown_it import MarkdownIt
from markdown_it.extensions import front_matter
from markdown_it.token import Token
import yaml

import mdformat
from mdformat.plugins import PARSEPLUGINS


class FrontMatterPlugin:
    """A class for extending the base parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> MarkdownIt:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        return mdit.use(front_matter.front_matter_plugin)

    @staticmethod
    def render_token(
        tokens: List[Token], index: int, options: dict, env: dict
    ) -> Optional[str]:
        """Convert a token to a string, or return None if no render method
        available."""
        token = tokens[index]
        if token.type == "front_matter":
            text = yaml.dump(yaml.safe_load(token.content))
            return f"---\n{text.rstrip()}\n---\n"


def test_front_matter(monkeypatch):
    """Test the front matter plugin, as a simple extension example."""
    monkeypatch.setitem(PARSEPLUGINS, "front_matter", FrontMatterPlugin)
    text = mdformat.text(
        dedent(
            """\
    ---
    a:          1
    ---
    a
    """
        ),
        plugins=["front_matter"],
    )
    assert text == dedent(
        """\
    ---
    a: 1
    ---
    a
    """
    )
