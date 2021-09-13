from io import StringIO
import sys
from unittest import mock

from mdformat._cli import run
from mdformat._conf import read_toml_opts


def test_cli_override(tmp_path):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("wrap = 'no'")

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("remove\nthis\nwrap\n")

    assert run((str(file_path), "--wrap=keep")) == 0
    assert file_path.read_text() == "remove\nthis\nwrap\n"

    assert run((str(file_path),)) == 0
    assert file_path.read_text() == "remove this wrap\n"


def test_conf_in_parent_dir(tmp_path):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("wrap = 'no'")

    subdir_path = tmp_path / "subdir"
    subdir_path.mkdir()
    file_path = subdir_path / "test_markdown.md"
    file_path.write_text("remove\nthis\nwrap")

    assert run((str(file_path),)) == 0
    assert file_path.read_text() == "remove this wrap\n"


def test_invalid_conf_key(tmp_path, capsys):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("numberr = true")

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("1. one\n1. two\n1. three")

    assert run((str(file_path),)) == 1
    captured = capsys.readouterr()
    assert "Invalid key 'numberr'" in captured.err


def test_conf_with_stdin(tmp_path, capfd, monkeypatch):
    read_toml_opts.cache_clear()

    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("number = true")

    monkeypatch.setattr(sys, "stdin", StringIO("1. one\n1. two\n1. three"))

    with mock.patch("mdformat._cli.Path.cwd", return_value=tmp_path):
        assert run(("-",)) == 0
    captured = capfd.readouterr()
    assert captured.out == "1. one\n2. two\n3. three\n"
