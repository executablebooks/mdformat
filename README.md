<div align="center">

[![Documentation Status](https://readthedocs.org/projects/mdformat/badge/?version=latest)](https://mdformat.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://github.com/executablebooks/mdformat/workflows/Tests/badge.svg?branch=master)](https://github.com/executablebooks/mdformat/actions?query=workflow%3ATests+branch%3Amaster+event%3Apush)
[![codecov.io](https://codecov.io/gh/executablebooks/mdformat/branch/master/graph/badge.svg)](https://codecov.io/gh/executablebooks/mdformat)
[![PyPI version](https://img.shields.io/pypi/v/mdformat)](https://pypi.org/project/mdformat)

# ![mdformat](https://raw.githubusercontent.com/executablebooks/mdformat/master/docs/_static/logo.svg)

> CommonMark compliant Markdown formatter

</div>

<!-- start mini-description -->

Mdformat is an opinionated Markdown formatter
that can be used to enforce a consistent style in Markdown files.
Mdformat is a Unix-style command-line tool as well as a Python library.

<!-- end mini-description -->

Find out more in the [docs](https://mdformat.readthedocs.io).

<!-- start installing -->

## Installing

Install with CommonMark support:

```bash
pip install mdformat
```

Alternatively install with GitHub Flavored Markdown (GFM) support:

```bash
pip install mdformat-gfm
```

<!-- end installing -->

<!-- start cli-usage -->

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

<!-- end cli-usage -->

## Documentation

This README merely provides a quickstart guide for the command line interface.
For more information refer to the [documentation](https://mdformat.readthedocs.io).
Here's a few pointers to get you started:

- [Style guide](https://mdformat.readthedocs.io/en/stable/users/style.html)
- [Python API usage](https://mdformat.readthedocs.io/en/stable/users/installation_and_usage.html#python-api-usage)
- [Usage as a pre-commit hook](https://mdformat.readthedocs.io/en/stable/users/installation_and_usage.html#usage-as-a-pre-commit-hook)
- [Plugin usage](https://mdformat.readthedocs.io/en/stable/users/plugins.html)
- [Plugin development guide](https://mdformat.readthedocs.io/en/stable/contributors/contributing.html)
- [List of code block formatter plugins](https://mdformat.readthedocs.io/en/stable/users/plugins.html#existing-plugins)
- [List of parser extension plugins](https://mdformat.readthedocs.io/en/stable/users/plugins.html#id1)
- [Changelog](https://mdformat.readthedocs.io/en/stable/users/changelog.html)

<!-- start faq -->

## Frequently Asked Questions

### Why not use [Prettier](https://github.com/prettier/prettier) instead?

Mdformat is pure Python code!
Python is pre-installed on macOS and virtually any Linux distribution,
meaning that typically little to no additional installations are required to run mdformat.
This argument also holds true when using together with
[pre-commit](https://github.com/pre-commit/pre-commit) (also Python).
Prettier on the other hand requires Node.js/npm.

Prettier suffers from [numerous](https://github.com/prettier/prettier/issues?q=is%3Aopen+label%3Alang%3Amarkdown+label%3Atype%3Abug+) bugs,
many of which cause changes in Markdown AST and rendered HTML.
Many of these bugs are a consequence of using [`remark-parse`](https://github.com/remarkjs/remark/tree/main/packages/remark-parse) v8.x as Markdown parser which,
according to the author themselves,
is [inferior to markdown-it](https://github.com/remarkjs/remark/issues/75#issuecomment-143532326) used by mdformat.
`remark-parse` v9.x is advertised as CommonMark compliant
and presumably would fix many of the issues,
but is not used by Prettier (v2.2.1) yet.

Prettier (v2.2.1), being able to format many languages other than Markdown,
is a large package with 63 direct dependencies
(mdformat only has 2 in Python 3.8+).
This can be a disadvantage in many environments,
one example being size optimized Docker images.

Mdformat's parser extension plugin API allows not only customization of the Markdown specification in use,
but also advanced features like [automatic table of contents generation](https://github.com/hukkinj1/mdformat-toc).
Also provided is a code formatter plugin API enabling integration of embedded code formatting for any programming language.

### What's wrong with the mdformat logo? It renders incorrectly and is just terrible in general.

Nope, the logo is actually pretty great – you're terrible.
The logo is more a piece of art than a logo anyways,
depicting the horrors of poorly formatted text documents.
I made it myself!

That said, if you have any graphic design skills and want to contribute a revised version, a PR is more than welcome 😄.

<!-- end faq -->
