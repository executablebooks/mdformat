from __future__ import annotations

import argparse
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
import contextlib
import itertools
import logging
from pathlib import Path
import re
import shutil
import sys
import textwrap

import mdformat
from mdformat._compat import importlib_metadata
from mdformat._conf import DEFAULT_OPTS, InvalidConfError, read_toml_opts
from mdformat._util import atomic_write, is_md_equal
import mdformat.plugins
import mdformat.renderer

# Match "\r" and "\n" characters that are not part of a "\r\n" sequence
RE_NON_CRLF_LINE_END = re.compile(r"(?:(?:[^\r]|^)\n|\r(?:[^\n]|$))")


class RendererWarningPrinter(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            sys.stderr.write(f"Warning: {record.msg}\n")


def run(cli_args: Sequence[str]) -> int:  # noqa: C901
    # Enable all parser plugins
    enabled_parserplugins = mdformat.plugins.PARSER_EXTENSIONS
    # Enable code formatting for all languages that have a plugin installed
    enabled_codeformatters = mdformat.plugins.CODEFORMATTERS

    changes_ast = any(
        getattr(plugin, "CHANGES_AST", False)
        for plugin in enabled_parserplugins.values()
    )

    arg_parser = make_arg_parser(enabled_parserplugins, enabled_codeformatters)
    cli_opts = {
        k: v for k, v in vars(arg_parser.parse_args(cli_args)).items() if v is not None
    }
    if not cli_opts["paths"]:
        print_paragraphs(["No files have been passed in. Doing nothing."])
        return 0

    try:
        file_paths = resolve_file_paths(cli_opts["paths"])
    except InvalidPath as e:
        arg_parser.error(f'File "{e.path}" does not exist.')

    format_errors_found = False
    renderer_warning_printer = RendererWarningPrinter()
    for path in file_paths:
        try:
            toml_opts = read_toml_opts(path.parent if path else Path.cwd())
        except InvalidConfError as e:
            print_error(str(e))
            return 1
        opts = {**DEFAULT_OPTS, **toml_opts, **cli_opts}

        if path:
            path_str = str(path)
            # Unlike `path.read_text(encoding="utf-8")`, this preserves
            # line ending type.
            original_str = path.read_bytes().decode()
        else:
            path_str = "-"
            original_str = sys.stdin.read()

        formatted_str = mdformat.text(
            original_str,
            options=opts,
            extensions=enabled_parserplugins,
            codeformatters=enabled_codeformatters,
            _first_pass_contextmanager=log_handler_applied(
                mdformat.renderer.LOGGER, renderer_warning_printer
            ),
        )

        if opts["check"]:
            if (
                (formatted_str != original_str)
                or (opts["end_of_line"] == "lf" and "\r" in original_str)
                or (
                    opts["end_of_line"] == "crlf"
                    and RE_NON_CRLF_LINE_END.search(original_str)
                )
            ):
                format_errors_found = True
                print_error(f'File "{path_str}" is not formatted.')
        else:
            if not changes_ast and not is_md_equal(
                original_str,
                formatted_str,
                options=opts,
                extensions=enabled_parserplugins,
                codeformatters=enabled_codeformatters,
            ):
                print_error(
                    f'Could not format "{path_str}".',
                    paragraphs=[
                        "The formatted Markdown renders to different HTML than the input Markdown. "  # noqa: E501
                        "This is likely a bug in mdformat. "
                        "Please create an issue report here, including the input Markdown: "  # noqa: E501
                        "https://github.com/executablebooks/mdformat/issues",
                    ],
                )
                return 1
            newline = "\r\n" if opts["end_of_line"] == "crlf" else "\n"
            if path:
                atomic_write(path, formatted_str, newline)
            else:
                with open(
                    sys.stdout.fileno(), "w", closefd=False, newline=newline
                ) as stdout:
                    stdout.write(formatted_str)
    if format_errors_found:
        return 1
    return 0


def validate_wrap_arg(value: str) -> str | int:
    if value in {"keep", "no"}:
        return value
    width = int(value)
    if width < 1:
        raise ValueError("wrap width must be a positive integer")
    return width


def make_arg_parser(
    parser_extensions: Mapping[str, mdformat.plugins.ParserExtensionInterface],
    codeformatters: Mapping[str, Callable[[str, str], str]],
) -> argparse.ArgumentParser:
    plugin_versions_str = get_plugin_versions_str(parser_extensions, codeformatters)
    parser = argparse.ArgumentParser(
        description="CommonMark compliant Markdown formatter",
        epilog=f"Installed plugins: {plugin_versions_str}"
        if plugin_versions_str
        else None,
    )
    parser.add_argument("paths", nargs="*", help="files to format")
    parser.add_argument(
        "--check", action="store_true", help="do not apply changes to files"
    )
    version_str = f"mdformat {mdformat.__version__}"
    if plugin_versions_str:
        version_str += f" ({plugin_versions_str})"
    parser.add_argument("--version", action="version", version=version_str)
    parser.add_argument(
        "--number",
        action="store_const",
        const=True,
        help="apply consecutive numbering to ordered lists",
    )
    parser.add_argument(
        "--wrap",
        type=validate_wrap_arg,
        metavar="{keep,no,INTEGER}",
        help="paragraph word wrap mode (default: keep)",
    )
    parser.add_argument(
        "--end-of-line",
        choices=("lf", "crlf"),
        help="output file line ending mode (default: lf)",
    )
    for plugin in parser_extensions.values():
        if hasattr(plugin, "add_cli_options"):
            plugin.add_cli_options(parser)
    return parser


class InvalidPath(Exception):
    """Exception raised when a path does not exist."""

    def __init__(self, path: Path):
        self.path = path


def resolve_file_paths(path_strings: Iterable[str]) -> list[None | Path]:
    """Resolve pathlib.Path objects from filepath strings.

    Convert path strings to pathlib.Path objects. Resolve symlinks.
    Check that all paths are either files, directories or stdin. If not,
    raise InvalidPath. Resolve directory paths to a list of file paths
    (ending with ".md").
    """
    file_paths: list[None | Path] = []  # Path to file or None for stdin/stdout
    for path_str in path_strings:
        if path_str == "-":
            file_paths.append(None)
            continue
        path_obj = Path(path_str)
        path_obj = _resolve_path(path_obj)
        if path_obj.is_dir():
            for p in path_obj.glob("**/*.md"):
                p = _resolve_path(p)
                file_paths.append(p)
        else:
            file_paths.append(path_obj)
    return file_paths


def _resolve_path(path: Path) -> Path:
    """Resolve path.

    Resolve symlinks. Raise `InvalidPath` if the path does not exist.
    """
    try:
        path = path.resolve()  # resolve symlinks
        path_exists = path.exists()
    except OSError:  # Catch "OSError: [WinError 123]" on Windows
        path_exists = False
    if not path_exists:
        raise InvalidPath(path)
    return path


def print_paragraphs(paragraphs: Iterable[str]) -> None:
    assert not isinstance(paragraphs, str)
    sys.stderr.write(wrap_paragraphs(paragraphs))


def print_error(title: str, paragraphs: Iterable[str] = ()) -> None:
    assert not isinstance(paragraphs, str)
    assert not title.lower().startswith("error")
    title = "Error: " + title
    paragraphs = [title] + list(paragraphs)
    print_paragraphs(paragraphs)


def wrap_paragraphs(paragraphs: Iterable[str]) -> str:
    """Wrap and concatenate paragraphs.

    Take an iterable of paragraphs as input. Return a string where the
    paragraphs are concatenated (empty line as separator) and wrapped.
    End the string in a newline.
    """
    terminal_width, _ = shutil.get_terminal_size()
    if 0 < terminal_width < 80:
        wrap_width = terminal_width
    else:
        wrap_width = 80
    wrapper = textwrap.TextWrapper(
        break_long_words=False, break_on_hyphens=False, width=wrap_width
    )
    return "\n\n".join(wrapper.fill(p) for p in paragraphs) + "\n"


@contextlib.contextmanager
def log_handler_applied(
    logger: logging.Logger, handler: logging.Handler
) -> Generator[None, None, None]:
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)


def get_plugin_versions(
    parser_extensions: Mapping[str, mdformat.plugins.ParserExtensionInterface],
    codeformatters: Mapping[str, Callable[[str, str], str]],
) -> dict[str, str]:
    versions = {}
    for iface in itertools.chain(parser_extensions.values(), codeformatters.values()):
        # Packages and modules should have `__package__`
        if hasattr(iface, "__package__"):
            package_name = iface.__package__  # type: ignore[attr-defined]
        else:  # class or function
            module_name = iface.__module__
            package_name = module_name.split(".", maxsplit=1)[0]
        try:
            package_version = importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            # In test scenarios the package may not exist
            package_version = "unknown"
        versions[package_name] = package_version
    return versions


def get_plugin_versions_str(
    parser_extensions: Mapping[str, mdformat.plugins.ParserExtensionInterface],
    codeformatters: Mapping[str, Callable[[str, str], str]],
) -> str:
    plugin_versions = get_plugin_versions(parser_extensions, codeformatters)
    return ", ".join(f"{name}: {version}" for name, version in plugin_versions.items())
