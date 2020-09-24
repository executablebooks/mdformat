## Contributing

1. Fork and clone the repository.

1. Install dependencies.

   ```bash
   pip install poetry
   poetry install
   ```

1. Install pre-commit hooks

   ```bash
   pre-commit install
   ```

1. After making changes and having written tests, make sure tests pass:

   ```bash
   pytest
   ```

   Alternatively you can run the tests *via* `tox`,
   which will automate the poetry install into a virtual environment, before calling pytest.

1. Commit, push, and make a PR.

## Developing code formatter plugins

Mdformat code formatter plugins need to define a formatter function that is of type `Callable[[str, str], str]`.
The input arguments are the code block's unformatted code and info string, in that order.
The return value should be formatted code.

This function needs to be exposed via entry point distribution metadata.
The entry point's group must be "mdformat.codeformatter",
name must be name of the coding language it formats (as it appears in Markdown code block info strings), e.g. "python",
and value has to point to the formatter function within the plugin package,
e.g. "my\_package.some\_module:format\_python"

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

For a real-world example plugin, see [mdformat-black](<https://github.com/hukkinj1/mdformat-black>),
which formats Python code blocks with Black.
