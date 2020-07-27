from typing import Any, List

from markdown_it.token import Token

from mdformat._renderer import container_renderers, token_renderers
from mdformat._renderer.util import MARKERS, removesuffix


class MDRenderer:
    __output__ = "md"

    def __init__(self, parser: Any = None):
        """__init__ must have `parser` parameter for markdown-it-py
        compatibility."""

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
            else:
                tkn_renderer = getattr(
                    token_renderers, token.type, token_renderers.default,
                )
                result = tkn_renderer(tokens, i, options, env)

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
                container_result = text_stack.pop() + result
                container_renderer = getattr(
                    container_renderers, token.type, container_renderers.default,
                )
                container_result = container_renderer(
                    container_result, tokens, i, options, env
                )
                text_stack[-1] = text_stack[-1] + container_result

        rendered_content = text_stack.pop()
        assert not text_stack, "Text stack should be empty before returning"

        if not _recursion_level:
            rendered_content = removesuffix(rendered_content, MARKERS.BLOCK_SEPARATOR)
            rendered_content = rendered_content.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")
            rendered_content = rendered_content + "\n"
        return rendered_content
