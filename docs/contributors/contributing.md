# Contributing

Welcome to the mdformat developer docs!
We're excited you're here and want to contribute. ✨

Please discuss new features in an issue before submitting a PR
to make sure that the feature is wanted and will be merged.
Note that mdformat is an opinionated tool
that attempts to keep formatting style changing configuration to its minimum.
New configuration will only be added for a very good reason and use case.

Below are the basic development steps,
and for further information also see the
[EBP organisation guidelines](https://github.com/executablebooks/.github/blob/master/CONTRIBUTING.md).

1. Fork and clone the repository.

1. Install pre-commit hooks

   ```bash
   pre-commit install
   ```

1. After making changes and having written tests, make sure tests pass:

   ```bash
   tox
   ```

1. Test the pre-commit hook against the README.md file

   ```bash
   pre-commit try-repo . mdformat --files README.md
   ```

1. Commit, push, and make a PR.

## Developing code formatter plugins

Mdformat code formatter plugins need to define a formatter function that is of type `Callable[[str, str], str]`.
The input arguments are the code block's unformatted code and info string, in that order.
The return value should be formatted code.

This function needs to be exposed via entry point distribution metadata.
The entry point's group must be "mdformat.codeformatter",
name must be name of the coding language it formats (as it appears in Markdown code block info strings), e.g. "python",
and value has to point to the formatter function within the plugin package,
e.g. "my_package.some_module:format_python"

If using `setup.py` for packaging, the entry point configuration would have to be similar to:

```python
import setuptools

setuptools.setup(
    # other arguments here...
    entry_points={
        "mdformat.codeformatter": ["python = my_package.some_module:format_python"]
    }
)
```

If using Poetry for packaging, the entry point configuration in `pyproject.toml` would need to be like:

```toml
# other config here...
[tool.poetry.plugins."mdformat.codeformatter"]
"python" = "my_package.some_module:format_python"
```

For a real-world example plugin, see [mdformat-black](https://github.com/hukkin/mdformat-black),
which formats Python code blocks with Black.

## Developing parser extension plugins

The easiest way to get started on a plugin, is to use the <https://github.com/executablebooks/mdformat-plugin> template repository.

Mdformat parser extension plugins need to adhere to the `mdformat.plugins.ParserExtensionInterface`:

```python
from collections.abc import Mapping
from markdown_it import MarkdownIt
from mdformat.renderer.typing import Render


def update_mdit(mdit: MarkdownIt) -> None:
    """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""


# A mapping from `RenderTreeNode.type` value to a `Render` function that can
# render the given `RenderTreeNode` type. These functions override the default
# `Render` funcs defined in `mdformat.renderer.DEFAULT_RENDERERS`.
RENDERERS: Mapping[str, Render]
```

This interface needs to be exposed via entry point distribution metadata.
The entry point's group must be "mdformat.parser_extension".

If using `setup.py` for packaging, the entry point configuration would have to be similar to:

```python
import setuptools

setuptools.setup(
    # other arguments here...
    entry_points={
        "mdformat.parser_extension": ["myextension = my_package:ext_module_or_class"]
    }
)
```

If using Poetry or Flit for packaging, the entry point configuration in `pyproject.toml` would need to be like:

```toml
# other config here...
[tool.poetry.plugins."mdformat.parser_extension"]
"myextension" = "my_package:ext_module_or_class"
# or
[tool.flit.plugins."mdformat.parser_extension"]
"myextension" = "my_package:ext_module_or_class"
```
