from textwrap import dedent
from typing import List, Optional, Tuple

from markdown_it import MarkdownIt
from markdown_it.extensions import front_matter
from markdown_it.token import Token
import yaml

import mdformat
from mdformat.plugins import CODEFORMATTERS, PARSER_EXTENSIONS
from mdformat.renderer import MARKERS, MDRenderer


def example_formatter(code, info):
    return "dummy\n"


def test_code_formatter(monkeypatch):
    monkeypatch.setitem(CODEFORMATTERS, "lang", example_formatter)
    text = mdformat.text(
        dedent(
            """\
    ```lang
    a
    ```
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang
    dummy
    ```
    """
    )


class ExampleFrontMatterPlugin:
    """A class for extending the base parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        mdit.use(front_matter.front_matter_plugin)

    @staticmethod
    def render_token(
        renderer: MDRenderer, tokens: List[Token], index: int, options: dict, env: dict
    ) -> Optional[Tuple[str, int]]:
        """Convert a token to a string, or return None if no render method
        available."""
        token = tokens[index]
        if token.type == "front_matter":
            text = yaml.dump(yaml.safe_load(token.content))
            return f"---\n{text.rstrip()}\n---" + MARKERS.BLOCK_SEPARATOR, index
        return None


def test_front_matter(monkeypatch):
    """Test the front matter plugin, as a single token extension example."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "front_matter", ExampleFrontMatterPlugin)
    text = mdformat.text(
        dedent(
            """\
    ---
    a:          1
    ---
    a
    """
        ),
        extensions=["front_matter"],
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
    def update_mdit(mdit: MarkdownIt):
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        mdit.enable("table")

    @staticmethod
    def render_token(
        renderer: MDRenderer, tokens: List[Token], index: int, options: dict, env: dict
    ) -> Optional[Tuple[str, int]]:
        """Convert a token to a string, or return None if no render method
        available."""
        token = tokens[index]
        if token.type == "table_open":
            # search for the table close, and return a dummy output
            while index < len(tokens):
                index += 1
                if tokens[index].type == "table_close":
                    break
            return f"dummy {index}" + MARKERS.BLOCK_SEPARATOR, index
        return None


def test_table(monkeypatch):
    """Test the table plugin, as a multi-token extension example."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExampleTablePlugin)
    text = mdformat.text(
        dedent(
            """\
    |a|b|
    |-|-|
    |c|d|

    other text
    """
        ),
        extensions=["table"],
    )
    assert text == dedent(
        """\
    dummy 21

    other text
    """
    )
