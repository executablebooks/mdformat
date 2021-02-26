from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode


RendererFunc = Callable[
    [
        "RenderTreeNode",
        # There is a recursion here. This should be
        # `Mapping[str, RendererFunc],` but mypy doesn't support this until
        # https://github.com/python/mypy/issues/731 is implemented.
        Mapping[str, Callable[..., str]],
        Mapping[str, Any],
        MutableMapping,
    ],
    str,
]
