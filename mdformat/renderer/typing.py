from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping

if TYPE_CHECKING:
    from mdformat.renderer import TreeNode

RendererFunc = Callable[
    ["TreeNode", Mapping[str, Callable[..., str]], Mapping[str, Any], MutableMapping],
    str,
]
