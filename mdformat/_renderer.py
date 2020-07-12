import inspect
from typing import List, Optional, Any

from markdown_it.token import Token


# This fixes some issues with tight list newlines, but definitely
# misses some corner cases.
ENABLE_HACKY_TIGHT_LIST_FIX = True


# Marks that can be used markdown that is not yet fully processed.
# "\x00" is invalid Markdown so a string that contains it can't be
# naturally exist in Markdown.
LIST_ITEM_MARKER = "\x00list-item"
INDENTATION_MARKER = "\x00indentation"


class RendererCmark:
    __output__ = "md"

    def __init__(self, parser: Any = None):
        self.rules = {
            k: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if not (k.startswith("render") or k.startswith("_"))
        }

    def render(
        self, tokens: List[Token], options: dict, env: dict, *, _recursion_level: int = 0
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
                result = self.renderToken(tokens, i, options, env)

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
            rendered_content = rendered_content.rstrip("\n") + "\n"
        return rendered_content

    def renderInlineAsText(self, tokens: Optional[List[Token]], options: dict, env: dict) -> str:
        """Special kludge for image `alt` attributes to conform CommonMark spec.

        Don't try to use it! Spec requires to show `alt` content with stripped markup,
        instead of simple escaping.
        """
        result = ""
        if not tokens:
            return result

        for i, token in enumerate(tokens):
            if token.type == "text":
                result += token.content
            elif token.type == "image":
                result += self.renderInlineAsText(token.children, options, env)
            elif token.type in {"link_open", "link_close"}:
                result += self.renderToken(tokens, i, options, env)

        return result

    def renderToken(
        self, tokens: List[Token], idx: int, options: dict, env: dict
    ) -> str:
        token = tokens[idx]

        if token.type == "em_open":
            return token.markup
        elif token.type == "em_close":
            return token.markup
        elif token.type == "strong_open":
            return token.markup
        elif token.type == "strong_close":
            return token.markup
        elif token.type == "link_open":
            if token.markup == "autolink":
                return "<"
            return "["
        elif token.type == "link_close":
            if token.markup == "autolink":
                return ">"
            open_tkn = _find_opening_token(tokens, idx)
            attrs = dict(open_tkn.attrs)
            uri = attrs["href"]
            title = attrs.get("title")
            if title is None:
                return "](<{}>)".format(uri)
            title = _escape_link_title(title)
            return '](<{}> "{}")'.format(uri, title)
        elif token.type == "hr":
            return "___\n"
        return ""

    ###################################################################
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

    def code_inline(self, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
        code = tokens[idx].content
        if not code.strip():  # If all chars are whitespace
            return f"`{code}`"
        longest_backtick_seq = _longest_consecutive_sequence(code, "`")
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

        return f"{fence_str}{lang}\n{code_block}{fence_str}\n"

    def code_block(self, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
        return self.fence(tokens, idx, options, env)

    def html_block(self, tokens: List[Token], idx: int, *args: Any) -> str:
        return tokens[idx].content.rstrip("\n") + "\n\n"

    def html_inline(self, tokens: List[Token], idx: int, *args: Any) -> str:
        return tokens[idx].content

    def hardbreak(self, tokens: List[Token], idx: int, options: dict, *args: Any) -> str:
        return "\\" + "\n"

    def softbreak(self, tokens: List[Token], idx: int, options: dict, *args: Any) -> str:
        return "\n"

    def text(self, tokens: List[Token], idx: int, *args: Any) -> str:
        text = tokens[idx].content
        if _is_text_inside_autolink(tokens, idx):
            return text
        # This backslash replace has to be first, else we start
        # multiplying backslashes.
        text = text.replace("\\", "\\\\")

        # if text.startswith("-"):
        #     text = "\\-" + text[1:]

        text = text.replace("#", "\\#")
        text = text.replace("*", "\\*")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        text = text.replace("<", "\\<")
        text = text.replace("`", "\\`")
        text = _escape_dots_after_digit(text)
        text = text.replace("&", "\\&")

        # Solves a test for Rule 12 of Emphasis and strong emphasis.
        # Should look into only making the replace in emphasis blocks.
        text = text.replace("_", "\\_")

        # Replace line starting tabs with numeric decimal representation.
        # A normal tab character would start a code block.
        lines = text.split("\n")
        starting_tabs_replaced = (
            "&#9;" + line[1:] if line.startswith("\t") else line for line in lines
        )
        text = "\n".join(starting_tabs_replaced)

        # The parser can give us consecutive newlines which can break
        # the markdown structure. Replace two or more consecutive newlines
        # with newline character's decimal reference.
        text = "&#10;&#10;".join(text.split("\n\n"))

        # === or --- sequences can seem like a header when aligned properly. Escape them.
        text = "\\=\\=\\=".join(text.split("==="))
        text = "\\-\\-\\-".join(text.split("---"))

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
        """
        A namespace for functions that render the markdown of
        complete container blocks.
        """

        @staticmethod
        def default(text: str, tokens: List[Token], idx: int, options: dict, env: dict) -> str:
            """Default formatter for tokens that don't have one implemented."""
            return text

        @staticmethod
        def blockquote_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            without_trailing_newlines = text.rstrip("\n")
            lines = without_trailing_newlines.splitlines()
            if not lines:
                return ">" + "\n\n"
            tabbed_lines = (f"> {line}" for line in lines)
            tabbed_str = "\n".join(tabbed_lines)
            return tabbed_str + "\n\n"

        @staticmethod
        def list_item_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            """Return one list item as string.

            The string contains LIST_ITEM_MARKERs and INDENTATION_MARKERs which
            have to be replaced in later processing."""
            without_trailing_newlines = text.rstrip("\n")
            trailing_newline_count = len(text) - len(without_trailing_newlines)
            lines = without_trailing_newlines.splitlines()
            if not lines:
                return LIST_ITEM_MARKER + "\n"
            indented = []
            for i, line in enumerate(lines):
                if i == 0:
                    indented.append(LIST_ITEM_MARKER + line)
                else:
                    indented.append(INDENTATION_MARKER + line)
            tabbed_str = "\n".join(indented) + "\n" * trailing_newline_count
            return tabbed_str

        @staticmethod
        def bullet_list_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            last_item_closing_tkn = tokens[idx - 1]

            if ENABLE_HACKY_TIGHT_LIST_FIX:
                if _is_tight_list(tokens, idx):
                    text = text.replace(
                        "\n\n" + LIST_ITEM_MARKER, "\n" + LIST_ITEM_MARKER
                    )

            bullet_marker = last_item_closing_tkn.markup + " "
            indentation = " " * len(bullet_marker)
            text = text.replace(LIST_ITEM_MARKER, bullet_marker)
            text = text.replace(INDENTATION_MARKER, indentation)
            return text + "\n"

        @staticmethod
        def ordered_list_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            last_item_closing_tkn = tokens[idx - 1]
            number_marker = last_item_closing_tkn.markup

            if ENABLE_HACKY_TIGHT_LIST_FIX:
                if _is_tight_list(tokens, idx):
                    text = text.replace(
                        "\n\n" + LIST_ITEM_MARKER, "\n" + LIST_ITEM_MARKER
                    )

            # Replace first LIST_ITEM_MARKER with the starting number of the list.
            # Replace following LIST_ITEM_MARKERs with number one prefixed by zeros
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
            text = text.replace(LIST_ITEM_MARKER, first_item_marker, 1)
            text = text.replace(LIST_ITEM_MARKER, other_item_marker)
            text = text.replace(INDENTATION_MARKER, indentation)

            return text + "\n"

        @staticmethod
        def paragraph_close(
            text: str, tokens: List[Token], idx: int, options: dict, env: dict
        ) -> str:
            # Make sure a paragraph line does not start with "-"
            # (otherwise it will be interpreted as list item).
            lines = text.split("\n")
            lines = [f"\\{line}" if line.startswith("-") else line for line in lines]
            text = "\n".join(lines)

            # if ENABLE_HACKY_TIGHT_LIST_FIX:
            #     return text + "\n\n"

            # TODO: Make this logic happen in the closing token of the bullet list
            #       or ordered list (for all lines if one line is not "hidden").
            #       ENABLE_HACKY_TIGHT_LIST_FIX attempts to do exactly this, but passes
            #       less tests than using this logic here. When used together, these two hacks
            #       pass more tests than alone... There must be a cleaner way
            closing_token = tokens[idx]
            if closing_token.hidden:
                return text + "\n"

            return text + "\n\n"

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

            return prefix + newlines_removed + "\n"


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


def _longest_consecutive_sequence(seq: str, char: str) -> int:
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


def _escape_link_title(title: str) -> str:
    title = title.replace('"', '\\"')
    return title


def _is_text_inside_autolink(tokens: List[Token], idx: int) -> bool:
    assert tokens[idx].type == "text"
    if idx == 0:
        return False
    previous_token = tokens[idx - 1]
    return previous_token.type == "link_open" and previous_token.markup == "autolink"


def _escape_dots_after_digit(text: str) -> str:
    escaped_str = ""
    is_prev_digit = False
    for c in text:
        if is_prev_digit and c == ".":
            escaped_str += "\\."
        else:
            escaped_str += c
        is_prev_digit = c.isdigit()
    return escaped_str
