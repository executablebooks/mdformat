from __future__ import annotations

__all__ = (
    "MDRenderer",
    "LOGGER",
    "RenderTreeNode",
    "DEFAULT_RENDERERS",
    "RenderContext",
    "WRAP_POINT",
)

from collections.abc import Mapping, MutableMapping, Sequence
import logging
from types import MappingProxyType
from typing import Any

from markdown_it.common.normalize_url import unescape_string
from markdown_it.token import Token

from mdformat.renderer._context import DEFAULT_RENDERERS, WRAP_POINT, RenderContext
from mdformat.renderer._tree import RenderTreeNode
from mdformat.renderer.typing import Postprocess

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
        tree: RenderTreeNode,
        options: Mapping[str, Any],
        env: MutableMapping,
        *,
        finalize: bool = True,
    ) -> str:
        self._prepare_env(env)

        # Update RENDERER_MAP defaults with renderer functions defined
        # by plugins.
        updated_renderers = {}
        postprocessors: dict[str, tuple[Postprocess, ...]] = {}
        for plugin in options.get("parser_extension", []):
            for syntax_name, renderer_func in plugin.RENDERERS.items():
                if syntax_name in updated_renderers:
                    LOGGER.warning(
                        "Plugin conflict. More than one plugin defined a renderer"
                        f' for "{syntax_name}" syntax.'
                    )
                else:
                    updated_renderers[syntax_name] = renderer_func
            for syntax_name, pp in getattr(plugin, "POSTPROCESSORS", {}).items():
                if syntax_name not in postprocessors:
                    postprocessors[syntax_name] = (pp,)
                else:
                    postprocessors[syntax_name] += (pp,)
        renderer_map = MappingProxyType({**DEFAULT_RENDERERS, **updated_renderers})
        postprocessor_map = MappingProxyType(postprocessors)

        render_context = RenderContext(renderer_map, postprocessor_map, options, env)
        text = tree.render(render_context)
        if finalize:
            if env["used_refs"]:
                text += "\n\n"
                text += self._write_references(env)
            if text:
                text += "\n"

        assert "\x00" not in text, "null bytes should be removed by now"
        return text

    @staticmethod
    def _write_references(env: MutableMapping) -> str:
        ref_list = []
        for label in sorted(env["used_refs"]):
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

    def _prepare_env(self, env: MutableMapping) -> None:
        env["indent_width"] = 0
        env["used_refs"] = set()
