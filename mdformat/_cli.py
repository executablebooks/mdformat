import argparse
from pathlib import Path
import sys
from typing import List, Optional, Sequence

import mdformat
from mdformat._util import is_md_equal


def run(cli_args: Sequence[str]) -> int:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="CommonMark compliant Markdown formatter"
    )
    parser.add_argument("paths", nargs="*", help="Files to format")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(cli_args)

    if not args.paths:
        sys.stderr.write("No files have been passed in. Doing nothing.\n")
        return 0

    # Convert paths given as args to pathlib.Path objects.
    # Check that all paths are either files, directories or stdin.
    # Resolve directory paths to a list of file paths (ending with ".md").
    file_paths: List[Optional[Path]] = []  # Path to file or None for stdin/stdout
    for path_str in args.paths:
        if path_str == "-":
            file_paths.append(None)
            continue
        path_obj = Path(path_str)
        if path_obj.is_dir():
            for p in path_obj.glob("**/*.md"):
                file_paths.append(p)
        elif path_obj.is_file():
            file_paths.append(path_obj)
        else:
            sys.stderr.write(f'Error: File "{path_str}" does not exist.\n')
            return 1

    format_errors_found = False
    for path in file_paths:
        if path:
            path_str = str(path)
            original_str = path.read_text(encoding="utf-8")
        else:
            path_str = "-"
            original_str = sys.stdin.read()
        formatted_str = mdformat.text(original_str)

        if args.check:
            if formatted_str != original_str:
                format_errors_found = True
                sys.stderr.write(f'Error: File "{path_str}" is not formatted.\n')
        else:
            if not is_md_equal(original_str, formatted_str):
                sys.stderr.write(
                    f'Error: Could not format "{path_str}"\n'
                    "\n"
                    "The formatted Markdown renders to different HTML than the input Markdown.\n"  # noqa: E501
                    "This is likely a bug in mdformat. Please create an issue report here:\n"  # noqa: E501
                    "https://github.com/hukkinj1/mdformat/issues\n"
                )
                return 1
            if path:
                path.write_text(formatted_str, encoding="utf-8")
            else:
                sys.stdout.write(formatted_str)
    if format_errors_found:
        return 1
    return 0
