__all__ = ("MDRenderer", "LOGGER", "RenderTreeNode", "DEFAULT_RENDERER_FUNCS")


import logging
from types import MappingProxyType
from typing import Any, Mapping, MutableMapping, Sequence

from markdown_it.common.normalize_url import unescape_string
from markdown_it.token import Token

from mdformat.renderer._default_renderers import DEFAULT_RENDERER_FUNCS
from mdformat.renderer._tree import SyntaxTreeNode
from mdformat.renderer.typing import RendererFunc

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

    def render(
        self,
        tokens: Sequence[Token],
        options: Mapping[str, Any],
        env: MutableMapping,
        *,
        finalize: bool = True,
    ) -> str:
        """Takes token stream and generates Markdown.

        Args:
            tokens: A sequence of block tokens to render
            options: Params of parser instance
            env: Additional data from parsed input
            finalize: write references and add trailing newline
        """
        tree = RenderTreeNode(tokens)
        return self.render_tree(tree, options, env, finalize=finalize)

    def render_tree(
        self,
        tree: "RenderTreeNode",
        options: Mapping[str, Any],
        env: MutableMapping,
        *,
        finalize: bool = True,
    ) -> str:
        # Update RENDERER_MAP defaults with renderer functions defined
        # by plugins.
        updated_renderers = {}
        for plugin in options.get("parser_extension", []):
            for token_name, renderer_func in plugin.RENDERER_FUNCS.items():
                if token_name in updated_renderers:
                    LOGGER.warning(
                        "Plugin conflict. More than one plugin defined a renderer"
                        f' for "{token_name}" token or token pair.'
                    )
                else:
                    updated_renderers[token_name] = renderer_func
        renderer_map = MappingProxyType({**DEFAULT_RENDERER_FUNCS, **updated_renderers})

        text = tree.render(renderer_map, options, env)
        if finalize:
            if env.get("used_refs"):
                text += "\n\n"
                text += self._write_references(env)
            text += "\n"
        return text

    @staticmethod
    def _write_references(env: MutableMapping) -> str:
        ref_list = []
        for label in sorted(env.get("used_refs", [])):
            ref = env["references"][label]
            destination = ref["href"] if ref["href"] else "<>"
            destination = unescape_string(destination)
            item = f"[{label.lower()}]: {destination}"
            title = ref["title"]
            if title:
                title = title.replace('"', '\\"')
                item += f' "{title}"'
            ref_list.append(item)
        return "\n".join(ref_list)


class RenderTreeNode(SyntaxTreeNode):
    def render(
        self,
        renderer_funcs: Mapping[str, RendererFunc],
        options: Mapping[str, Any],
        env: MutableMapping,
    ) -> str:
        renderer_func = renderer_funcs[self.type]
        return renderer_func(self, renderer_funcs, options, env)
