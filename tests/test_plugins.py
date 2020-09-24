from textwrap import dedent
from typing import List, Optional

from markdown_it import MarkdownIt
from markdown_it.extensions import front_matter
from markdown_it.token import Token
import yaml

import mdformat
from mdformat._renderer import MDRenderer
from mdformat.plugins import EXTENDPLUGINS


class ExampleFrontMatterPlugin:
    """A class for extending the base parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> MarkdownIt:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        return mdit.use(front_matter.front_matter_plugin)

    @staticmethod
    def render_token(
        renderer: MDRenderer, tokens: List[Token], index: int, options: dict, env: dict
    ) -> Optional[str]:
        """Convert a token to a string, or return None if no render method
        available."""
        token = tokens[index]
        if token.type == "front_matter":
            text = yaml.dump(yaml.safe_load(token.content))
            return f"---\n{text.rstrip()}\n---\n", index


def test_front_matter(monkeypatch):
    """Test the front matter plugin, as a single token extension example."""
    monkeypatch.setitem(EXTENDPLUGINS, "front_matter", ExampleFrontMatterPlugin)
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


class ExampleTablePlugin:
    """A class for extending the base parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> MarkdownIt:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        return mdit.enable("table")

    @staticmethod
    def render_token(
        renderer: MDRenderer, tokens: List[Token], index: int, options: dict, env: dict
    ) -> Optional[str]:
        """Convert a token to a string, or return None if no render method
        available."""
        token = tokens[index]
        if token.type == "table_open":
            # search for the table close, and return a dummy output
            while index < len(tokens):
                index += 1
                if tokens[index].type == "table_close":
                    break
            return f"dummy {index}\n\n", index


def test_table(monkeypatch):
    """Test the table plugin, as a multi-token extension example."""
    monkeypatch.setitem(EXTENDPLUGINS, "table", ExampleTablePlugin)
    text = mdformat.text(
        dedent(
            """\
    |a|b|
    |-|-|
    |c|d|

    other text
    """
        ),
        plugins=["table"],
    )
    assert text == dedent(
        """\
    dummy 21

    other text
    """
    )
