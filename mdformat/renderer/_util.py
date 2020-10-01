import html
import re
from typing import Sequence

from markdown_it.token import Token

# Regex that finds character references.
# The reference can be either
#   1. decimal representation, e.g. &#11;
#   2. hex representation, e.g. &#x1e;
#   3. HTML5 entity reference, e.g. &nbsp;
RE_CHAR_REFERENCE = re.compile(
    "&("
    "#[0-9]{1,7}"
    "|#[Xx][0-9A-Fa-f]{1,6}"
    "|" + "|".join({c.rstrip(";") for c in html.entities.html5}) + ");"
)

# key to indicate consecutive numbering of ordered lists
CONSECUTIVE_KEY = "number"


class MARKERS:
    """A container for markers for unprocessed Markdown.

    Temporary markers that can be used for markdown that is not yet
    fully processed. "\x00" is invalid Markdown so a string that
    contains it can not naturally exist in Markdown.
    """

    LIST_ITEM = "\x00 0 list-item"
    INDENTATION = "\x00 1 indentation"
    # We add BLOCK_SEPARATOR instead of newlines at the end of every block.
    # We convert it to newlines when closing
    #   - a list item
    #   - a list
    #   - a blockquote
    #   - the root document
    BLOCK_SEPARATOR = "\x00 2 block-separator"


def index_opening_token(tokens: Sequence[Token], closing_token_idx: int) -> int:
    """Return index of an opening token.

    Takes token stream and closing token index of a container block as
    params. Returns index of the corresponding opening token.
    """
    closing_tkn = tokens[closing_token_idx]
    assert closing_tkn.nesting == -1, "Cant find opening token for non closing token"
    for i in reversed(range(closing_token_idx)):
        opening_tkn_candidate = tokens[i]
        if opening_tkn_candidate.level == closing_tkn.level:
            return i
    raise ValueError("Invalid token list. Closing token not found.")


def find_opening_token(tokens: Sequence[Token], closing_token_idx: int) -> Token:
    """Return an opening token.

    Takes token stream and closing token index of a container block as
    params. Returns the corresponding opening token.
    """
    opening_token_idx = index_opening_token(tokens, closing_token_idx)
    return tokens[opening_token_idx]


def is_tight_list(tokens: Sequence[Token], closing_token_idx: int) -> bool:
    closing_tkn = tokens[closing_token_idx]
    assert closing_tkn.type in {"bullet_list_close", "ordered_list_close"}

    # The list has list items at level +1 so paragraphs in those list
    # items must be at level +2
    paragraph_level = closing_tkn.level + 2

    for i in range(
        index_opening_token(tokens, closing_token_idx) + 1, closing_token_idx
    ):
        if tokens[i].level != paragraph_level or tokens[i].type != "paragraph_open":
            continue
        is_tight = tokens[i].hidden
        if not is_tight:
            return False
    return True


def is_tight_list_item(tokens: Sequence[Token], closing_token_idx: int) -> bool:
    list_item_closing_tkn = tokens[closing_token_idx]
    assert list_item_closing_tkn.type == "list_item_close"

    for i in range(closing_token_idx, len(tokens)):
        if tokens[i].level < list_item_closing_tkn.level:
            return is_tight_list(tokens, i)
    raise ValueError("List closing token not found")


def longest_consecutive_sequence(seq: str, char: str) -> int:
    """Return length of the longest consecutive sequence of `char` characters
    in string `seq`."""
    assert len(char) == 1
    longest = 0
    current_streak = 0
    for c in seq:
        if c == char:
            current_streak += 1
        else:
            current_streak = 0
        if current_streak > longest:
            longest = current_streak
    return longest


def is_text_inside_autolink(tokens: Sequence[Token], idx: int) -> bool:
    assert tokens[idx].type == "text"
    if idx == 0:
        return False
    previous_token = tokens[idx - 1]
    return previous_token.type == "link_open" and previous_token.markup == "autolink"


def removesuffix(string: str, suffix: str) -> str:
    if suffix and string.endswith(suffix):
        return string[: -len(suffix)]
    return string
