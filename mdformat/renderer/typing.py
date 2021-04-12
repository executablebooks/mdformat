from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode

# There should be `mdformat.renderer.RenderContext` instead of `Any`
# here and in `Postprocess` below but that results in recursive typing
# which mypy doesn't support until
# https://github.com/python/mypy/issues/731 is implemented.
Render = Callable[
    ["RenderTreeNode", Any],
    str,
]

Postprocess = Callable[[str, "RenderTreeNode", Any], str]
