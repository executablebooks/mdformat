[![Build Status](https://travis-ci.com/hukkinj1/mdformat.svg?branch=master)](<https://travis-ci.com/hukkinj1/mdformat>)
[![codecov.io](https://codecov.io/gh/hukkinj1/mdformat/branch/master/graph/badge.svg)](<https://codecov.io/gh/hukkinj1/mdformat>)
[![PyPI version](https://badge.fury.io/py/mdformat.svg)](<https://badge.fury.io/py/mdformat>)

# mdformat

> CommonMark compliant Markdown formatter

**WARNING:**
Mdformat is still in an early phase of development.
There is no stable library API, and the Markdown formatting rules may change at any time.
It is recommended to pin mdformat dependency to an exact version.

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

### Format a string

~~~python
import mdformat

markdown = "\n\n# A header\n\n"
formatted_markdown = mdformat.string(markdown)
assert formatted_markdown == "# A header\n"
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
- repo: https://github.com/hukkinj1/mdformat
  rev: 0.0.6  # Use the ref you want to point at
  hooks:
  - id: mdformat
~~~
