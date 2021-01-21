"""A namespace for functions that render the markdown of complete container
blocks."""
import re
from typing import Any, Mapping, Optional, Sequence

from markdown_it.token import Token

from mdformat.renderer._util import (
    CONSECUTIVE_KEY,
    MARKERS,
    find_opening_token,
    get_list_marker_type,
    is_tight_list,
    is_tight_list_item,
    maybe_add_link_brackets,
    removesuffix,
)


def default(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    """Default formatter for containers that don't have one implemented."""
    return text


def blockquote_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")
    lines = text.splitlines()
    if not lines:
        return ">" + MARKERS.BLOCK_SEPARATOR
    quoted_lines = (f"> {line}" if line else ">" for line in lines)
    quoted_str = "\n".join(quoted_lines)
    return quoted_str + MARKERS.BLOCK_SEPARATOR


def list_item_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    """Return one list item as string.

    The string contains MARKERS.LIST_ITEMs, MARKERS.LIST_INDENTs and
    MARKERS.LIST_INDENT_FIRST_LINEs which have to be replaced in later
    processing.
    """
    text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    if is_tight_list_item(tokens, idx):
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
    else:
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

    lines = text.splitlines()
    if not lines:
        return MARKERS.LIST_ITEM + MARKERS.BLOCK_SEPARATOR
    indented = []
    for i, line in enumerate(lines):
        if i == 0:
            indented.append(
                MARKERS.LIST_ITEM + MARKERS.LIST_INDENT_FIRST_LINE + line
                if line
                else MARKERS.LIST_ITEM
            )
        else:
            indented.append(MARKERS.LIST_INDENT + line if line else line)
    tabbed_str = "\n".join(indented) + MARKERS.BLOCK_SEPARATOR
    return tabbed_str


def bullet_list_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    if is_tight_list(tokens, idx):
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
    else:
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

    marker_type = get_list_marker_type(tokens, idx)
    first_line_indent = " "
    indent = " " * len(marker_type + first_line_indent)
    text = text.replace(MARKERS.LIST_ITEM, marker_type)
    text = text.replace(MARKERS.LIST_INDENT_FIRST_LINE, first_line_indent)
    text = text.replace(MARKERS.LIST_INDENT, indent)
    return text + MARKERS.BLOCK_SEPARATOR


def ordered_list_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    marker_type = get_list_marker_type(tokens, idx)
    first_line_indent = " "

    text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    if is_tight_list(tokens, idx):
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
    else:
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

    opening_token = find_opening_token(tokens, idx)
    # TODO: remove the type ignore when
    #       https://github.com/executablebooks/markdown-it-py/pull/102
    #       is merged and released
    starting_number: Optional[int] = opening_token.attrGet("start")  # type: ignore
    if starting_number is None:
        starting_number = 1

    if options.get("mdformat", {}).get(CONSECUTIVE_KEY):
        # Replace MARKERS.LIST_ITEM with consecutive numbering,
        # padded with zeros to make all markers of even length.
        # E.g.
        #   002. This is the first list item
        #   003. Second item
        #   ...
        #   112. Last item
        pad = len(str(text.count(MARKERS.LIST_ITEM) + starting_number - 1))
        indentation = " " * (pad + len(f"{marker_type}{first_line_indent}"))
        while MARKERS.LIST_ITEM in text:
            number = str(starting_number).rjust(pad, "0")
            text = text.replace(MARKERS.LIST_ITEM, f"{number}{marker_type}", 1)
            starting_number += 1
    else:
        # Replace first MARKERS.LIST_ITEM with the starting number of the list.
        # Replace following MARKERS.LIST_ITEMs with number one prefixed by zeros
        # to make the marker of even length with the first one.
        # E.g.
        #   5321. This is the first list item
        #   0001. Second item
        #   0001. Third item
        first_item_marker = f"{starting_number}{marker_type}"
        other_item_marker = "0" * (len(str(starting_number)) - 1) + "1" + marker_type
        indentation = " " * len(first_item_marker + first_line_indent)
        text = text.replace(MARKERS.LIST_ITEM, first_item_marker, 1)
        text = text.replace(MARKERS.LIST_ITEM, other_item_marker)

    text = text.replace(MARKERS.LIST_INDENT_FIRST_LINE, first_line_indent)
    text = text.replace(MARKERS.LIST_INDENT, indentation)

    return text + MARKERS.BLOCK_SEPARATOR


def paragraph_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    lines = text.split("\n")

    # Replace line starting tabs with numeric decimal representation.
    # A normal tab character would start a code block.
    lines = ["&#9;" + line[1:] if line.startswith("\t") else line for line in lines]
    # Make sure a paragraph line does not start with "#"
    # (otherwise it will be interpreted as an ATX heading).
    lines = [f"\\{line}" if line.startswith("#") else line for line in lines]
    # Make sure a paragraph line does not start with "*", "-" or "+"
    # followed by a space, tab, or end of line.
    # (otherwise it will be interpreted as list item).
    lines = [
        f"\\{line}" if re.match(r"[-*+]( |\t|$)", line) else line for line in lines
    ]
    # If a line starts with a number followed by "." or ")" followed by
    # a space, tab or end of line, escape the "." or ")" or it will be
    # interpreted as ordered list item.
    lines = [
        line.replace(")", "\\)", 1) if re.match(r"[0-9]+\)( |\t|$)", line) else line
        for line in lines
    ]
    lines = [
        line.replace(".", "\\.", 1) if re.match(r"[0-9]+\.( |\t|$)", line) else line
        for line in lines
    ]

    text = "\n".join(lines)

    return text + MARKERS.BLOCK_SEPARATOR


def heading_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    opener_token = find_opening_token(tokens, idx)
    if opener_token.markup == "=":
        prefix = "# "
    elif opener_token.markup == "-":
        prefix = "## "
    else:  # ATX heading
        prefix = opener_token.markup + " "

    # There can be newlines in setext headers, but we make an ATX
    # header always. Convert newlines to spaces.
    text = text.replace("\n", " ").rstrip()

    # If the text ends in a sequence of hashes (#), the hashes will be
    # interpreted as an optional closing sequence of the heading, and
    # will not be rendered. Escape a line ending hash to prevent this.
    if text.endswith("#"):
        text = text[:-1] + "\\#"

    return prefix + text + MARKERS.BLOCK_SEPARATOR


def strong_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    indicator = tokens[idx].markup
    return indicator + text + indicator


def em_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    indicator = tokens[idx].markup
    return indicator + text + indicator


def link_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    token = tokens[idx]
    if token.markup == "autolink":
        return "<" + text + ">"
    open_tkn = find_opening_token(tokens, idx)
    assert open_tkn.attrs is not None, "link_open token attrs must not be None"

    ref_label = open_tkn.meta.get("label")
    if ref_label:
        env.setdefault("used_refs", set()).add(ref_label)
        ref_label_repr = ref_label.lower()
        if text.lower() == ref_label_repr:
            return f"[{text}]"
        return f"[{text}][{ref_label_repr}]"

    attrs = dict(open_tkn.attrs)
    uri = attrs["href"]
    uri = maybe_add_link_brackets(uri)
    title = attrs.get("title")
    if title is None:
        return f"[{text}]({uri})"
    title = title.replace('"', '\\"')
    return f'[{text}]({uri} "{title}")'
