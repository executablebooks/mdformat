import argparse
from pathlib import Path
import sys

from markdown_it import MarkdownIt

from mdformat._renderer import RendererCmark


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="CommonMark compliant Markdown formatter"
    )
    parser.add_argument("paths", type=Path, nargs="+", help="Files to format")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    for path in args.paths:
        if not path.is_file():
            print(f'Error: File "{path}" does not exist.')
            sys.exit(1)

    for path in args.paths:
        original_str = path.read_text()
        formatted_str = MarkdownIt(renderer_cls=RendererCmark).render(original_str)

        if args.check:
            if formatted_str != original_str:
                print(f'Error: File "{path}" is not formatted.')
                sys.exit(1)
        else:
            with path.open(mode="w") as f:
                f.write(formatted_str)


if __name__ == "__main__":
    run_cli()
