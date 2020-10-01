import argparse
from pathlib import Path
import sys
from typing import Iterable, List, Optional, Sequence

import mdformat
from mdformat._util import is_md_equal
import mdformat.plugins
from mdformat.renderer._util import CONSECUTIVE_KEY


def run(cli_args: Sequence[str]) -> int:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="CommonMark compliant Markdown formatter"
    )
    parser.add_argument("paths", nargs="*", help="Files to format")
    parser.add_argument(
        "--check", action="store_true", help="Do not apply changes to files"
    )
    parser.add_argument(
        f"--{CONSECUTIVE_KEY}",
        action="store_true",
        help="Apply consecutive numbering to ordered lists",
    )
    changes_ast = False
    for plugin in mdformat.plugins.PARSER_EXTENSIONS.values():
        if hasattr(plugin, "add_cli_options"):
            plugin.add_cli_options(parser)
        if getattr(plugin, "CHANGES_AST", False):
            changes_ast = True

    args = parser.parse_args(cli_args)

    if not args.paths:
        sys.stderr.write("No files have been passed in. Doing nothing.\n")
        return 0

    try:
        file_paths = resolve_file_paths(args.paths)
    except InvalidPath as e:
        parser.error(f'File "{e.path}" does not exist.')

    # convert args to dict
    options = vars(args)
    # Enable all parser plugins
    enabled_parserplugins = mdformat.plugins.PARSER_EXTENSIONS.keys()
    # Enable code formatting for all languages that have a plugin installed
    enabled_codeformatter_langs = mdformat.plugins.CODEFORMATTERS.keys()

    format_errors_found = False
    for path in file_paths:
        if path:
            path_str = str(path)
            original_str = path.read_text(encoding="utf-8")
        else:
            path_str = "-"
            original_str = sys.stdin.read()
        formatted_str = mdformat.text(
            original_str,
            options=options,
            extensions=enabled_parserplugins,
            codeformatters=enabled_codeformatter_langs,
        )

        if args.check:
            if formatted_str != original_str:
                format_errors_found = True
                sys.stderr.write(f'Error: File "{path_str}" is not formatted.\n')
        else:
            if not changes_ast and not is_md_equal(
                original_str,
                formatted_str,
                options,
                extensions=enabled_parserplugins,
                codeformatters=enabled_codeformatter_langs,
            ):
                sys.stderr.write(
                    f'Error: Could not format "{path_str}"\n'
                    "\n"
                    "The formatted Markdown renders to different HTML than the input Markdown.\n"  # noqa: E501
                    "This is likely a bug in mdformat. Please create an issue report here:\n"  # noqa: E501
                    "https://github.com/executablebooks/mdformat/issues\n"
                )
                return 1
            if path:
                path.write_text(formatted_str, encoding="utf-8")
            else:
                sys.stdout.write(formatted_str)
    if format_errors_found:
        return 1
    return 0


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
