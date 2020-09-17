[![Build Status](https://github.com/executablebooks/mdformat/workflows/Tests/badge.svg?branch=master)](<https://github.com/executablebooks/mdformat/actions?query=workflow%3ATests+branch%3Amaster+event%3Apush>)
[![codecov.io](https://codecov.io/gh/executablebooks/mdformat/branch/master/graph/badge.svg)](<https://codecov.io/gh/executablebooks/mdformat>)
[![PyPI version](https://badge.fury.io/py/mdformat.svg)](<https://badge.fury.io/py/mdformat>)

# mdformat

> CommonMark compliant Markdown formatter

Mdformat is an opinionated Markdown formatter that can be used to enforce a consistent style in Markdown files.
Mdformat is a Unix-style command-line tool as well as a Python library.

The features/opinions of the formatter include:

- Strip trailing and leading whitespace
- Always use ATX style headings
- Consistent indentation for contents of block quotes and list items
- Reformat reference links as inline links
- Reformat indented code blocks as fenced code blocks
- Separate blocks with a single empty line
  (an exception being tight lists where the separator is a single newline character)
- End the file in a single newline character
- Use `1.` as the ordered list marker if possible, also for noninitial list items

Mdformat by default will not change word wrapping.
The rationale for this is to support techniques like
[One Sentence Per Line](<https://asciidoctor.org/docs/asciidoc-recommended-practices/#one-sentence-per-line>)
and
[Semantic Line Breaks](<https://sembr.org/>).

**NOTE:**
The formatting style produced by mdformat may change in each version.
It is recommended to pin mdformat dependency version.

## Installing

~~~bash
pip install mdformat
~~~

## Command line usage

### Format files

Format files `README.md` and `CHANGELOG.md` in place

~~~bash
mdformat README.md CHANGELOG.md
~~~

Format `.md` files in current working directory recursively

~~~bash
mdformat .
~~~

Read Markdown from standard input until `EOF`.
Write formatted Markdown to standard output.

~~~bash
mdformat -
~~~

### Check formatting

~~~bash
mdformat --check README.md CHANGELOG.md
~~~

This will not apply any changes to the files.
If a file is not properly formatted, the exit code will be non-zero.

## Python API usage

### Format text

~~~python
import mdformat

unformatted = "\n\n# A header\n\n"
formatted = mdformat.text(unformatted)
assert formatted == "# A header\n"
~~~

### Format a file

Format file `README.md` in place:

~~~python
import mdformat

# Input filepath as a string...
mdformat.file("README.md")

# ...or a pathlib.Path object
import pathlib

filepath = pathlib.Path("README.md")
mdformat.file(filepath)
~~~

## Usage as a pre-commit hook

`mdformat` can be used as a [pre-commit](<https://github.com/pre-commit/pre-commit>) hook.
Add the following to your project's `.pre-commit-config.yaml` to enable this:

~~~yaml
- repo: https://github.com/executablebooks/mdformat
  rev: 0.1.2  # Use the ref you want to point at
  hooks:
  - id: mdformat
~~~

## Code formatter plugins

Mdformat features a plugin system to support formatting of Markdown code blocks where the coding language has been labeled.
For instance, if [`mdformat-black`](<https://github.com/hukkinj1/mdformat-black>) plugin is installed in the environment,
mdformat CLI will automatically format Python code blocks with [Black](<https://github.com/psf/black>).

For stability, mdformat Python API behavior will not change simply due to a plugin being installed.
Code formatters will have to be explicitly enabled in addition to being installed:

~~~~python
import mdformat

unformatted = "~~~python\n'''black converts quotes'''\n~~~\n"
# Pass in `codeformatters` here! It is an iterable of coding languages
# that should be formatted
formatted = mdformat.text(unformatted, codeformatters={"python"})
assert formatted == '~~~python\n"""black converts quotes"""\n~~~\n'
~~~~

Read the [contribution guide](<https://github.com/executablebooks/mdformat/blob/master/CONTRIBUTING.md#developing-code-formatter-plugins>)
if you wish to implement a new code formatter plugin.
