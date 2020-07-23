import html
import inspect
import re
from typing import Any, List, Optional

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


class RendererCmark:
    __output__ = "md"

    def __init__(self, parser: Any = None):
        self.rules = {
            k: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if not (k.startswith("render") or k.startswith("_"))
        }

    def render(
        self,
        tokens: List[Token],
        options: dict,
        env: dict,
        *,
        _recursion_level: int = 0,
    ) -> str:
        """Takes token stream and generates Markdown.

        :param tokens: list on block tokens to render
        :param options: params of parser instance
        :param env: additional data from parsed input
        """
        assert _recursion_level in {
            0,
            1,
        }, "There should be no more than one level of recursion in tokens"
        text_stack = [""]

        for i, token in enumerate(tokens):

            # Render text of the current token.
            if token.type == "inline":
                result = self.render(
                    token.children, options, env, _recursion_level=_recursion_level + 1
                )
            elif token.type in self.rules:
                result = self.rules[token.type](tokens, i, options, env)
            else:
                result = ""

            # If the token opens a new container block, create a new item for
            # it in the text stack.
            if token.nesting == 1:
                text_stack.append(result)
            # If the token doesn't change nesting, write in the immediate container
            # block's stack item.
            elif token.nesting == 0:
                text_stack[-1] = text_stack[-1] + result
            # If the token ends a container block, pop the block's stack item,
            # format all markdown of that block, and append formatted markdown
            # to the block's container's stack item.
            else:  # token.nesting == -1
                whole_block_result = text_stack.pop() + result
                container_block_renderer = getattr(
                    RendererCmark.ContainerBlockRenderers,
                    token.type,
                    RendererCmark.ContainerBlockRenderers.default,
                )
                whole_block_result = container_block_renderer(
                    whole_block_result, tokens, i, options, env
                )
                text_stack[-1] = text_stack[-1] + whole_block_result

        rendered_content = text_stack.pop()
        assert not text_stack, "Text stack should be empty before returning"

        if not _recursion_level:
            rendered_content = _removesuffix(rendered_content, MARKERS.BLOCK_SEPARATOR)
            rendered_content = rendered_content.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")
            rendered_content = rendered_content + "\n"
        return rendered_content

    def renderInlineAsText(
        self, tokens: Optional[List[Token]], options: dict, env: dict
    ) -> str:
        """Special kludge for image `alt` attributes to conform CommonMark
        spec.

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
                result += self.renderInlineAsText(token.children, options, env)
            elif token.type == "link_open":
                result += self.link_open(tokens, i, options, env)
            elif token.type == "link_close":
                result += self.link_close(tokens, i, options, env)

        return result

    ###################################################################

    def link_open(self, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
        token = tokens[idx]
        if token.markup == "autolink":
            return "<"
        return "["

    def link_close(
        self, tokens: List[Token], idx: int, options: dict, env: dict
    ) -> str:
        token = tokens[idx]
        if token.markup == "autolink":
            return ">"
        open_tkn = _find_opening_token(tokens, idx)
        attrs = dict(open_tkn.attrs)
        uri = attrs["href"]
        title = attrs.get("title")
        if title is None:
            return "](<{}>)".format(uri)
        title = title.replace('"', '\\"')
        return '](<{}> "{}")'.format(uri, title)

    def hr(self, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
        return "___" + MARKERS.BLOCK_SEPARATOR

    def image(self, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
        token = tokens[idx]

        # "alt" attr MUST be set, even if empty. Because it's mandatory and
        # should be placed on proper position for tests.
        #
        # Replace content with actual value
        token.attrs[token.attrIndex("alt")][1] = self.renderInlineAsText(
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

    def code_inline(
        self, tokens: List[Token], idx: int, options: dict, env: dict
    ) -> str:
        code = tokens[idx].content
        all_chars_are_whitespace = not code.strip()
        longest_backtick_seq = _longest_consecutive_sequence(code, "`")
        if not longest_backtick_seq or all_chars_are_whitespace:
            return f"`{code}`"
        separator = "`" * (longest_backtick_seq + 1)
        return f"{separator} {code} {separator}"

    def fence(self, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
        token = tokens[idx]
        lang = token.info.strip() if token.info else ""
        code_block = token.content

        # The code block must not include as long or longer sequence of "~"
        # chars as the fence string itself
        fence_len = max(3, _longest_consecutive_sequence(code_block, "~") + 1)
        fence_str = "~" * fence_len

        return f"{fence_str}{lang}\n{code_block}{fence_str}" + MARKERS.BLOCK_SEPARATOR

    def code_block(
        self, tokens: List[Token], idx: int, options: dict, env: dict
    ) -> str:
        return self.fence(tokens, idx, options, env)

    def html_block(self, tokens: List[Token], idx: int, *args: Any) -> str:
        return tokens[idx].content.rstrip("\n") + MARKERS.BLOCK_SEPARATOR

    def html_inline(self, tokens: List[Token], idx: int, *args: Any) -> str:
        return tokens[idx].content

    def hardbreak(
        self, tokens: List[Token], idx: int, options: dict, *args: Any
    ) -> str:
        return "\\" + "\n"

    def softbreak(
        self, tokens: List[Token], idx: int, options: dict, *args: Any
    ) -> str:
        return "\n"

    def text(self, tokens: List[Token], idx: int, *args: Any) -> str:
        """Process a text token.

        Text should always be a child of an inline token enclosed by a
          - heading
          - paragraph
          - autolink (any link?)
        """
        text = tokens[idx].content
        if _is_text_inside_autolink(tokens, idx):
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

    class ContainerBlockRenderers:
        """A namespace for functions that render the markdown of complete
        container blocks."""

        @staticmethod
        def default(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            """Default formatter for tokens that don't have one implemented."""
            return text

        @staticmethod
        def blockquote_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            text = _removesuffix(text, MARKERS.BLOCK_SEPARATOR)
            text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")
            lines = text.splitlines()
            if not lines:
                return ">" + MARKERS.BLOCK_SEPARATOR
            quoted_lines = (f"> {line}" if line else ">" for line in lines)
            quoted_str = "\n".join(quoted_lines)
            return quoted_str + MARKERS.BLOCK_SEPARATOR

        @staticmethod
        def list_item_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            """Return one list item as string.

            The string contains MARKERS.LIST_ITEMs and
            MARKERS.INDENTATIONs which have to be replaced in later
            processing.
            """
            text = _removesuffix(text, MARKERS.BLOCK_SEPARATOR)
            if _is_tight_list_item(tokens, idx):
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

        @staticmethod
        def bullet_list_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            last_item_closing_tkn = tokens[idx - 1]

            text = _removesuffix(text, MARKERS.BLOCK_SEPARATOR)
            if _is_tight_list(tokens, idx):
                text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
            else:
                text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

            bullet_marker = last_item_closing_tkn.markup + " "
            indentation = " " * len(bullet_marker)
            text = text.replace(MARKERS.LIST_ITEM, bullet_marker)
            text = text.replace(MARKERS.INDENTATION, indentation)
            return text + MARKERS.BLOCK_SEPARATOR

        @staticmethod
        def ordered_list_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            last_item_closing_tkn = tokens[idx - 1]
            number_marker = last_item_closing_tkn.markup

            text = _removesuffix(text, MARKERS.BLOCK_SEPARATOR)
            if _is_tight_list(tokens, idx):
                text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n")
            else:
                text = text.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

            # Replace first MARKERS.LIST_ITEM with the starting number of the list.
            # Replace following MARKERS.LIST_ITEMs with number one prefixed by zeros
            # to make the marker of even length with the first one.
            # E.g.
            #   5321. This is the first list item
            #   0001. Second item
            #   0001. Third item
            opening_token = _find_opening_token(tokens, idx)
            starting_number = opening_token.attrGet("start")
            if starting_number is None:
                starting_number = 1
            first_item_marker = f"{starting_number}{number_marker} "
            other_item_marker = (
                "0" * (len(str(starting_number)) - 1) + "1" + number_marker + " "
            )
            indentation = " " * len(first_item_marker)
            text = text.replace(MARKERS.LIST_ITEM, first_item_marker, 1)
            text = text.replace(MARKERS.LIST_ITEM, other_item_marker)
            text = text.replace(MARKERS.INDENTATION, indentation)

            return text + MARKERS.BLOCK_SEPARATOR

        @staticmethod
        def paragraph_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            lines = text.split("\n")

            # Make sure a paragraph line does not start with "-"
            # (otherwise it will be interpreted as list item).
            lines = [f"\\{line}" if line.startswith("-") else line for line in lines]
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

        @staticmethod
        def heading_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            opener_token = _find_opening_token(tokens, idx)
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

        @staticmethod
        def strong_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            indicator = tokens[idx].markup
            return indicator + text + indicator

        @staticmethod
        def em_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            indicator = tokens[idx].markup
            return indicator + text + indicator


def _index_opening_token(tokens: List[Token], closing_token_idx: int) -> int:
    closing_tkn = tokens[closing_token_idx]
    assert closing_tkn.nesting == -1, "Cant find opening token for non closing token"
    for i in reversed(range(closing_token_idx)):
        opening_tkn_candidate = tokens[i]
        if opening_tkn_candidate.level == closing_tkn.level:
            return i
    raise ValueError("Invalid token list. Closing token not found.")


def _find_opening_token(tokens: List[Token], closing_token_idx: int) -> Token:
    opening_token_idx = _index_opening_token(tokens, closing_token_idx)
    return tokens[opening_token_idx]


def _is_tight_list(tokens: List[Token], closing_token_idx: int) -> bool:
    closing_tkn = tokens[closing_token_idx]
    assert closing_tkn.type in {"bullet_list_close", "ordered_list_close"}

    # The list has list items at level +1 so paragraphs in those list
    # items must be at level +2
    paragraph_level = closing_tkn.level + 2

    for i in range(
        _index_opening_token(tokens, closing_token_idx) + 1, closing_token_idx
    ):
        if tokens[i].level != paragraph_level or tokens[i].type != "paragraph_open":
            continue
        is_tight = tokens[i].hidden
        if not is_tight:
            return False
    return True


def _is_tight_list_item(tokens: List[Token], closing_token_idx: int) -> bool:
    list_item_closing_tkn = tokens[closing_token_idx]
    assert list_item_closing_tkn.type == "list_item_close"

    for i in range(closing_token_idx, len(tokens)):
        if tokens[i].level < list_item_closing_tkn.level:
            return _is_tight_list(tokens, i)
    raise ValueError("List closing token not found")


def _longest_consecutive_sequence(seq: str, char: str) -> int:
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


def _is_text_inside_autolink(tokens: List[Token], idx: int) -> bool:
    assert tokens[idx].type == "text"
    if idx == 0:
        return False
    previous_token = tokens[idx - 1]
    return previous_token.type == "link_open" and previous_token.markup == "autolink"


def _is_in_block(tokens: List[Token], idx: int, block_closing_tkn_type: str) -> bool:
    """Is tokens[idx] in a block closed by block_closing_tkn_type?"""
    assert tokens[idx].type == "text"
    if tokens[idx].level == 0:
        return False
    current_lvl = tokens[idx].level
    for i in range(idx + 1, len(tokens)):
        if tokens[i].level < current_lvl:
            current_lvl = tokens[i].level
            if tokens[i].type == block_closing_tkn_type:
                return True
    return False


def _removesuffix(string: str, suffix: str) -> str:
    if suffix and string.endswith(suffix):
        return string[: -len(suffix)]
    return string
