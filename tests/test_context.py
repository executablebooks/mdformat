from mdformat.renderer import DEFAULT_RENDERERS
from mdformat.renderer._context import RenderContext


def render_fake_syntax(node, ctx):
    return "blaa"


def test_with_default_renderer_for():
    original_renderers = {
        "fake_syntax": render_fake_syntax,
        "fake_syntax_2": render_fake_syntax,
    }
    ctx = RenderContext(
        renderers=original_renderers, postprocessors={}, options={}, env={}
    )
    ctx_2 = ctx.with_default_renderer_for("fake_syntax", "paragraph")
    assert ctx_2.renderers == {
        "fake_syntax_2": render_fake_syntax,
        "paragraph": DEFAULT_RENDERERS["paragraph"],
    }
