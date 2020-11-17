import logging
from typing import Any, Mapping, Optional, Sequence

from markdown_it.common.normalize_url import unescape_string
from markdown_it.token import Token

from mdformat.renderer import _container_renderers, _token_renderers
from mdformat.renderer._util import MARKERS, removesuffix

__all__ = ("MDRenderer", "MARKERS", "LOGGER")

LOGGER = logging.getLogger(__name__)


class MDRenderer:
    """Markdown renderer.

    A renderer class that outputs formatted Markdown. Compatible with
    `markdown_it.MarkdownIt`.
    """

    __output__ = "md"

    def __init__(self, parser: Any = None):
        """__init__ must have `parser` parameter for markdown-it-py
        compatibility."""

    def render(  # noqa: C901
        self,
        tokens: Sequence[Token],
        options: Mapping[str, Any],
        env: dict,
        *,
        start: int = 0,
        stop: Optional[int] = None,
        finalize: bool = True,
        _recursion_level: int = 0,
    ) -> str:
        """Takes token stream and generates Markdown.

        Args:
            tokens: A list of block tokens to render
            options: Params of parser instance
            env: Additional data from parsed input
            start: Start rendering from this index
            stop: Stop rendering before this index
            finalize: replace markers and write references
        """
        assert _recursion_level in {
            0,
            1,
        }, "There should be no more than one level of recursion in tokens"
        text_stack = [""]

        i = start - 1
        if stop is None:
            stop = len(tokens)
        while (i + 1) < stop:
            i += 1
            token = tokens[i]

            result = None

            # first check plugins
            for plugin in options.get("parser_extension", []):
                output = plugin.render_token(self, tokens, i, options, env)
                if output is not None:
                    result, i = output
                    break

            if result is not None:
                # if a plugin has handled the token,
                # we assume that it does not need to open or close a container
                text_stack[-1] = text_stack[-1] + result
                continue

            if token.type == "inline":
                # inline tokens require nested rendering
                result = self.render(
                    token.children,
                    options,
                    env,
                    finalize=finalize,
                    _recursion_level=_recursion_level + 1,
                )
            else:
                # otherwise use a built-in renderer
                tkn_renderer = getattr(
                    _token_renderers, token.type, _token_renderers.default
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
                    _container_renderers, token.type, _container_renderers.default
                )
                container_result = container_renderer(
                    container_result, tokens, i, options, env
                )
                text_stack[-1] = text_stack[-1] + container_result

        rendered_content = text_stack.pop()
        assert not text_stack, "Text stack should be empty before returning"

        if finalize and not _recursion_level:
            rendered_content = removesuffix(rendered_content, MARKERS.BLOCK_SEPARATOR)
            rendered_content = rendered_content.replace(MARKERS.BLOCK_SEPARATOR, "\n\n")

            if env.get("used_refs"):
                rendered_content += "\n\n"
                rendered_content += self._write_references(env)

            rendered_content += "\n"

        return rendered_content

    @staticmethod
    def _write_references(env: dict) -> str:
        text = ""
        for label in sorted(env.get("used_refs", [])):
            ref = env["references"][label]
            destination = ref["href"] if ref["href"] else "<>"
            destination = unescape_string(destination)
            item = f"[{label.lower()}]: {destination}"
            title = ref["title"]
            if title:
                title = unescape_string(title)
                title = title.replace('"', '\\"')
                item += f' "{title}"'
            text += item + "\n"
        return text.rstrip()
