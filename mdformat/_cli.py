import argparse
import contextlib
import logging
from pathlib import Path
import shutil
import sys
import textwrap
from typing import Any, Generator, Iterable, List, Mapping, Optional, Sequence

import mdformat
from mdformat._util import is_md_equal
import mdformat.plugins
import mdformat.renderer
from mdformat.renderer._util import CONSECUTIVE_KEY


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

    arg_parser = make_arg_parser(enabled_parserplugins.values())
    args = arg_parser.parse_args(cli_args)
    if not args.paths:
        print_paragraphs(["No files have been passed in. Doing nothing."])
        return 0

    try:
        file_paths = resolve_file_paths(args.paths)
    except InvalidPath as e:
        arg_parser.error(f'File "{e.path}" does not exist.')

    # Convert args to a mapping
    options: Mapping[str, Any] = vars(args)

    format_errors_found = False
    renderer_warning_printer = RendererWarningPrinter()
    for path in file_paths:
        if path:
            path_str = str(path)
            original_str = path.read_text(encoding="utf-8")
        else:
            path_str = "-"
            original_str = sys.stdin.read()

        with log_handler_applied(mdformat.renderer.LOGGER, renderer_warning_printer):
            formatted_str = mdformat.text(
                original_str,
                options=options,
                extensions=enabled_parserplugins,
                codeformatters=enabled_codeformatters,
            )

        if args.check:
            if formatted_str != original_str:
                format_errors_found = True
                print_error(f'File "{path_str}" is not formatted.')
        else:
            if not changes_ast and not is_md_equal(
                original_str,
                formatted_str,
                options,
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
            if path:
                path.write_text(formatted_str, encoding="utf-8")
            else:
                sys.stdout.write(formatted_str)
    if format_errors_found:
        return 1
    return 0


def make_arg_parser(
    parser_plugins: Iterable[mdformat.plugins.ParserExtensionInterface],
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CommonMark compliant Markdown formatter"
    )
    parser.add_argument("paths", nargs="*", help="files to format")
    parser.add_argument(
        "--check", action="store_true", help="do not apply changes to files"
    )
    parser.add_argument(
        "--version", action="version", version=f"mdformat {mdformat.__version__}"
    )
    parser.add_argument(
        f"--{CONSECUTIVE_KEY}",
        action="store_true",
        help="apply consecutive numbering to ordered lists",
    )
    for plugin in parser_plugins:
        if hasattr(plugin, "add_cli_options"):
            plugin.add_cli_options(parser)
    return parser


class InvalidPath(Exception):
    """Exception raised when a path does not exist."""

    def __init__(self, path: Path):
        self.path = path


def resolve_file_paths(path_strings: Iterable[str]) -> List[Optional[Path]]:
    """Resolve pathlib.Path objects from filepath strings.

    Convert path strings to pathlib.Path objects. Check that all paths
    are either files, directories or stdin. If not, raise InvalidPath.
    Resolve directory paths to a list of file paths (ending with ".md").
    """
    file_paths: List[Optional[Path]] = []  # Path to file or None for stdin/stdout
    for path_str in path_strings:
        if path_str == "-":
            file_paths.append(None)
            continue
        path_obj = Path(path_str)
        try:
            path_exists = path_obj.exists()
        except OSError:  # Catch "OSError: [WinError 123]" on Windows
            path_exists = False
        if not path_exists:
            raise InvalidPath(path_obj)
        if path_obj.is_dir():
            for p in path_obj.glob("**/*.md"):
                file_paths.append(p)
        else:
            file_paths.append(path_obj)
    return file_paths


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
    wrapper = textwrap.TextWrapper(
        break_long_words=False, break_on_hyphens=False, width=min(terminal_width, 80)
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
