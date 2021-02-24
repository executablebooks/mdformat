from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping

if TYPE_CHECKING:
    from mdformat.renderer import SyntaxTreeNode

# There is a recursion in this type that can be added when
# https://github.com/python/mypy/issues/731 is implemented.
RendererFunc = Callable[
    [
        "SyntaxTreeNode",
        Mapping[str, Callable[..., str]],
        Mapping[str, Any],
        MutableMapping,
    ],
    str,
]
