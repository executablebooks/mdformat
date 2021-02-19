from collections import defaultdict
import logging
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping, Optional

from mdformat.renderer._typing import RendererFunc
from mdformat.renderer._util import (
    CONSECUTIVE_KEY,
    RE_CHAR_REFERENCE,
    escape_asterisk_emphasis,
    escape_underscore_emphasis,
    get_list_marker_type,
    is_text_inside_autolink,
    is_tight_list,
    is_tight_list_item,
    longest_consecutive_sequence,
    maybe_add_link_brackets,
)

if TYPE_CHECKING:
    from mdformat.renderer import TreeNode

LOGGER = logging.getLogger(__name__)


def make_render_children(separator: str) -> RendererFunc:
    def render_children(
        node: "TreeNode",
        renderer_funcs: Mapping[str, RendererFunc],
        options: Mapping[str, Any],
        env: dict,
    ) -> str:
        return separator.join(
            child.render(renderer_funcs, options, env) for child in node.children
        )

    return render_children


def hr(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    thematic_break_width = 70
    return "_" * thematic_break_width


def code_inline(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    code = node.token.content
    all_chars_are_whitespace = not code.strip()
    longest_backtick_seq = longest_consecutive_sequence(code, "`")
    if longest_backtick_seq:
        separator = "`" * (longest_backtick_seq + 1)
        return f"{separator} {code} {separator}"
    if code.startswith(" ") and code.endswith(" ") and not all_chars_are_whitespace:
        return f"` {code} `"
    return f"`{code}`"


def html_block(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    return node.token.content.rstrip("\n")


def html_inline(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    return node.token.content


def hardbreak(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    return "\\" + "\n"


def softbreak(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    return "\n"


def text(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    """Process a text token.

    Text should always be a child of an inline token. An inline token
    should always be enclosed by a heading or a paragraph.
    """
    text = node.token.content
    if is_text_inside_autolink(node):
        return text

    # Escape backslash to prevent it from making unintended escapes.
    # This escape has to be first, else we start multiplying backslashes.
    text = text.replace("\\", "\\\\")

    text = escape_asterisk_emphasis(text)  # Escape emphasis/strong marker.
    text = escape_underscore_emphasis(text)  # Escape emphasis/strong marker.
    text = text.replace("[", "\\[")  # Escape link label enclosure
    text = text.replace("]", "\\]")  # Escape link label enclosure
    text = text.replace("<", "\\<")  # Escape URI enclosure
    text = text.replace("`", "\\`")  # Escape code span marker

    # Escape "&" if it starts a sequence that can be interpreted as
    # a character reference.
    for char_refs_found, char_ref in enumerate(RE_CHAR_REFERENCE.finditer(text)):
        start = char_ref.start() + char_refs_found
        text = text[:start] + "\\" + text[start:]

    # Replace no-break space with its decimal representation
    text = text.replace(chr(160), "&#160;")

    # The parser can give us consecutive newlines which can break
    # the markdown structure. Replace two or more consecutive newlines
    # with newline character's decimal reference.
    text = text.replace("\n\n", "&#10;&#10;")

    # If the last character is a "!" and the token next up is a link, we
    # have to escape the "!" or else the link will be interpreted as image.
    next_sibling = node.next_sibling()
    if text.endswith("!") and next_sibling and next_sibling.type_ == "link":
        text = text[:-1] + "\\!"

    return text


def fence(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    token = node.token
    assert token.map is not None, "fence token map must not be None"

    info_str = token.info.strip() if token.info else ""
    lang = info_str.split()[0] if info_str.split() else ""
    code_block = token.content

    # Info strings of backtick code fences can not contain backticks or tildes.
    # If that is the case, we make a tilde code fence instead.
    if "`" in info_str or "~" in info_str:
        fence_char = "~"
    else:
        fence_char = "`"

    # Format the code block using enabled codeformatter funcs
    if lang in options.get("codeformatters", {}):
        fmt_func = options["codeformatters"][lang]
        try:
            code_block = fmt_func(code_block, info_str)
        except Exception:
            # Swallow exceptions so that formatter errors (e.g. due to
            # invalid code) do not crash mdformat.
            LOGGER.warning(
                f"Failed formatting content of a {lang} code block "
                f"(line {token.map[0] + 1} before formatting)"
            )

    # The code block must not include as long or longer sequence of `fence_char`s
    # as the fence string itself
    fence_len = max(3, longest_consecutive_sequence(code_block, fence_char) + 1)
    fence_str = fence_char * fence_len

    return f"{fence_str}{info_str}\n{code_block}{fence_str}"


def code_block(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    return fence(node, renderer_funcs, options, env)


def image(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    token = node.token
    assert token.attrs is not None, "image token attrs must not be None"

    description = _render_inline_as_text(node, renderer_funcs, options, env)

    ref_label = token.meta.get("label")
    if ref_label:
        env.setdefault("used_refs", set()).add(ref_label)
        ref_label_repr = ref_label.lower()
        if description.lower() == ref_label_repr:
            return f"![{description}]"
        return f"![{description}][{ref_label_repr}]"

    uri = token.attrGet("src")
    assert uri is not None
    uri = maybe_add_link_brackets(uri)
    title = token.attrGet("title")
    if title is not None:
        return f'![{description}]({uri} "{title}")'
    return f"![{description}]({uri})"


def _render_inline_as_text(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    """Special kludge for image `alt` attributes to conform CommonMark spec.

    Don't try to use it! Spec requires to show `alt` content with
    stripped markup, instead of simple escaping.
    """

    def text_renderer(
        node: "TreeNode",
        renderer_funcs: Mapping[str, RendererFunc],
        options: Mapping[str, Any],
        env: dict,
    ) -> str:
        return node.token.content

    def image_renderer(
        node: "TreeNode",
        renderer_funcs: Mapping[str, RendererFunc],
        options: Mapping[str, Any],
        env: dict,
    ) -> str:
        return _render_inline_as_text(node, renderer_funcs, options, env)

    inline_renderer_funcs: Mapping[str, RendererFunc] = defaultdict(
        lambda: make_render_children(""),
        {
            "text": text_renderer,
            "image": image_renderer,
            "link": link,
        },
    )
    return make_render_children("")(node, inline_renderer_funcs, options, env)


def link(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    text = ""
    for child in node.children:
        text += child.render(renderer_funcs, options, env)
    token = node.closing
    if token.markup == "autolink":
        return "<" + text + ">"
    open_tkn = node.opening
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


def em(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    text = make_render_children(separator="")(node, renderer_funcs, options, env)
    indicator = node.closing.markup
    return indicator + text + indicator


def strong(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    text = make_render_children(separator="")(node, renderer_funcs, options, env)
    indicator = node.closing.markup
    return indicator + text + indicator


def heading(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    text = make_render_children(separator="")(node, renderer_funcs, options, env)

    opener_token = node.opening
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

    return prefix + text


def blockquote(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    text = make_render_children(separator="\n\n")(node, renderer_funcs, options, env)
    # text = removesuffix(text, MARKERS.BLOCK_SEPARATOR)
    # text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")
    lines = text.splitlines()
    if not lines:
        return ">"
    quoted_lines = (f"> {line}" if line else ">" for line in lines)
    quoted_str = "\n".join(quoted_lines)
    return quoted_str


def paragraph(  # noqa: C901
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    inline_node = node.children[0]
    text = inline_node.render(renderer_funcs, options, env)
    lines = text.split("\n")

    for i in range(len(lines)):
        # Replace line starting tabs with numeric decimal representation.
        # A normal tab character would start a code block.
        if lines[i].startswith("\t"):
            lines[i] = "&#9;" + lines[i][1:]

        # Make sure a paragraph line does not start with "#"
        # (otherwise it will be interpreted as an ATX heading).
        if lines[i].startswith("#"):
            lines[i] = f"\\{lines[i]}"

        # Make sure a paragraph line does not start with "*", "-" or "+"
        # followed by a space, tab, or end of line.
        # (otherwise it will be interpreted as list item).
        if re.match(r"[-*+]( |\t|$)", lines[i]):
            lines[i] = f"\\{lines[i]}"

        # If a line starts with a number followed by "." or ")" followed by
        # a space, tab or end of line, escape the "." or ")" or it will be
        # interpreted as ordered list item.
        if re.match(r"[0-9]+\)( |\t|$)", lines[i]):
            lines[i] = lines[i].replace(")", "\\)", 1)
        if re.match(r"[0-9]+\.( |\t|$)", lines[i]):
            lines[i] = lines[i].replace(".", "\\.", 1)

        # Consecutive "-", "*" or "_" sequences can be interpreted as thematic
        # break. Escape them.
        space_removed = lines[i].replace(" ", "").replace("\t", "")
        if len(space_removed) >= 3:
            if all(c == "*" for c in space_removed):
                lines[i] = lines[i].replace("*", "\\*", 1)
            elif all(c == "-" for c in space_removed):
                lines[i] = lines[i].replace("-", "\\-", 1)
            elif all(c == "_" for c in space_removed):
                lines[i] = lines[i].replace("_", "\\_", 1)

        # A stripped line where all characters are "=" or "-" will be
        # interpreted as a setext heading. Escape.
        stripped = lines[i].strip(" \t")
        if all(c == "-" for c in stripped):
            lines[i] = lines[i].replace("-", "\\-", 1)
        elif all(c == "=" for c in stripped):
            lines[i] = lines[i].replace("=", "\\=", 1)

    text = "\n".join(lines)

    return text


def list_item(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    """Return one list item as string.

    The string contains MARKERS.LIST_ITEMs, MARKERS.LIST_INDENTs and
    MARKERS.LIST_INDENT_FIRST_LINEs which have to be replaced in later
    processing.
    """
    is_tight = is_tight_list_item(node)
    block_separator = "\n" if is_tight else "\n\n"
    text = make_render_children(block_separator)(node, renderer_funcs, options, env)

    if not text.strip():
        return ""
    return text


def bullet_list(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    marker_type = get_list_marker_type(node)
    first_line_indent = " "
    indent = " " * len(marker_type + first_line_indent)
    block_separator = "\n" if is_tight_list(node) else "\n\n"
    text = ""
    for child_idx, child in enumerate(node.children):
        list_item = child.render(renderer_funcs, options, env)
        lines = list_item.split("\n")
        formatted_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                formatted_lines.append(
                    f"{marker_type}{first_line_indent}{line}" if line else marker_type
                )
            else:
                formatted_lines.append(f"{indent}{line}" if line else "")

        text += "\n".join(formatted_lines)
        if child_idx != len(node.children) - 1:
            text += block_separator
    return text


def ordered_list(
    node: "TreeNode",
    renderer_funcs: Mapping[str, RendererFunc],
    options: Mapping[str, Any],
    env: dict,
) -> str:
    # text = render_children(node, renderer_funcs, options, env)
    marker_type = get_list_marker_type(node)
    first_line_indent = " "
    block_separator = "\n" if is_tight_list(node) else "\n\n"
    list_len = len(node.children)

    starting_number: Optional[int] = node.opening.attrGet("start")
    if starting_number is None:
        starting_number = 1

    text = ""
    for list_item_index, list_item in enumerate(node.children):
        list_item_text = list_item.render(renderer_funcs, options, env)
        lines = list_item_text.split("\n")
        formatted_lines = []
        conseucutive_numbering = options.get("mdformat", {}).get(CONSECUTIVE_KEY)
        for line_index, line in enumerate(lines):
            if line_index == 0:
                if conseucutive_numbering:
                    # Replace MARKERS.LIST_ITEM with consecutive numbering,
                    # padded with zeros to make all markers of even length.
                    # E.g.
                    #   002. This is the first list item
                    #   003. Second item
                    #   ...
                    #   112. Last item
                    number = starting_number + list_item_index
                    pad = len(str(list_len + starting_number - 1))
                    indentation = " " * (pad + len(f"{marker_type}{first_line_indent}"))
                    number_str = str(number).rjust(pad, "0")
                    formatted_lines.append(
                        f"{number_str}{marker_type}{first_line_indent}{line}"
                        if line
                        else f"{number_str}{marker_type}"
                    )
                else:
                    # Replace first MARKERS.LIST_ITEM with the starting number of the
                    # list. Replace following MARKERS.LIST_ITEMs with number one
                    # prefixed by zeros to make the marker of even length with the
                    # first one.
                    # E.g.
                    #   5321. This is the first list item
                    #   0001. Second item
                    #   0001. Third item
                    first_item_marker = f"{starting_number}{marker_type}"
                    other_item_marker = (
                        "0" * (len(str(starting_number)) - 1) + "1" + marker_type
                    )
                    indentation = " " * len(first_item_marker + first_line_indent)
                    if list_item_index == 0:
                        formatted_lines.append(
                            f"{first_item_marker}{first_line_indent}{line}"
                            if line
                            else first_item_marker
                        )
                    else:
                        formatted_lines.append(
                            f"{other_item_marker}{first_line_indent}{line}"
                            if line
                            else other_item_marker
                        )
            else:
                formatted_lines.append(f"{indentation}{line}" if line else "")

        text += "\n".join(formatted_lines)
        if list_item_index != len(node.children) - 1:
            text += block_separator
    return text


RENDERER_MAP: Mapping[str, RendererFunc] = MappingProxyType(
    {
        "inline": make_render_children(""),
        "root": make_render_children("\n\n"),
        "hr": hr,
        "code_inline": code_inline,
        "html_block": html_block,
        "html_inline": html_inline,
        "hardbreak": hardbreak,
        "softbreak": softbreak,
        "text": text,
        "fence": fence,
        "code_block": code_block,
        "link": link,
        "image": image,
        "em": em,
        "strong": strong,
        "heading": heading,
        "blockquote": blockquote,
        "paragraph": paragraph,
        "bullet_list": bullet_list,
        "ordered_list": ordered_list,
        "list_item": list_item,
    }
)
