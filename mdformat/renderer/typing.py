from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


Renderer = Callable[
    ["RenderTreeNode", "RenderContext"],
    str,
]

Postprocessor = Callable[[str, "RenderTreeNode", "RenderContext"], str]
