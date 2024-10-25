import argparse
import json
from textwrap import dedent
from unittest.mock import patch

from markdown_it import MarkdownIt
import pytest

import mdformat
from mdformat._cli import run
from mdformat.plugins import CODEFORMATTERS, PARSER_EXTENSIONS
from mdformat.renderer import MDRenderer, RenderContext, RenderTreeNode


def test_code_formatter(monkeypatch):
    def fmt_func(code, info):
        return "dummy\n"

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
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


def test_code_formatter__empty_str(monkeypatch):
    def fmt_func(code, info):
        return ""

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ~~~lang
    aag
    gw
    ~~~
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang
    ```
    """
    )


def test_code_formatter__no_end_newline(monkeypatch):
    def fmt_func(code, info):
        return "dummy\ndum"

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ```lang
    ```
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang
    dummy
    dum
    ```
    """
    )


def test_code_formatter__interface(monkeypatch):
    def fmt_func(code, info):
        return info + code * 2

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ```    lang  long
    multi
    mul
    ```
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang  long
    lang  longmulti
    mul
    multi
    mul
    ```
    """
    )


class TextEditorPlugin:
    """A plugin that makes all text the same."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_renderer(  # type: ignore[misc]
        tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return "All text is like this now!"

    RENDERERS = {"text": _text_renderer}


def test_single_token_extension(monkeypatch):
    """Test the front matter plugin, as a single token extension example."""
    plugin_name = "text_editor"
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name, TextEditorPlugin)
    text = mdformat.text(
        dedent(
            """\
    # Example Heading

    Example paragraph.
    """
        ),
        extensions=[plugin_name],
    )
    assert text == dedent(
        """\
    # All text is like this now!

    All text is like this now!
    """
    )


class ExampleTablePlugin:
    """A plugin that adds table extension to the parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.enable("table")

    def _table_renderer(  # type: ignore[misc]
        tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return "dummy 21"

    RENDERERS = {"table": _table_renderer}


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
        extensions=["table", "table"],
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
    """Test that CLI arguments added by plugins are correctly added to the
    options dict."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithCli)
    file_path = tmp_path / "test_markdown.md"
    file_path.touch()

    with patch.object(MDRenderer, "render", return_value="") as mock_render:
        assert run((str(file_path), "--o1", "other", "--o3", "4")) == 0

    (call_,) = mock_render.call_args_list
    posargs = call_[0]
    # Options is the second positional arg of MDRender.render
    opts = posargs[1]
    assert opts["mdformat"]["o1"] == "other"
    assert opts["mdformat"]["o2"] == "a"
    assert opts["mdformat"]["arg_name"] == 4


class ExamplePluginWithGroupedCli:
    """A plugin that adds CLI options."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.enable("table")

    @staticmethod
    def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
        group.add_argument("--o1", type=str)
        group.add_argument("--o2", type=str, default="a")
        group.add_argument("--o3", dest="arg_name", type=int)
        group.add_argument("--override-toml")


def test_cli_options_group(monkeypatch, tmp_path):
    """Test that CLI arguments added by plugins are correctly added to the
    options dict.

    Use add_cli_argument_group plugin API.
    """
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithGroupedCli)
    file_path = tmp_path / "test_markdown.md"
    conf_path = tmp_path / ".mdformat.toml"
    file_path.touch()
    conf_path.write_text(
        """\
[plugin.table]
override_toml = 'failed'
toml_only = true
"""
    )

    with patch.object(MDRenderer, "render", return_value="") as mock_render:
        assert (
            run(
                (
                    str(file_path),
                    "--o1",
                    "other",
                    "--o3",
                    "4",
                    "--override-toml",
                    "success",
                )
            )
            == 0
        )

    (call_,) = mock_render.call_args_list
    posargs = call_[0]
    # Options is the second positional arg of MDRender.render
    opts = posargs[1]
    assert opts["mdformat"]["plugin"]["table"]["o1"] == "other"
    assert opts["mdformat"]["plugin"]["table"]["o2"] == "a"
    assert opts["mdformat"]["plugin"]["table"]["arg_name"] == 4
    assert opts["mdformat"]["plugin"]["table"]["override_toml"] == "success"
    assert opts["mdformat"]["plugin"]["table"]["toml_only"] is True


def test_cli_options_group__no_toml(monkeypatch, tmp_path):
    """Test add_cli_argument_group plugin API with configuration only from
    CLI."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithGroupedCli)
    file_path = tmp_path / "test_markdown.md"
    file_path.touch()

    with patch.object(MDRenderer, "render", return_value="") as mock_render:
        assert run((str(file_path), "--o1", "other")) == 0

    (call_,) = mock_render.call_args_list
    posargs = call_[0]
    # Options is the second positional arg of MDRender.render
    opts = posargs[1]
    assert opts["mdformat"]["plugin"]["table"]["o1"] == "other"


class ExampleASTChangingPlugin:
    """A plugin that makes AST breaking formatting changes."""

    CHANGES_AST = True

    TEXT_REPLACEMENT = "Content replaced completely. AST is now broken!"

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_renderer(  # type: ignore[misc]
        tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return ExampleASTChangingPlugin.TEXT_REPLACEMENT

    RENDERERS = {"text": _text_renderer}


def test_ast_changing_plugin(monkeypatch, tmp_path):
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


class JSONFormatterPlugin:
    """A code formatter plugin that formats JSON."""

    @staticmethod
    def format_json(unformatted: str, _info_str: str) -> str:
        parsed = json.loads(unformatted)
        return json.dumps(parsed, indent=2) + "\n"


def test_code_format_warnings__cli(monkeypatch, tmp_path, capsys):
    monkeypatch.setitem(CODEFORMATTERS, "json", JSONFormatterPlugin.format_json)
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("```json\nthis is invalid json\n```\n")
    assert run([str(file_path)]) == 0
    captured = capsys.readouterr()
    assert (
        captured.err
        == f"Warning: Failed formatting content of a json code block (line 1 before formatting). Filename: {file_path}\n"  # noqa: E501
    )


def test_code_format_warnings__api(monkeypatch, caplog):
    monkeypatch.setitem(CODEFORMATTERS, "json", JSONFormatterPlugin.format_json)
    assert (
        mdformat.text("```json\nthis is invalid json\n```\n", codeformatters=("json",))
        == "```json\nthis is invalid json\n```\n"
    )
    assert (
        caplog.messages[0]
        == "Failed formatting content of a json code block (line 1 before formatting)"
    )


def test_plugin_conflict(monkeypatch, tmp_path, capsys):
    """Test a warning when plugins try to render same syntax."""
    plugin_name_1 = "plug1"
    plugin_name_2 = "plug2"
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name_1, TextEditorPlugin)
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name_2, ExampleASTChangingPlugin)

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("some markdown here")
    assert run([str(file_path)]) == 0
    captured = capsys.readouterr()
    assert (
        captured.err
        == 'Warning: Plugin conflict. More than one plugin defined a renderer for "text" syntax.\n'  # noqa: E501
    )


def test_plugin_versions_in_cli_help(monkeypatch, capsys):
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExampleTablePlugin)
    with pytest.raises(SystemExit) as exc_info:
        run(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Installed plugins:" in captured.out
    assert "tests: unknown" in captured.out


class PrefixPostprocessPlugin:
    """A plugin that postprocesses text, adding a prefix."""

    CHANGES_AST = True

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_postprocess(  # type: ignore[misc]
        text: str, tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return "Prefixed!" + text

    RENDERERS: dict = {}
    POSTPROCESSORS = {"text": _text_postprocess}


class SuffixPostprocessPlugin:
    """A plugin that postprocesses text, adding a suffix."""

    CHANGES_AST = True

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_postprocess(  # type: ignore[misc]
        text: str, tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return text + "Suffixed!"

    RENDERERS: dict = {}
    POSTPROCESSORS = {"text": _text_postprocess}


def test_postprocess_plugins(monkeypatch):
    """Test that postprocessors work collaboratively."""
    suffix_plugin_name = "suffixer"
    prefix_plugin_name = "prefixer"
    monkeypatch.setitem(PARSER_EXTENSIONS, suffix_plugin_name, SuffixPostprocessPlugin)
    monkeypatch.setitem(PARSER_EXTENSIONS, prefix_plugin_name, PrefixPostprocessPlugin)
    text = mdformat.text(
        dedent(
            """\
            # Example Heading.

            Example paragraph.
            """
        ),
        extensions=[suffix_plugin_name, prefix_plugin_name],
    )
    assert text == dedent(
        """\
        # Prefixed!Example Heading.Suffixed!

        Prefixed!Example paragraph.Suffixed!
        """
    )
