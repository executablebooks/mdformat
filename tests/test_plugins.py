import argparse
from textwrap import dedent
from typing import Any, Mapping, Optional, Sequence, Tuple
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
    """A plugin that adds front_matter extension to the parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.use(front_matter.front_matter_plugin)

    @staticmethod
    def render_token(
        renderer: MDRenderer,
        tokens: Sequence[Token],
        index: int,
        options: Mapping[str, Any],
        env: dict,
    ) -> Optional[Tuple[str, int]]:
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
    """A plugin that adds table extension to the parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.enable("table")

    @staticmethod
    def render_token(
        renderer: MDRenderer,
        tokens: Sequence[Token],
        index: int,
        options: Mapping[str, Any],
        env: dict,
    ) -> Optional[Tuple[str, int]]:
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
    """A plugin that adds CLI options."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.enable("table")

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
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


class ExampleASTChangingPlugin:
    """A plugin that makes AST breaking formatting changes."""

    CHANGES_AST = True

    TEXT_REPLACEMENT = "Content replaced completely. AST is now broken!"

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    @staticmethod
    def render_token(
        renderer: MDRenderer,
        tokens: Sequence[Token],
        index: int,
        options: Mapping[str, Any],
        env: dict,
    ) -> Optional[Tuple[str, int]]:
        token = tokens[index]
        if token.type == "text":
            return ExampleASTChangingPlugin.TEXT_REPLACEMENT, index
        return None


def test_ast_changing_plugin(monkeypatch, tmp_path):
    """Test that -o arguments are correctly added to the options dict."""
    plugin = ExampleASTChangingPlugin()
    monkeypatch.setitem(PARSER_EXTENSIONS, "ast_changer", plugin)
    file_path = tmp_path / "test_markdown.md"

    # Test that the AST changing formatting is applied successfully
    # under normal operation.
    file_path.write_text("Some markdown here\n")
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == plugin.TEXT_REPLACEMENT + "\n"

    # Set the plugin's `CHANGES_AST` flag to False and test that the
    # equality check triggers, notices the AST breaking changes and a
    # non-zero error code is returned.
    plugin.CHANGES_AST = False
    file_path.write_text("Some markdown here\n")
    assert run((str(file_path),)) == 1
    assert file_path.read_text() == "Some markdown here\n"
