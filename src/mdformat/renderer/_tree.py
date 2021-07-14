from markdown_it.tree import SyntaxTreeNode

from mdformat.renderer._context import RenderContext


class RenderTreeNode(SyntaxTreeNode):
    """A syntax tree node capable of making a text rendering of itself."""

    def render(self, context: RenderContext) -> str:
        renderer = context.renderers[self.type]
        text = renderer(self, context)
        for postprocessor in context.postprocessors.get(self.type, ()):
            text = postprocessor(text, self, context)
        return text
