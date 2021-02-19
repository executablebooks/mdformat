from typing import TYPE_CHECKING, Any, Callable, Mapping

if TYPE_CHECKING:
    from mdformat.renderer import TreeNode

RendererFunc = Callable[
    ["TreeNode", Mapping[str, Callable], Mapping[str, Any], dict], str
]
