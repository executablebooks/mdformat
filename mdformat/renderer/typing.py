from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode

# There should be `mdformat.renderer.RenderContext` instead of `Any`
# here but that results in recursive typing which mypy doesn't support
# until https://github.com/python/mypy/issues/731 is implemented.
Renderer = Callable[
    ["RenderTreeNode", Any],
    str,
]

# There should be `mdformat.renderer.RenderContext` instead of `Any`
# here but that results in recursive typing which mypy doesn't support
# until https://github.com/python/mypy/issues/731 is implemented.
Postprocessor = Callable[[str, "RenderTreeNode", Any], str]
