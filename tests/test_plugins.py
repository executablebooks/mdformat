import argparse
from textwrap import dedent
from typing import List, Optional, Tuple
from unittest.mock import call, patch

from markdown_it import MarkdownIt
from markdown_it.extensions import front_matter
from markdown_it.token import Token
import yaml

import mdformat
from mdformat._cli import run
from mdformat.plugins import PARSER_EXTENSIONS
from mdformat.renderer import MARKERS, MDRenderer
from mdformat.renderer._util import CONSECUTIVE_KEY


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


class ExamplePluginWithCli:
    """A class for extending the base parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
        mdit.enable("table")

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
        """Add options to the mdformat CLI, to be stored in
        mdit.options["mdformat"]"""
        parser.add_argument("--o1", type=str)
        parser.add_argument("--o2", type=str, default="a")
        parser.add_argument("--o3", dest="arg_name", type=int)


def test_cli_options(monkeypatch, tmp_path):
    """Test that -o arguments are correctly added to the options dict."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithCli)
    file_path = tmp_path / "test_markdown.md"
    file_path.touch()

    with patch.object(MDRenderer, "render", return_value="") as mock_method:
        assert run((str(file_path), "--o1", "other", "--o3", "4")) == 0

    calls = mock_method.call_args_list
    assert len(calls) == 1, calls
    expected = {
        "maxNesting": 20,
        "html": True,
        "linkify": False,
        "typographer": False,
        "quotes": "“”‘’",
        "xhtmlOut": True,
        "breaks": False,
        "langPrefix": "language-",
        "highlight": None,
        "store_labels": True,
        "parser_extension": [ExamplePluginWithCli],
        "codeformatters": {},
        "mdformat": {
            "arg_name": 4,
            "check": False,
            CONSECUTIVE_KEY: False,
            "o1": "other",
            "o2": "a",
            "paths": [str(file_path)],
        },
    }
    assert calls[0] == call([], expected, {}), calls[0]
