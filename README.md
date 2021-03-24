[![Documentation Status](https://readthedocs.org/projects/mdformat/badge/?version=latest)](https://mdformat.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://github.com/executablebooks/mdformat/workflows/Tests/badge.svg?branch=master)](https://github.com/executablebooks/mdformat/actions?query=workflow%3ATests+branch%3Amaster+event%3Apush)
[![codecov.io](https://codecov.io/gh/executablebooks/mdformat/branch/master/graph/badge.svg)](https://codecov.io/gh/executablebooks/mdformat)
[![PyPI version](https://img.shields.io/pypi/v/mdformat)](https://pypi.org/project/mdformat)

# mdformat

> CommonMark compliant Markdown formatter

Mdformat is an opinionated Markdown formatter
that can be used to enforce a consistent style in Markdown files.
Mdformat is a Unix-style command-line tool as well as a Python library.

The features/opinions of the formatter include:

- Consistent indentation and whitespace across the board
- Always use ATX style headings
- Move all link references to the bottom of the document (sorted by label)
- Reformat indented code blocks as fenced code blocks
- Use `1.` as the ordered list marker if possible, also for noninitial list items

Mdformat by default will not change word wrapping.
The rationale for this is to support [Semantic Line Breaks](https://sembr.org/).

For a comprehensive description and rationalization of the style,
read [the style guide](https://github.com/executablebooks/mdformat/TODO/UPDATE-ME.md).

**NOTE:**
The formatting style produced by mdformat may change in each version.
It is recommended to pin mdformat dependency version.

Mdformat offers an extensible plugin system for both code fence content formatting and parser extensions (like tables).

## Installing

```bash
pip install mdformat
```

## Command line usage

### Format files

Format files `README.md` and `CHANGELOG.md` in place

```bash
mdformat README.md CHANGELOG.md
```

Format `.md` files in current working directory recursively

```bash
mdformat .
```

Read Markdown from standard input until `EOF`.
Write formatted Markdown to standard output.

```bash
mdformat -
```

### Check formatting

```bash
mdformat --check README.md CHANGELOG.md
```

This will not apply any changes to the files.
If a file is not properly formatted, the exit code will be non-zero.

### Options

```console
foo@bar:~$ mdformat --help
usage: mdformat [-h] [--check] [--version] [--number]
                [--wrap {keep,no,INTEGER}]
                [paths [paths ...]]

CommonMark compliant Markdown formatter

positional arguments:
  paths                 files to format

optional arguments:
  -h, --help            show this help message and exit
  --check               do not apply changes to files
  --version             show program's version number and exit
  --number              apply consecutive numbering to ordered lists
  --wrap {keep,no,INTEGER}
                        paragraph word wrap mode (default: keep)
```

## Python API usage

TODO: add a readthedocs link

## Usage as a pre-commit hook

TODO: add a readthedocs link

## Plugins

TODO: add a readthedocs link to plugin usage
TODO: add a readthedocs link to plugin development
TODO: add a readthedocs link to existing plugins list
