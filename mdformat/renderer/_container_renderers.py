"""A namespace for functions that render the markdown of complete container
blocks."""
import re
from typing import Any, Mapping, Sequence

from markdown_it.token import Token

from mdformat.renderer._util import (
    CONSECUTIVE_KEY,
    MARKERS,
    find_opening_token,
    is_tight_list,
    is_tight_list_item,
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

    The string contains MARKERS.LIST_ITEMs and MARKERS.INDENTATIONs
    which have to be replaced in later processing.
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
            indented.append(MARKERS.LIST_ITEM + line)
        else:
            indented.append(MARKERS.INDENTATION + line if line else line)
    tabbed_str = "\n".join(indented) + MARKERS.BLOCK_SEPARATOR
    return tabbed_str


def bullet_list_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    last_item_closing_tkn = tokens[idx - 1]

    text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    if is_tight_list(tokens, idx):
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
    else:
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

    bullet_marker = last_item_closing_tkn.markup + " "
    indentation = " " * len(bullet_marker)
    text = text.replace(MARKERS.LIST_ITEM, bullet_marker)
    text = text.replace(MARKERS.INDENTATION, indentation)
    return text + MARKERS.BLOCK_SEPARATOR


def ordered_list_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    last_item_closing_tkn = tokens[idx - 1]
    number_marker = last_item_closing_tkn.markup

    text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    if is_tight_list(tokens, idx):
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
    else:
        text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

    opening_token = find_opening_token(tokens, idx)
    starting_number = opening_token.attrGet("start")
    if starting_number is None:
        starting_number = 1

    if options.get("mdformat", {}).get(CONSECUTIVE_KEY, False):
        # Replace MARKERS.LIST_ITEM with consecutive numbering,
        # padded with zeros to make all markers of even length.
        # E.g.
        #   002. This is the first list item
        #   003. Second item
        #   ...
        #   112. Last item
        pad = len(str(text.count(MARKERS.LIST_ITEM) + starting_number - 1))
        indentation = " " * (pad + len(f"{number_marker} "))
        while MARKERS.LIST_ITEM in text:
            number = str(starting_number).rjust(pad, "0")
            text = text.replace(MARKERS.LIST_ITEM, f"{number}{number_marker} ", 1)
            starting_number += 1
    else:
        # Replace first MARKERS.LIST_ITEM with the starting number of the list.
        # Replace following MARKERS.LIST_ITEMs with number one prefixed by zeros
        # to make the marker of even length with the first one.
        # E.g.
        #   5321. This is the first list item
        #   0001. Second item
        #   0001. Third item
        first_item_marker = f"{starting_number}{number_marker} "
        other_item_marker = (
            "0" * (len(str(starting_number)) - 1) + "1" + number_marker + " "
        )
        indentation = " " * len(first_item_marker)
        text = text.replace(MARKERS.LIST_ITEM, first_item_marker, 1)
        text = text.replace(MARKERS.LIST_ITEM, other_item_marker)

    text = text.replace(MARKERS.INDENTATION, indentation)

    return text + MARKERS.BLOCK_SEPARATOR


def paragraph_close(
    text: str, tokens: Sequence[Token], idx: int, options: Mapping[str, Any], env: dict
) -> str:
    lines = text.split("\n")

    # Make sure a paragraph line does not start with "-" or "+"
    # (otherwise it will be interpreted as list item).
    lines = [
        f"\\{line}" if (line.startswith("-") or line.startswith("+")) else line
        for line in lines
    ]
    # If a line starts with a number followed by "." or ")", escape the "." or
    # ")" or it will be interpreted as ordered list item.
    lines = [
        line.replace(")", "\\)", 1) if re.match(r"[0-9]+\)", line) else line
        for line in lines
    ]
    lines = [
        line.replace(".", "\\.", 1) if re.match(r"[0-9]+\.", line) else line
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
    newlines_removed = text.replace("\n", " ").rstrip()

    return prefix + newlines_removed + MARKERS.BLOCK_SEPARATOR


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
