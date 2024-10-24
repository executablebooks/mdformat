from __future__ import annotations

import argparse
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
import contextlib
import inspect
import itertools
import logging
import os.path
from pathlib import Path
import shutil
import sys
import textwrap

import mdformat
from mdformat._compat import importlib_metadata
from mdformat._conf import DEFAULT_OPTS, InvalidConfError, read_toml_opts
from mdformat._util import detect_newline_type, is_md_equal
import mdformat.plugins
import mdformat.renderer


class RendererWarningPrinter(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:  # pragma: no branch
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
            toml_opts, toml_path = read_toml_opts(path.parent if path else Path.cwd())
        except InvalidConfError as e:
            print_error(str(e))
            return 1
        opts: Mapping = {**DEFAULT_OPTS, **toml_opts, **cli_opts}

        if sys.version_info >= (3, 13):  # pragma: >=3.13 cover
            if is_excluded(path, opts["exclude"], toml_path, "exclude" in cli_opts):
                continue
        else:  # pragma: <3.13 cover
            if "exclude" in toml_opts:
                print_error(
                    "'exclude' patterns are only available on Python 3.13+.",
                    paragraphs=[
                        "Please remove the 'exclude' list from your .mdformat.toml"
                        " or upgrade Python version."
                    ],
                )
                return 1

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
            _filename=path_str,
        )
        newline = detect_newline_type(original_str, opts["end_of_line"])
        formatted_str = formatted_str.replace("\n", newline)

        if opts["check"]:
            if formatted_str != original_str:
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
                        "Formatted Markdown renders to different HTML than input Markdown. "  # noqa: E501
                        "This is a bug in mdformat or one of its installed plugins. "
                        "Please retry without any plugins installed. "
                        "If this error persists, "
                        "report an issue including the input Markdown "
                        "on https://github.com/executablebooks/mdformat/issues. "
                        "If not, "
                        "report an issue on the malfunctioning plugin's issue tracker.",
                    ],
                )
                return 1
            if path:
                if formatted_str != original_str:
                    path.write_bytes(formatted_str.encode())
            else:
                sys.stdout.buffer.write(formatted_str.encode())
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
        epilog=(
            f"Installed plugins: {plugin_versions_str}" if plugin_versions_str else None
        ),
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
        choices=("lf", "crlf", "keep"),
        help="output file line ending mode (default: lf)",
    )
    if sys.version_info >= (3, 13):  # pragma: >=3.13 cover
        parser.add_argument(
            "--exclude",
            action="append",
            metavar="PATTERN",
            help="exclude files that match the Unix-style glob pattern "
            "(multiple allowed)",
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

    Convert path strings to pathlib.Path objects. Check that all paths
    are either files, directories or stdin. If not, raise InvalidPath.
    Resolve directory paths to a list of file paths (ending with ".md").
    """
    file_paths: list[None | Path] = []  # Path to file or None for stdin/stdout
    for path_str in path_strings:
        if path_str == "-":
            file_paths.append(None)
            continue
        path_obj = Path(path_str)
        path_obj = _normalize_path(path_obj)
        if path_obj.is_dir():
            for p in path_obj.glob("**/*.md"):
                if p.is_file():
                    p = _normalize_path(p)
                    file_paths.append(p)
        elif path_obj.is_file():  # pragma: nt no cover
            file_paths.append(path_obj)
        else:  # pragma: nt no cover
            raise InvalidPath(path_obj)
    return file_paths


def is_excluded(  # pragma: >=3.13 cover
    path: Path | None,
    patterns: list[str],
    toml_path: Path | None,
    excludes_from_cli: bool,
) -> bool:
    if not path:
        return False

    if not excludes_from_cli and toml_path:
        exclude_root = toml_path.parent
    else:
        exclude_root = Path.cwd()

    try:
        relative_path = path.relative_to(exclude_root)
    except ValueError:
        return False

    return any(
        relative_path.full_match(pattern)  # type: ignore[attr-defined]
        for pattern in patterns
    )


def _normalize_path(path: Path) -> Path:
    """Normalize path.

    Make the path absolute, resolve any ".." sequences. Do not resolve
    symlinks, as it would interfere with 'exclude' patterns. Raise
    `InvalidPath` if the path does not exist.
    """
    path = Path(os.path.abspath(path))
    try:
        path_exists = path.exists()
    except OSError:  # Catch "OSError: [WinError 123]" on Windows  # pragma: no cover
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


def get_package_name(obj: object) -> str | None:
    """Return top level module name, or None if not found."""
    module = inspect.getmodule(obj)
    return module.__name__.split(".", maxsplit=1)[0] if module else None


def get_plugin_versions(
    parser_extensions: Mapping[str, mdformat.plugins.ParserExtensionInterface],
    codeformatters: Mapping[str, Callable[[str, str], str]],
) -> list[tuple[str, str]]:
    """Return a list of (plugin_distro, plugin_version) tuples.

    If many plugins come from the same distribution package, only return
    the version of that distribution once. If we have no reliable way to
    one-to-one map a plugin to a distribution package, use the top level
    module name and set version to "unknown". If we don't even know the
    top level module name, return the tuple ("unknown", "unknown").
    """
    problematic_versions = []
    # Use a dict for successful version lookups so that if more than one plugin
    # originates from the same distribution, it only shows up once in a version
    # string.
    success_versions = {}
    import_package_to_distro = importlib_metadata.packages_distributions()
    for iface in itertools.chain(parser_extensions.values(), codeformatters.values()):
        import_package = get_package_name(iface)
        if import_package is None:
            problematic_versions.append(("unknown", "unknown"))
            continue
        distro_list = import_package_to_distro.get(import_package)
        if (
            not distro_list  # No distribution package found
            or len(distro_list) > 1  # Don't make any guesses with namespace packages
        ):
            problematic_versions.append((import_package, "unknown"))
            continue
        distro_name = distro_list[0]
        success_versions[distro_name] = importlib_metadata.version(distro_name)
    return [(k, v) for k, v in success_versions.items()] + problematic_versions


def get_plugin_versions_str(
    parser_extensions: Mapping[str, mdformat.plugins.ParserExtensionInterface],
    codeformatters: Mapping[str, Callable[[str, str], str]],
) -> str:
    plugin_versions = get_plugin_versions(parser_extensions, codeformatters)
    return ", ".join(f"{name}: {version}" for name, version in plugin_versions)
