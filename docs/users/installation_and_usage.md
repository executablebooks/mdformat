# Installation and usage

## Installing

Install with CommonMark support:

```bash
pip install mdformat
```

Alternatively install with GitHub Flavored Markdown (GFM) support:

```bash
pip install mdformat-gfm
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

### Format text

```python
import mdformat

unformatted = "\n\n# A header\n\n"
formatted = mdformat.text(unformatted)
assert formatted == "# A header\n"
```

### Format a file

Format file `README.md` in place:

```python
import mdformat

# Input filepath as a string...
mdformat.file("README.md")

# ...or a pathlib.Path object
import pathlib

filepath = pathlib.Path("README.md")
mdformat.file(filepath)
```

### Options

All formatting style modifying options available in the CLI are also available in the Python API,
with equivalent option names:

```python
import mdformat

mdformat.file(
    "FILENAME.md",
    options={
        "number": True,  # switch on consecutive numbering of ordered lists
        "wrap": 60,  # set word wrap width to 60 characters
    }
)
```

## Usage as a pre-commit hook

`mdformat` can be used as a [pre-commit](https://github.com/pre-commit/pre-commit) hook.
Add the following to your project's `.pre-commit-config.yaml` to enable this:

```yaml
- repo: https://github.com/executablebooks/mdformat
  rev: 0.6.1  # Use the ref you want to point at
  hooks:
  - id: mdformat
    # Optionally add plugins
    additional_dependencies:
    - mdformat-gfm
    - mdformat-black
```
