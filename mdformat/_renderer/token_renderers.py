"""A namespace for functions that render the Markdown of tokens from markdown-
it-py."""
from typing import Any, List, Optional

from markdown_it.token import Token

from mdformat._renderer.util import (
    MARKERS,
    RE_CHAR_REFERENCE,
    find_opening_token,
    is_text_inside_autolink,
    longest_consecutive_sequence,
)


def default(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    """Default formatter for containers that don't have one implemented."""
    return ""


def link_open(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    token = tokens[idx]
    if token.markup == "autolink":
        return "<"
    return "["


def link_close(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    token = tokens[idx]
    if token.markup == "autolink":
        return ">"
    open_tkn = find_opening_token(tokens, idx)
    attrs = dict(open_tkn.attrs)
    uri = attrs["href"]
    title = attrs.get("title")
    if title is None:
        return "](<{}>)".format(uri)
    title = title.replace('"', '\\"')
    return '](<{}> "{}")'.format(uri, title)


def hr(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    return "___" + MARKERS.BLOCK_SEPARATOR


def image(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    token = tokens[idx]

    # "alt" attr MUST be set, even if empty. Because it's mandatory and
    # should be placed on proper position for tests.
    #
    # Replace content with actual value
    token.attrs[token.attrIndex("alt")][1] = _render_inline_as_text(
        token.children, options, env
    )
    label = token.attrGet("alt")
    assert label is not None

    uri = token.attrGet("src")
    assert uri is not None
    title = token.attrGet("title")
    if title is not None:
        return '![{}]({} "{}")'.format(label, uri, title)
    return "![{}]({})".format(label, uri)


def code_inline(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    code = tokens[idx].content
    all_chars_are_whitespace = not code.strip()
    longest_backtick_seq = longest_consecutive_sequence(code, "`")
    if not longest_backtick_seq or all_chars_are_whitespace:
        return f"`{code}`"
    separator = "`" * (longest_backtick_seq + 1)
    return f"{separator} {code} {separator}"


def fence(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    token = tokens[idx]
    lang = token.info.strip() if token.info else ""
    code_block = token.content

    # The code block must not include as long or longer sequence of "~"
    # chars as the fence string itself
    fence_len = max(3, longest_consecutive_sequence(code_block, "~") + 1)
    fence_str = "~" * fence_len

    return f"{fence_str}{lang}\n{code_block}{fence_str}" + MARKERS.BLOCK_SEPARATOR


def code_block(tokens: List[Token], idx: int, options: dict, env: dict) -> str:
    return fence(tokens, idx, options, env)


def html_block(tokens: List[Token], idx: int, *args: Any) -> str:
    return tokens[idx].content.rstrip("\n") + MARKERS.BLOCK_SEPARATOR


def html_inline(tokens: List[Token], idx: int, *args: Any) -> str:
    return tokens[idx].content


def hardbreak(tokens: List[Token], idx: int, options: dict, *args: Any) -> str:
    return "\\" + "\n"


def softbreak(tokens: List[Token], idx: int, options: dict, *args: Any) -> str:
    return "\n"


def text(tokens: List[Token], idx: int, *args: Any) -> str:
    """Process a text token.

    Text should always be a child of an inline token enclosed by a
      - heading
      - paragraph
      - autolink (any link?)
    """
    text = tokens[idx].content
    if is_text_inside_autolink(tokens, idx):
        return text
    # This backslash replace has to be first, else we start
    # multiplying backslashes.
    text = text.replace("\\", "\\\\")

    text = text.replace("#", "\\#")
    text = text.replace("*", "\\*")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("<", "\\<")
    text = text.replace("`", "\\`")
    # Only escape "&" if it starts a sequence that can be interpreted as
    # a character reference.
    for char_refs_found, char_ref in enumerate(RE_CHAR_REFERENCE.finditer(text)):
        start = char_ref.start() + char_refs_found
        text = text[:start] + "\\" + text[start:]

    # Solves a test for Rule 12 of Emphasis and strong emphasis.
    # TODO: Should look into only making the replace in emphasis/strong blocks.
    text = text.replace("_", "\\_")

    # Replace line starting tabs with numeric decimal representation.
    # A normal tab character would start a code block.
    lines = text.split("\n")
    starting_tabs_replaced = (
        "&#9;" + line[1:] if line.startswith("\t") else line for line in lines
    )
    text = "\n".join(starting_tabs_replaced)

    # Replace no-break space with its decimal representation
    text = text.replace(chr(160), "&#160;")

    # The parser can give us consecutive newlines which can break
    # the markdown structure. Replace two or more consecutive newlines
    # with newline character's decimal reference.
    text = text.replace("\n\n", "&#10;&#10;")

    # === or --- sequences can seem like a header when aligned
    # properly. Escape them.
    text = text.replace("===", r"\=\=\=")
    text = text.replace("---", r"\-\-\-")

    # If the last character is a "!" and the token next up is a link, we
    # have to escape the "!" or else the link will be interpreted as image.
    if (
        text.endswith("!")
        and (idx + 1) < len(tokens)
        and tokens[idx + 1].type == "link_open"
    ):
        text = text[:-1] + "\\!"

    return text


def _render_inline_as_text(
    tokens: Optional[List[Token]], options: dict, env: dict
) -> str:
    """Special kludge for image `alt` attributes to conform CommonMark spec.

    Don't try to use it! Spec requires to show `alt` content with
    stripped markup, instead of simple escaping.
    """
    result = ""
    if not tokens:
        return result

    for i, token in enumerate(tokens):
        if token.type == "text":
            result += token.content
        elif token.type == "image":
            result += _render_inline_as_text(token.children, options, env)
        elif token.type == "link_open":
            result += link_open(tokens, i, options, env)
        elif token.type == "link_close":
            result += link_close(tokens, i, options, env)

    return result
