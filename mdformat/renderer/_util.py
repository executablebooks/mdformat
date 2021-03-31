import html.entities
import re
from typing import TYPE_CHECKING

from mdformat import codepoints

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode

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


def is_tight_list(node: "RenderTreeNode") -> bool:
    assert node.type in {"bullet_list", "ordered_list"}

    # The list has list items at level +1 so paragraphs in those list
    # items must be at level +2 (grand children)
    for child in node.children:
        for grand_child in child.children:
            if grand_child.type != "paragraph":
                continue
            is_tight = grand_child.hidden
            if not is_tight:
                return False
    return True


def is_tight_list_item(node: "RenderTreeNode") -> bool:
    assert node.type == "list_item"
    assert node.parent is not None
    return is_tight_list(node.parent)


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


def is_text_inside_autolink(node: "RenderTreeNode") -> bool:
    assert node.type == "text"
    return (
        node.parent  # type: ignore
        and node.parent.type == "link"
        and node.parent.info == "auto"
    )


def maybe_add_link_brackets(link: str) -> str:
    """Surround URI with brackets if required by spec."""
    if not link or (
        codepoints.ASCII_CTRL | codepoints.ASCII_WHITESPACE | {"(", ")"}
    ).intersection(link):
        return "<" + link + ">"
    return link


def get_list_marker_type(node: "RenderTreeNode") -> str:
    if node.type == "bullet_list":
        mode = "bullet"
        primary_marker = "-"
        secondary_marker = "*"
    else:
        mode = "ordered"
        primary_marker = "."
        secondary_marker = ")"
    consecutive_lists_count = 1
    current = node
    while True:
        previous_sibling = current.previous_sibling
        if previous_sibling is None:
            return primary_marker if consecutive_lists_count % 2 else secondary_marker
        prev_type = previous_sibling.type
        if (mode == "bullet" and prev_type == "bullet_list") or (
            mode == "ordered" and prev_type == "ordered_list"
        ):
            consecutive_lists_count += 1
            current = previous_sibling
        else:
            return primary_marker if consecutive_lists_count % 2 else secondary_marker


def escape_asterisk_emphasis(text: str) -> str:
    """Escape asterisks to prevent unexpected emphasis/strong emphasis.

    Currently we escape all asterisks unless both previous and next
    character are Unicode whitespace.
    """
    # Fast exit to improve performance
    if "*" not in text:
        return text

    escaped_text = ""

    text_length = len(text)
    for i, current_char in enumerate(text):
        if current_char != "*":
            escaped_text += current_char
            continue
        prev_char = text[i - 1] if (i - 1) >= 0 else None
        next_char = text[i + 1] if (i + 1) < text_length else None
        if (
            prev_char in codepoints.UNICODE_WHITESPACE
            and next_char in codepoints.UNICODE_WHITESPACE
        ):
            escaped_text += current_char
            continue
        escaped_text += "\\" + current_char

    return escaped_text


def escape_underscore_emphasis(text: str) -> str:
    """Escape underscores to prevent unexpected emphasis/strong emphasis.
    Currently we escape all underscores unless:

    - Neither of the surrounding characters are one of Unicode whitespace,
      start or end of line, or Unicode punctuation
    - Both surrounding characters are Unicode whitespace
    """
    # Fast exit to improve performance
    if "_" not in text:
        return text

    bad_neighbor_chars = (
        codepoints.UNICODE_WHITESPACE
        | codepoints.UNICODE_PUNCTUATION
        | frozenset({None})
    )
    escaped_text = ""

    text_length = len(text)
    for i, current_char in enumerate(text):
        if current_char != "_":
            escaped_text += current_char
            continue
        prev_char = text[i - 1] if (i - 1) >= 0 else None
        next_char = text[i + 1] if (i + 1) < text_length else None
        if (
            prev_char in codepoints.UNICODE_WHITESPACE
            and next_char in codepoints.UNICODE_WHITESPACE
        ) or (
            prev_char not in bad_neighbor_chars and next_char not in bad_neighbor_chars
        ):
            escaped_text += current_char
            continue
        escaped_text += "\\" + current_char

    return escaped_text


def decimalify_leading_whitespace(text: str) -> str:
    """Replace leading whitespace with decimal representations."""
    start_whitespace = ""
    start_whitespace_count = 0
    for ws_char in text:
        if ws_char in codepoints.UNICODE_WHITESPACE:
            start_whitespace += f"&#{ord(ws_char)};"
            start_whitespace_count += 1
        else:
            break
    return start_whitespace + text[start_whitespace_count:]


def decimalify_trailing_whitespace(text: str) -> str:
    """Replace trailing whitespace with decimal representations."""
    end_whitespace = ""
    end_whitespace_count = 0
    for ws_char in reversed(text):
        if ws_char in codepoints.UNICODE_WHITESPACE:
            end_whitespace = f"&#{ord(ws_char)};" + end_whitespace
            end_whitespace_count += 1
        else:
            break
    if end_whitespace:
        return text[:-end_whitespace_count] + end_whitespace
    return text
