[![Documentation Status](https://readthedocs.org/projects/mdformat/badge/?version=latest)](https://mdformat.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://github.com/executablebooks/mdformat/workflows/Tests/badge.svg?branch=master)](https://github.com/executablebooks/mdformat/actions?query=workflow%3ATests+branch%3Amaster+event%3Apush)
[![codecov.io](https://codecov.io/gh/executablebooks/mdformat/branch/master/graph/badge.svg)](https://codecov.io/gh/executablebooks/mdformat)
[![PyPI version](https://img.shields.io/pypi/v/mdformat)](https://pypi.org/project/mdformat)

# mdformat

> CommonMark compliant Markdown formatter

Mdformat is an opinionated Markdown formatter
that can be used to enforce a consistent style in Markdown files.
Mdformat is a Unix-style command-line tool as well as a Python library.

Find out more in the [docs](https://mdformat.readthedocs.io).

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

TODO: update the link

Read more in the [docs](https://mdformat.readthedocs.io/en/latest/users/installation_and_usage.html#python-api-usage).

## Usage as a pre-commit hook

TODO: update the link

Read more in the [docs](https://mdformat.readthedocs.io/en/latest/users/installation_and_usage.html#usage-as-a-pre-commit-hook).

## Plugins

Mdformat offers an extensible plugin system for both code fence content formatting and parser extensions (like GFM tables).
Read more in the docs:

TODO: update the links

- [Plugin usage](https://mdformat.readthedocs.io/en/latest/users/plugins.html)
- [Plugin development](https://mdformat.readthedocs.io/en/latest/developers/contributing.html)
- [List of existing plugins](https://mdformat.readthedocs.io/en/latest/users/plugins.html)
