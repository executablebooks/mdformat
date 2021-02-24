__all__ = ("MDRenderer", "LOGGER", "TreeNode", "DEFAULT_RENDERER_FUNCS")


import logging
from types import MappingProxyType
from typing import Any, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from markdown_it.common.normalize_url import unescape_string
from markdown_it.token import Token

from mdformat.renderer._default_renderers import DEFAULT_RENDERER_FUNCS
from mdformat.renderer._util import removesuffix
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
        tree = TreeNode.from_tokens(tokens)
        return self.render_tree(tree, options, env, finalize=finalize)

    def render_tree(
        self,
        tree: "TreeNode",
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


class TreeNode:
    def __init__(self) -> None:
        # Root and containers don't have self.token
        self.token: Any = None  # Optional[Token]

        # Only containers have self.opening and self.closing
        self.opening: Any = None  # Optional[Token]
        self.closing: Any = None  # Optional[Token]

        # Root does not have self.parent
        self.parent: Any = None  # Optional["TreeNode"]

        # Empty list unless a non-empty container, inline or image
        self.children: List["TreeNode"] = []

    @staticmethod
    def from_tokens(tokens: Sequence[Token]) -> "TreeNode":
        root = TreeNode()
        root._set_children_from_tokens(tokens)
        return root

    @property
    def siblings(self) -> Sequence["TreeNode"]:
        return self.parent.children

    @property
    def type_(self) -> str:
        if self.token is None and self.opening is None:
            return "root"
        if self.token:
            return self.token.type
        assert self.opening is not None
        return removesuffix(self.opening.type, "_open")

    def render(
        self,
        renderer_funcs: Mapping[str, RendererFunc],
        options: Mapping[str, Any],
        env: MutableMapping,
    ) -> str:
        renderer_func = renderer_funcs[self.type_]
        return renderer_func(self, renderer_funcs, options, env)

    def next_sibling(self) -> Optional["TreeNode"]:
        if not self.parent:
            return None
        self_index = self.siblings.index(self)
        if self_index + 1 < len(self.siblings):
            return self.siblings[self_index + 1]
        return None

    def previous_sibling(self) -> Optional["TreeNode"]:
        if not self.parent:
            return None
        self_index = self.siblings.index(self)
        if self_index - 1 >= 0:
            return self.siblings[self_index - 1]
        return None

    def _add_child(
        self,
        *,
        token: Optional[Token] = None,
        token_pair: Optional[Tuple[Token, Token]] = None,
    ) -> "TreeNode":
        child = TreeNode()
        if token:
            child.token = token
        else:
            assert token_pair is not None
            child.opening = token_pair[0]
            child.closing = token_pair[1]
        child.parent = self
        self.children.append(child)
        return child

    def _set_children_from_tokens(self, tokens: Sequence[Token]) -> None:
        """Convert the token stream to a tree structure."""
        reversed_tokens = list(reversed(tokens))
        while reversed_tokens:
            token = reversed_tokens.pop()

            if token.nesting == 0:
                child = self._add_child(token=token)
                if token.children:
                    child._set_children_from_tokens(token.children)
                continue

            assert token.nesting == 1

            nested_tokens = [token]
            nesting = 1
            while reversed_tokens and nesting != 0:
                token = reversed_tokens.pop()
                nested_tokens.append(token)
                nesting += token.nesting
            if nesting != 0:
                raise ValueError(f"unclosed tokens starting {nested_tokens[0]}")

            child = self._add_child(token_pair=(nested_tokens[0], nested_tokens[-1]))
            child._set_children_from_tokens(nested_tokens[1:-1])
